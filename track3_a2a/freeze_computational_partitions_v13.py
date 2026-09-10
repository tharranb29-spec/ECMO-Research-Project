#!/usr/bin/env python3

"""Reconcile v1.3 computational labels with the pre-existing frozen split."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CURATION = ROOT / "data" / "curated" / "chembl251_computational_benchmark_v1.3.json"
FROZEN_V12 = ROOT / "data" / "curated" / "chembl251_provisional_partitions_v1.2.json"
DOCKING = ROOT / "outputs" / "v1.2" / "docking-full" / "report.json"
SPEC = ROOT / "config" / "confirmatory_spec.v1.3.1.json"
OUTPUT = ROOT / "data" / "curated" / "chembl251_computational_partitions_v1.3.json"
AUDIT = ROOT / "outputs" / "v1.3" / "computational_partition_audit.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile_partitions(curated_records, frozen_records, docked_ids):
    curated = {row["chembl_id"]: row for row in curated_records}
    frozen = {row["chembl_id"]: row for row in frozen_records}
    new_ids = set(curated) - set(frozen)
    if new_ids:
        raise ValueError(
            f"Computational curation introduced IDs absent from the frozen v1.2 population: {sorted(new_ids)}. "
            "Do not silently select or assign new records after development results."
        )

    records = []
    for chembl_id in sorted(curated):
        source = curated[chembl_id]
        prior = frozen[chembl_id]
        partition = {
            "provisional_development": "development",
            "provisional_locked_holdout": "locked_holdout",
        }[prior["partition"]]
        docking_available = chembl_id in docked_ids
        records.append({
            "chembl_id": chembl_id,
            "molecule_name": source["molecule_name"],
            "functional_class": source["functional_class"],
            "primary_binary_label": source["primary_binary_label"],
            "evidence_tier": source["evidence_tier"],
            "standardized_smiles": source["standardized_smiles"],
            "standardized_inchikey": source["standardized_inchikey"],
            "generic_murcko_scaffold_smiles": source["generic_murcko_scaffold_smiles"],
            "partition": partition,
            "partition_membership_preserved_from_v1.2": True,
            "docking_available": docking_available,
            "training_eligible": partition == "development" and docking_available,
            "holdout_evaluation_eligible": partition == "locked_holdout" and docking_available,
            "curation_mode": "machine_curated_computational_audit",
            "human_validation_claimed": False,
        })
    return records


def main():
    curated = json.loads(CURATION.read_text(encoding="utf-8"))["records"]
    frozen = json.loads(FROZEN_V12.read_text(encoding="utf-8"))["records"]
    docking = json.loads(DOCKING.read_text(encoding="utf-8"))
    docked_ids = {row["chembl_id"] for row in docking["molecules"] if row["status"] == "valid"}
    records = reconcile_partitions(curated, frozen, docked_ids)

    development_scaffolds = {
        row["generic_murcko_scaffold_smiles"] for row in records if row["partition"] == "development"
    }
    holdout_scaffolds = {
        row["generic_murcko_scaffold_smiles"] for row in records if row["partition"] == "locked_holdout"
    }
    overlap = development_scaffolds & holdout_scaffolds
    if overlap:
        raise RuntimeError(f"Scaffold leakage detected across partitions: {sorted(overlap)}")

    created_at = utc_now()
    output = {
        "schema_version": 1,
        "created_at": created_at,
        "specification_id": "a2a-computational-partitions-v1.3",
        "partition_status": "frozen_membership_reconciled_to_computational_curation",
        "membership_preserved_from_v1.2": True,
        "population_change": "subtractive_evidence_exclusions_only",
        "human_validation_claimed": False,
        "source_hashes": {
            "computational_curation": sha256(CURATION),
            "frozen_v1.2_partitions": sha256(FROZEN_V12),
            "docking_report": sha256(DOCKING),
            "confirmatory_spec": sha256(SPEC),
        },
        "records": records,
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    counts = Counter(row["partition"] for row in records)
    class_counts = Counter((row["partition"], row["functional_class"]) for row in records)
    missing_docking = [row["chembl_id"] for row in records if not row["docking_available"]]
    accepted_ids = {row["chembl_id"] for row in records}
    removed_ids = sorted(row["chembl_id"] for row in frozen if row["chembl_id"] not in accepted_ids)
    audit = {
        "created_at": created_at,
        "specification_id": output["specification_id"],
        "manifest_sha256": sha256(OUTPUT),
        "accepted_record_count": len(records),
        "partition_counts": dict(sorted(counts.items())),
        "class_partition_counts": {
            f"{partition}:{label}": count
            for (partition, label), count in sorted(class_counts.items())
        },
        "development_training_eligible_count": sum(row["training_eligible"] for row in records),
        "holdout_evaluation_eligible_count": sum(row["holdout_evaluation_eligible"] for row in records),
        "missing_docking_ids": missing_docking,
        "development_scaffold_count": len(development_scaffolds),
        "locked_holdout_scaffold_count": len(holdout_scaffolds),
        "scaffold_overlap_count": 0,
        "membership_preserved_from_v1.2": True,
        "removed_from_frozen_population_count": len(removed_ids),
        "removed_from_frozen_population_ids": removed_ids,
        "human_validation_claimed": False,
        "next_gate": "build the v1.3 computational feature matrix without accessing holdout outcomes",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
