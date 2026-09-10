#!/usr/bin/env python3

"""Freeze scaffold-separated prototype partitions from AI-reviewed A2A labels."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AI_REVIEW = ROOT / "data" / "curated" / "chembl251_ai_assisted_review_v1.2.json"
STRUCTURES = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
SPEC = ROOT / "config" / "analysis_spec.v1.2.json"
OUTPUT = ROOT / "data" / "curated" / "chembl251_provisional_partitions_v1.2.json"
AUDIT = ROOT / "outputs" / "dataset" / "provisional_partitions_v1.2_audit.json"
HOLDOUT_TARGET = {"agonist": 13, "antagonist": 30}
SALT = "a2a-v1.2-provisional-holdout-20260906"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose_holdout_groups(groups):
    """Find an exact class-balanced subset without splitting scaffold groups."""
    ordered = sorted(groups, key=lambda key: hashlib.sha256(f"{SALT}|{key}".encode()).hexdigest())
    states = {(0, 0): []}
    for scaffold in ordered:
        counts = Counter(item["functional_class"] for item in groups[scaffold])
        da, dn = counts["agonist"], counts["antagonist"]
        updates = dict(states)
        for (a_count, n_count), selected in states.items():
            new_state = (a_count + da, n_count + dn)
            if new_state[0] <= HOLDOUT_TARGET["agonist"] and new_state[1] <= HOLDOUT_TARGET["antagonist"]:
                updates.setdefault(new_state, selected + [scaffold])
        states = updates
    target = (HOLDOUT_TARGET["agonist"], HOLDOUT_TARGET["antagonist"])
    if target not in states:
        raise RuntimeError(f"No scaffold-group subset reaches holdout target {target}")
    return set(states[target])


def main():
    reviews = json.loads(AI_REVIEW.read_text(encoding="utf-8"))["records"]
    structures = {row["chembl_id"]: row for row in json.loads(STRUCTURES.read_text(encoding="utf-8"))["records"]}
    included = [row for row in reviews if row["recommended_evidence_tier"] == "tier_1"]
    excluded = [row for row in reviews if row["recommended_evidence_tier"] != "tier_1"]
    records = []
    groups = defaultdict(list)
    for review in included:
        structure = structures[review["chembl_id"]]
        row = {
            "chembl_id": review["chembl_id"],
            "molecule_name": review["molecule_name"],
            "functional_class": review["proposed_class"],
            "primary_binary_label": 1 if review["proposed_class"] == "agonist" else 0,
            "standardized_smiles": structure["standardized_smiles"],
            "standardized_inchikey": structure["standardized_inchikey"],
            "generic_murcko_scaffold_smiles": structure["generic_murcko_scaffold_smiles"],
            "evidence_basis": "AI-assisted deterministic review of official ChEMBL metadata",
            "human_validation_claimed": False,
            "final_training_eligible": False,
            "provisional_model_development_eligible": True
        }
        records.append(row)
        groups[row["generic_murcko_scaffold_smiles"]].append(row)
    holdout_scaffolds = choose_holdout_groups(groups)
    for row in records:
        row["partition"] = "provisional_locked_holdout" if row["generic_murcko_scaffold_smiles"] in holdout_scaffolds else "provisional_development"

    output = {
        "schema_version": 1,
        "created_at": utc_now(),
        "specification_id": "a2a-functional-classification-v1.2",
        "partition_status": "provisional_computational_only",
        "human_validation_claimed": False,
        "final_training_eligible_count": 0,
        "source_hashes": {
            "analysis_spec": sha256(SPEC),
            "ai_review": sha256(AI_REVIEW),
            "standardized_structures": sha256(STRUCTURES)
        },
        "holdout_selection_salt": SALT,
        "records": records,
        "excluded_records": [
            {
                "chembl_id": row["chembl_id"],
                "proposed_class": row["proposed_class"],
                "reason": row["ai_recommendation"]
            }
            for row in excluded
        ]
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    partition_counts = Counter(row["partition"] for row in records)
    class_partition_counts = Counter((row["partition"], row["functional_class"]) for row in records)
    development_scaffolds = {row["generic_murcko_scaffold_smiles"] for row in records if row["partition"] == "provisional_development"}
    locked_scaffolds = {row["generic_murcko_scaffold_smiles"] for row in records if row["partition"] == "provisional_locked_holdout"}
    if development_scaffolds & locked_scaffolds:
        raise RuntimeError("Scaffold leakage detected between provisional partitions")
    audit = {
        "created_at": utc_now(),
        "included_record_count": len(records),
        "excluded_record_count": len(excluded),
        "included_class_counts": dict(sorted(Counter(row["functional_class"] for row in records).items())),
        "partition_counts": dict(sorted(partition_counts.items())),
        "class_partition_counts": {
            f"{partition}:{label}": count
            for (partition, label), count in sorted(class_partition_counts.items())
        },
        "development_scaffold_count": len(development_scaffolds),
        "locked_holdout_scaffold_count": len(locked_scaffolds),
        "scaffold_overlap_count": 0,
        "human_validation_claimed": False,
        "final_training_eligible_count": 0,
        "next_gate": "prepare 3D ligand states and run versioned provisional dual-state GNINA docking"
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
