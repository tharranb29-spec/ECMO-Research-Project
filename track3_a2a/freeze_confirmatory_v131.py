#!/usr/bin/env python3

"""Freeze the v1.3.1 confirmatory implementation before holdout evaluation."""

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "confirmatory_spec.v1.3.1.json"
FEATURES = ROOT / "outputs" / "v1.3" / "docking_clean_computational.csv"
PARTITIONS = ROOT / "data" / "curated" / "chembl251_computational_partitions_v1.3.json"
FEATURE_AUDIT = ROOT / "outputs" / "v1.3" / "feature_construction_audit.json"
RUNNER = ROOT / "run_confirmatory_holdout_v131.py"
MODEL_CONFIG = ROOT / "config" / "model_evaluation.v1.2.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["freeze_manifest"]
    if not RUNNER.exists():
        raise FileNotFoundError("Confirmatory runner must exist before the preflight can be frozen.")

    with FEATURES.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    development = [row for row in rows if row["partition"] == "development"]
    holdout = [row for row in rows if row["partition"] == "locked_holdout"]
    if len(holdout) < 1:
        raise RuntimeError("No locked-holdout records are available.")
    if sum(row["label"] == "agonist" for row in holdout) < config["population"]["minimum_holdout_agonists"]:
        raise RuntimeError("The locked holdout does not meet the predeclared agonist floor.")

    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"],
        "status": "frozen_before_first_and_only_holdout_evaluation",
        "source_hashes": {
            "confirmatory_spec": sha256(CONFIG),
            "feature_matrix": sha256(FEATURES),
            "partition_manifest": sha256(PARTITIONS),
            "feature_audit": sha256(FEATURE_AUDIT),
            "holdout_runner": sha256(RUNNER),
            "predictive_model_config_v1.2": sha256(MODEL_CONFIG),
        },
        "development": {
            "record_count": len(development),
            "class_counts": dict(sorted(Counter(row["label"] for row in development).items())),
        },
        "locked_holdout": {
            "record_count": len(holdout),
            "class_counts": dict(sorted(Counter(row["label"] for row in holdout).items())),
            "outcomes_used_for_model_selection": False,
        },
        "locked_method": {
            "formula": config["model"]["formula"],
            "chemistry_descriptors": config["model"]["chemistry_descriptors"],
            "pca_components": config["model"]["pca_components"],
            "estimator": config["model"]["estimator"],
            "endpoint": config["confirmatory_endpoint"],
            "predictive_sensitivity": config["predictive_sensitivity"],
        },
        "software": {"numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "human_validation_claimed": False,
        "next_gate": "run the hash-verified v1.3.1 holdout evaluator exactly once without changing this manifest",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
