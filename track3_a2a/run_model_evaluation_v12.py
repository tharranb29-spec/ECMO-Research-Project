#!/usr/bin/env python3

"""Run provisional Step 4 scaffold-grouped A2A model evaluation."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from sklearn.calibration import calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    matthews_corrcoef,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "model_evaluation.v1.2.json"
OUTPUT_DIR = ROOT / "outputs" / "v1.2" / "model_evaluation"

DESCRIPTOR_COLUMNS = [
    "molecular_weight", "clogp", "h_bond_donors", "h_bond_acceptors",
    "rotatable_bonds", "tpsa", "heavy_atom_count", "qed",
]
C_COLUMNS = [
    "x_inactive_5NM4_affinity_kcal_mol",
    "inactive_5NM4_affinity_sd",
    "inactive_5NM4_median_cnnscore",
    "inactive_5NM4_median_cnnaffinity_pk",
]
D_COLUMNS = [
    "m_affinity_kcal_mol", "d_affinity_kcal_mol", "d_affinity_per_heavy_atom",
    "m_cnnscore", "d_cnnscore", "m_cnnaffinity_pk", "d_cnnaffinity_pk",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_development_rows(config: dict) -> list[dict]:
    path = ROOT / config["input"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row["partition"] == config["development_partition"]]


def numeric_matrix(rows: list[dict], columns: list[str]) -> np.ndarray:
    return np.asarray([[float(row[column]) for column in columns] for row in rows], dtype=float)


def fingerprint_matrix(rows: list[dict], radius: int, bits: int, use_chirality: bool) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=radius, fpSize=bits, includeChirality=use_chirality
    )
    matrix = np.zeros((len(rows), bits), dtype=np.uint8)
    for index, row in enumerate(rows):
        molecule = Chem.MolFromSmiles(row["standardized_smiles"])
        if molecule is None:
            raise ValueError(f"Invalid SMILES for {row['molecule_id']}")
        DataStructs.ConvertToNumpyArray(generator.GetFingerprint(molecule), matrix[index])
    return matrix.astype(float)


def build_feature_sets(rows: list[dict], config: dict) -> tuple[dict[str, np.ndarray], dict[str, list[str]]]:
    fp_config = config["fingerprint"]
    fp = fingerprint_matrix(rows, fp_config["radius"], fp_config["bits"], fp_config["use_chirality"])
    descriptors = numeric_matrix(rows, DESCRIPTOR_COLUMNS)
    single_state = numeric_matrix(rows, C_COLUMNS)
    dual_state = numeric_matrix(rows, D_COLUMNS)
    names = {
        "A": [f"ECFP4_{index}" for index in range(fp.shape[1])],
        "B": DESCRIPTOR_COLUMNS,
        "AB": [f"ECFP4_{index}" for index in range(fp.shape[1])] + DESCRIPTOR_COLUMNS,
        "C": C_COLUMNS,
        "D": D_COLUMNS,
        "E": [f"ECFP4_{index}" for index in range(fp.shape[1])] + DESCRIPTOR_COLUMNS + D_COLUMNS,
    }
    return {
        "A": fp,
        "B": descriptors,
        "AB": np.hstack([fp, descriptors]),
        "C": single_state,
        "D": dual_state,
        "E": np.hstack([fp, descriptors, dual_state]),
    }, names


def estimator(config: dict) -> Pipeline:
    settings = config["estimator"]
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("classifier", LogisticRegression(
            C=settings["C"], penalty=settings["penalty"], solver=settings["solver"],
            class_weight=settings["class_weight"], max_iter=settings["max_iter"],
            random_state=config["validation"]["random_seed"],
        )),
    ])


def metric_set(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    fraction, mean_prediction = calibration_curve(y_true, probabilities, n_bins=5, strategy="quantile")
    return {
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "mcc": float(matthews_corrcoef(y_true, predictions)),
        "sensitivity": float(tp / (tp + fn)) if tp + fn else None,
        "specificity": float(tn / (tn + fp)) if tn + fp else None,
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "calibration_curve": {
            "mean_predicted_probability": mean_prediction.tolist(),
            "observed_positive_fraction": fraction.tolist(),
        },
    }


def percentile_interval(values: list[float], confidence: float) -> dict:
    alpha = (1.0 - confidence) / 2.0
    return {
        "estimate": float(np.median(values)),
        "lower": float(np.quantile(values, alpha)),
        "upper": float(np.quantile(values, 1.0 - alpha)),
    }


def bootstrap_metrics(
    y: np.ndarray,
    model_probabilities: dict[str, np.ndarray],
    config: dict,
) -> tuple[dict, dict]:
    rng = np.random.default_rng(config["validation"]["random_seed"] + 9000)
    count = config["validation"]["bootstrap_resamples"]
    confidence = config["validation"]["confidence_level"]
    aucs = {name: [] for name in model_probabilities}
    primary_deltas, secondary_deltas = [], []
    attempts = 0
    while len(primary_deltas) < count and attempts < count * 2:
        attempts += 1
        selected = rng.integers(0, len(y), len(y))
        sampled_y = y[selected]
        if len(np.unique(sampled_y)) != 2:
            continue
        sampled_aucs = {
            name: float(roc_auc_score(sampled_y, probabilities[selected]))
            for name, probabilities in model_probabilities.items()
        }
        for name, value in sampled_aucs.items():
            aucs[name].append(value)
        primary_deltas.append(sampled_aucs["E"] - sampled_aucs["AB"])
        secondary_deltas.append(sampled_aucs["D"] - sampled_aucs["C"])
    return (
        {name: percentile_interval(values, confidence) for name, values in aucs.items()},
        {
            "primary_E_minus_AB": percentile_interval(primary_deltas, confidence),
            "secondary_D_minus_C": percentile_interval(secondary_deltas, confidence),
            "valid_resamples": len(primary_deltas),
        },
    )


def random_stratified_comparison(
    features: dict[str, np.ndarray],
    y: np.ndarray,
    config: dict,
) -> dict:
    """Report the predeclared optimistic comparator without using it for admission."""
    probability_sums = {name: np.zeros(len(y), dtype=float) for name in features}
    probability_counts = {name: np.zeros(len(y), dtype=int) for name in features}
    for repeat in range(config["validation"]["repeats"]):
        splitter = StratifiedKFold(
            n_splits=config["validation"]["folds"],
            shuffle=True,
            random_state=config["validation"]["random_seed"] + 1000 + repeat,
        )
        for train, test in splitter.split(features["B"], y):
            for name, matrix in features.items():
                pipeline = estimator(config)
                pipeline.fit(matrix[train], y[train])
                probability_sums[name][test] += pipeline.predict_proba(matrix[test])[:, 1]
                probability_counts[name][test] += 1
    threshold = config["estimator"]["classification_threshold"]
    return {
        name: metric_set(y, probability_sums[name] / probability_counts[name], threshold)
        for name in features
    }


def evaluate(rows: list[dict], config: dict) -> tuple[dict, list[dict]]:
    features, feature_names = build_feature_sets(rows, config)
    y = np.asarray([int(row["binary_label"]) for row in rows], dtype=int)
    groups = np.asarray([row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in rows])
    repeats = config["validation"]["repeats"]
    folds = config["validation"]["folds"]
    probability_sums = {name: np.zeros(len(rows), dtype=float) for name in features}
    probability_counts = {name: np.zeros(len(rows), dtype=int) for name in features}
    fold_records = []
    d_coefficients = []

    for repeat in range(repeats):
        splitter = StratifiedGroupKFold(
            n_splits=folds, shuffle=True,
            random_state=config["validation"]["random_seed"] + repeat,
        )
        for fold, (train, test) in enumerate(splitter.split(features["B"], y, groups), start=1):
            record = {
                "repeat": repeat + 1,
                "fold": fold,
                "train_size": len(train),
                "test_size": len(test),
                "test_agonists": int(y[test].sum()),
                "test_antagonists": int(len(test) - y[test].sum()),
                "test_scaffold_count": len(set(groups[test])),
                "models": {},
            }
            for name, matrix in features.items():
                pipeline = estimator(config)
                pipeline.fit(matrix[train], y[train])
                probabilities = pipeline.predict_proba(matrix[test])[:, 1]
                probability_sums[name][test] += probabilities
                probability_counts[name][test] += 1
                record["models"][name] = metric_set(
                    y[test], probabilities, config["estimator"]["classification_threshold"]
                ) if len(np.unique(y[test])) == 2 else {"roc_auc": None}
                if name == "D":
                    coefficient = pipeline.named_steps["classifier"].coef_[0]
                    d_coefficients.append(float(coefficient[feature_names["D"].index("d_affinity_kcal_mol")]))
            fold_records.append(record)

    averaged = {
        name: probability_sums[name] / probability_counts[name]
        for name in features
    }
    threshold = config["estimator"]["classification_threshold"]
    aggregate_metrics = {name: metric_set(y, probabilities, threshold) for name, probabilities in averaged.items()}
    random_metrics = random_stratified_comparison(features, y, config)
    auc_intervals, paired_intervals = bootstrap_metrics(y, averaged, config)
    tolerance = config["admission_tolerance"]
    primary = paired_intervals["primary_E_minus_AB"]
    secondary = paired_intervals["secondary_D_minus_C"]
    gate_checks = {
        "model_E_auc": aggregate_metrics["E"]["roc_auc"] >= tolerance["minimum_model_E_ROC_AUC"],
        "model_E_sensitivity": aggregate_metrics["E"]["sensitivity"] >= tolerance["minimum_model_E_agonist_sensitivity"],
        "primary_delta": primary["estimate"] >= tolerance["minimum_primary_delta_auc"],
        "primary_ci_lower": primary["lower"] >= tolerance["minimum_primary_delta_ci_lower"],
        "secondary_delta": secondary["estimate"] >= tolerance["minimum_secondary_delta_auc"],
        "secondary_ci_lower": secondary["lower"] >= tolerance["minimum_secondary_delta_ci_lower"],
    }
    predictions = []
    for index, row in enumerate(rows):
        predictions.append({
            "molecule_id": row["molecule_id"],
            "label": row["label"],
            "binary_label": int(row["binary_label"]),
            "scaffold": groups[index],
            **{f"probability_{name}": float(averaged[name][index]) for name in averaged},
        })
    return {
        "aggregate_metrics": aggregate_metrics,
        "optimistic_random_stratified_metrics": random_metrics,
        "random_minus_scaffold_roc_auc": {
            name: random_metrics[name]["roc_auc"] - aggregate_metrics[name]["roc_auc"]
            for name in aggregate_metrics
        },
        "roc_auc_bootstrap_intervals": auc_intervals,
        "paired_auc_differences": paired_intervals,
        "d_affinity_standardized_coefficient_across_folds": percentile_interval(
            d_coefficients, config["validation"]["confidence_level"]
        ),
        "admission_gate_checks": gate_checks,
        "development_admission_gate_passed": all(gate_checks.values()),
        "folds": fold_records,
    }, predictions


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    source = ROOT / config["input"]
    rows = load_development_rows(config)
    results, predictions = evaluate(rows, config)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    predictions_path = OUTPUT_DIR / "development_oof_predictions.csv"
    with predictions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_id": config["protocol_id"],
        "run_mode": config["run_mode"],
        "formal_label_review_gate_passed": False,
        "locked_holdout_accessed": False,
        "source_hashes": {
            "model_evaluation_config": sha256(CONFIG),
            "feature_matrix": sha256(source),
        },
        "development_dataset": {
            "molecule_count": len(rows),
            "class_counts": dict(sorted(Counter(row["label"] for row in rows).items())),
            "unique_scaffolds": len({row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in rows}),
        },
        "review_gate_note": "Team review was reported by the project lead, but the record-level reviewer fields remain blank; these results cannot be promoted as independently validated.",
        **results,
        "predictions_sha256": sha256(predictions_path),
        "next_gate": "complete and hash record-level dual-review fields, then freeze the model before one locked-holdout evaluation",
    }
    report_path = OUTPUT_DIR / "development_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = {
        "development_dataset": report["development_dataset"],
        "aggregate_roc_auc": {name: value["roc_auc"] for name, value in report["aggregate_metrics"].items()},
        "paired_auc_differences": report["paired_auc_differences"],
        "development_admission_gate_passed": report["development_admission_gate_passed"],
        "formal_label_review_gate_passed": False,
        "locked_holdout_accessed": False,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
