#!/usr/bin/env python3
"""Reproduce the frozen v1.6 development comparisons without external outcomes."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from run_continuous_activity_v15 import evaluate_endpoint, write_csv


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "config" / "protocol.v1.6.json"
SUMMARY = ROOT / "data" / "curated" / "activity_molecule_summary_v15_exploratory.csv"
FEATURES = ROOT / "outputs" / "v1.3" / "docking_clean_computational.csv"
OUTPUT = ROOT / "outputs" / "v1.6" / "model_reproduction"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    protocol = json.loads(PROTOCOL.read_text())
    rf_parameters = protocol["models"]["chemistry_rf_comparator"]["parameters"]
    adapter = {
        "development_evaluation": protocol["development_reproduction"],
        "models": {"qsar_primary": {"parameters": rf_parameters}},
        "uncertainty": {"random_seed": protocol["external_confirmation"]["random_seed"]},
    }
    features = {row["molecule_id"]: row for row in read_csv(FEATURES)}
    rows = []
    for summary in read_csv(SUMMARY):
        if (
            summary["endpoint_name"] == "pBind_Ki"
            and summary["review_status"] == "admitted_exploratory"
            and summary["development_partition"] == "development"
        ):
            if summary["molecule_id"] not in features:
                raise RuntimeError(f"missing feature row: {summary['molecule_id']}")
            rows.append({**features[summary["molecule_id"]], **summary})

    result, predictions = evaluate_endpoint(rows, adapter, "pBind_Ki", "v1.6_frozen_reproduction")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    prediction_path = OUTPUT / "development_oof_predictions.csv"
    write_csv(prediction_path, predictions)
    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": protocol["specification_id"],
        "status": "complete_development_reproduction",
        "claim_status": "development_only_not_external_confirmation",
        "historical_locked_holdout_rows_used": 0,
        "external_outcomes_loaded": False,
        "endpoint": "pBind_Ki",
        "model_mapping": {
            "Mean": protocol["models"]["required_baseline"],
            "AB_Ridge": protocol["models"]["primary_external_predictor"],
            "AB_RF": protocol["models"]["chemistry_rf_comparator"],
            "E_RF": protocol["models"]["docking_increment_comparator"],
        },
        "result": result,
        "source_hashes": {
            "protocol": sha256(PROTOCOL),
            "summary": sha256(SUMMARY),
            "features": sha256(FEATURES),
            "runner": sha256(Path(__file__)),
        },
        "prediction_file": str(prediction_path.relative_to(ROOT)),
        "prediction_sha256": sha256(prediction_path),
        "promotion_allowed": False,
    }
    report_path = OUTPUT / "development_results.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "n": result["n"],
        "scaffolds": result["scaffold_count"],
        "metrics": result["metrics"],
        "prediction_sha256": report["prediction_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
