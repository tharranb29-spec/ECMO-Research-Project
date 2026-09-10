#!/usr/bin/env python3

"""Build the A2A feature matrix from admitted v1.3 computational labels."""

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.build_feature_matrix_v12 import (
    build_feature_row,
    hard_filter_sensitivity,
    index_unique,
    quality_summary,
)


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "feature_construction.v1.3.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    input_paths = {name: ROOT / value for name, value in config["inputs"].items()}
    inputs = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in input_paths.items()}
    partitions = index_unique(inputs["partitions"]["records"], "chembl_id")
    decisions = index_unique(inputs["evidence_review"]["records"], "chembl_id")
    chemistry = index_unique(
        inputs["standardized_chemistry"]["records"],
        "chembl_id",
        ("standardized_smiles", "descriptors", "murcko_scaffold_smiles"),
    )

    rows = []
    missing_metadata = []
    excluded_by_curation = []
    for molecule in inputs["docking_report"]["molecules"]:
        chembl_id = molecule["chembl_id"]
        if chembl_id not in partitions:
            excluded_by_curation.append(chembl_id)
            continue
        if chembl_id not in decisions or chembl_id not in chemistry:
            missing_metadata.append(chembl_id)
            continue
        decision = decisions[chembl_id]
        if not decision["dataset_admission_eligible"]:
            continue
        evidence_adapter = {"recommended_evidence_tier": decision["evidence_tier"]}
        row = build_feature_row(molecule, partitions[chembl_id], evidence_adapter, chemistry[chembl_id], config)
        row["label_status"] = config["label_status"]
        row["training_eligible"] = partitions[chembl_id]["training_eligible"]
        row["holdout_evaluation_eligible"] = partitions[chembl_id]["holdout_evaluation_eligible"]
        row["human_approval_required"] = False
        row["evidence_source_url"] = decision["representative_source_url"]
        row["evidence_decision"] = decision["decision"]
        rows.append(row)

    rows.sort(key=lambda row: row["molecule_id"])
    output_path = ROOT / config["outputs"]["feature_matrix"]
    audit_path = ROOT / config["outputs"]["audit"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    development = [row for row in rows if row["partition"] == "development"]
    holdout = [row for row in rows if row["partition"] == "locked_holdout"]
    development_scaffolds = {row["generic_murcko_scaffold_smiles"] for row in development}
    holdout_scaffolds = {row["generic_murcko_scaffold_smiles"] for row in holdout}
    overlap = sorted(development_scaffolds & holdout_scaffolds)
    if overlap:
        raise RuntimeError(f"Scaffold leakage detected in v1.3 feature matrix: {overlap}")

    audit = {
        "schema_version": 1,
        "created_at": utc_now(),
        "protocol_id": config["protocol_id"],
        "source_hashes": {name: sha256(path) for name, path in input_paths.items()},
        "feature_matrix_sha256": sha256(output_path),
        "output_row_count": len(rows),
        "development_row_count": len(development),
        "locked_holdout_row_count": len(holdout),
        "class_counts": dict(sorted(Counter(row["label"] for row in rows).items())),
        "partition_class_counts": dict(sorted(Counter(f"{row['partition']}:{row['label']}" for row in rows).items())),
        "missing_metadata_ids": missing_metadata,
        "excluded_by_computational_curation_ids": sorted(excluded_by_curation),
        "accepted_without_valid_docking_ids": sorted(
            chembl_id for chembl_id, row in partitions.items() if not row["docking_available"]
        ),
        "pose_quality": quality_summary(rows),
        "hard_filter_sensitivity_not_primary": hard_filter_sensitivity(rows),
        "scaffold_overlap_count": 0,
        "label_status": config["label_status"],
        "human_approval_required": False,
        "human_validation_claimed": False,
        "holdout_accessed": False,
        "next_gate": "freeze development-only model settings, then perform one confirmatory evaluation on the locked holdout",
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
