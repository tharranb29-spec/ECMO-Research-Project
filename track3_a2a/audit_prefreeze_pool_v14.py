#!/usr/bin/env python3

"""Audit whether the pre-v1.4 ChEMBL pool can count as external evidence."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STANDARDIZED = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
REVIEW = ROOT / "data" / "curated" / "chembl251_functional_review_packet.json"
HISTORICAL = ROOT / "data" / "curated" / "chembl251_computational_partitions_v1.3.json"
OUTPUT = ROOT / "outputs" / "v1.4" / "prefreeze_pool_independence_audit.json"


def build_report() -> dict:
    standardized_payload = json.loads(STANDARDIZED.read_text(encoding="utf-8"))
    review_payload = json.loads(REVIEW.read_text(encoding="utf-8"))
    historical_payload = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    chemistry = {row["chembl_id"]: row for row in standardized_payload["records"]}
    reviewed = {row["chembl_id"]: row for row in review_payload["records"]}
    historical = historical_payload["records"]
    historical_ids = {row["chembl_id"] for row in historical}
    historical_inchikeys = {row["standardized_inchikey"] for row in historical}
    historical_scaffolds = {row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in historical}
    unused_ids = sorted(set(reviewed) - historical_ids)
    structurally_independent = []
    overlaps = Counter()
    class_counts = Counter()
    for chembl_id in unused_ids:
        row = chemistry[chembl_id]
        class_counts[reviewed[chembl_id]["proposed_class"]] += 1
        exact = row["standardized_inchikey"] in historical_inchikeys
        scaffold = (row["generic_murcko_scaffold_smiles"] or "ACYCLIC") in historical_scaffolds
        overlaps["exact_structure_overlap" if exact else "no_exact_structure_overlap"] += 1
        overlaps["generic_scaffold_overlap" if scaffold else "no_generic_scaffold_overlap"] += 1
        if not exact and not scaffold:
            structurally_independent.append(chembl_id)
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "audit_question": "Can unused records from the September 4 ChEMBL functional review pool be the definitive v1.4 external cohort?",
        "answer": "no",
        "reason": "The complete review packet was available to the project before model and holdout analysis; disjoint chemistry alone does not remove prior-visibility and selection-bias risk.",
        "source_created_at": review_payload["created_at"],
        "historical_feature_freeze_at": "2026-09-10T13:08:35.650328+00:00",
        "reviewed_source_pool_count": len(reviewed),
        "v1_3_partition_count": len(historical_ids),
        "unused_prefreeze_record_count": len(unused_ids),
        "unused_prefreeze_class_counts": dict(sorted(class_counts.items())),
        "overlap_counts": dict(sorted(overlaps.items())),
        "structure_and_scaffold_disjoint_count": len(structurally_independent),
        "definitive_external_eligible_count": 0,
        "retrospective_stress_test_candidate_count": len(structurally_independent),
        "retrospective_stress_test_candidate_ids": structurally_independent,
        "permitted_use": "retrospective_external-like_stress_test_only",
        "prohibited_claim": "independent_external_validation",
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError("Pre-freeze pool audit already exists; refusing to overwrite it.")
    report = build_report()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "retrospective_stress_test_candidate_ids"}, indent=2))


if __name__ == "__main__":
    main()
