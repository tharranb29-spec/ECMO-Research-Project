#!/usr/bin/env python3

"""Run the predeclared Random Forest model-class sensitivity analysis."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

from track3_a2a.run_model_evaluation_v12 import build_feature_sets


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "random_forest_sensitivity.v1.2.json"
OUTPUT = ROOT / "outputs" / "v1.2" / "random_forest_sensitivity"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interval(values):
    return {
        "estimate": float(np.median(values)),
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
    }


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    source = ROOT / config["input"]
    with source.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["partition"] == config["partition"]]
    base_config = json.loads((ROOT / "config" / "model_evaluation.v1.2.json").read_text())
    all_features, _ = build_feature_sets(rows, base_config)
    features = {name: all_features[name] for name in config["models"]}
    y = np.asarray([int(row["binary_label"]) for row in rows])
    groups = np.asarray([row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in rows])
    sums = {name: np.zeros(len(rows)) for name in features}
    counts = {name: np.zeros(len(rows), dtype=int) for name in features}
    fold_count = 0
    for repeat in range(config["validation"]["repeats"]):
        splitter = StratifiedGroupKFold(
            n_splits=config["validation"]["folds"], shuffle=True,
            random_state=config["validation"]["random_seed"] + repeat,
        )
        for fold, (train, test) in enumerate(splitter.split(features["AB"], y, groups)):
            fold_count += 1
            for name, matrix in features.items():
                settings = config["estimator"]
                model = RandomForestClassifier(
                    n_estimators=settings["n_estimators"],
                    max_features=settings["max_features"],
                    min_samples_leaf=settings["min_samples_leaf"],
                    class_weight=settings["class_weight"],
                    n_jobs=settings["n_jobs"],
                    random_state=config["validation"]["random_seed"] + repeat * 10 + fold,
                )
                model.fit(matrix[train], y[train])
                sums[name][test] += model.predict_proba(matrix[test])[:, 1]
                counts[name][test] += 1
    probabilities = {name: sums[name] / counts[name] for name in features}
    auc = {name: float(roc_auc_score(y, value)) for name, value in probabilities.items()}
    rng = np.random.default_rng(config["validation"]["random_seed"] + 9000)
    primary, secondary = [], []
    while len(primary) < config["validation"]["bootstrap_resamples"]:
        selected = rng.integers(0, len(y), len(y))
        if len(np.unique(y[selected])) < 2:
            continue
        sample_auc = {name: roc_auc_score(y[selected], value[selected]) for name, value in probabilities.items()}
        primary.append(sample_auc["E"] - sample_auc["AB"])
        secondary.append(sample_auc["D"] - sample_auc["C"])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_id": config["protocol_id"],
        "interpretation": config["interpretation"],
        "formal_label_review_gate_passed": False,
        "locked_holdout_accessed": False,
        "source_hashes": {"config": sha256(CONFIG), "feature_matrix": sha256(source)},
        "dataset": {"molecule_count": len(rows), "fold_count": fold_count},
        "roc_auc": auc,
        "paired_auc_differences": {
            "E_minus_AB": interval(primary),
            "D_minus_C": interval(secondary),
        },
    }
    (OUTPUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
