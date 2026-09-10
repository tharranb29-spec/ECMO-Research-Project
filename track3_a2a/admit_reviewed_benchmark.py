#!/usr/bin/env python3

"""Validate dual-review decisions and create an admitted A2A benchmark snapshot."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_PLAN = ROOT / "data" / "curated" / "chembl251_curation_plan_220.csv"
STANDARDIZED = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
OUTPUT = ROOT / "data" / "curated" / "chembl251_reviewed_benchmark.json"
AUDIT = ROOT / "outputs" / "dataset" / "reviewed_benchmark_admission_audit.json"

ACCEPT = {"accept_agonist": "agonist", "accept_antagonist": "antagonist"}
REJECT = {"reject_binding_only", "reject_context", "reject_conflict", "needs_full_text"}
ALLOWED = set(ACCEPT) | REJECT | {""}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def decision_status(row):
    d1 = row.get("decision_1", "").strip()
    d2 = row.get("decision_2", "").strip()
    final = row.get("final_decision", "").strip()
    invalid = sorted({value for value in (d1, d2, final) if value not in ALLOWED})
    if invalid:
        return "invalid_decision", f"Unsupported decision(s): {invalid}"
    if not row.get("reviewer_1", "").strip() or not row.get("reviewer_2", "").strip():
        return "pending", "Two named reviewers are required"
    if not d1 or not d2:
        return "pending", "Both reviewer decisions are required"
    if d1 == d2:
        if final and final != d1:
            return "invalid_decision", "Final decision conflicts with reviewer agreement"
        final = d1
    else:
        if not row.get("adjudicator", "").strip() or not final:
            return "needs_adjudication", "Disagreement requires a named adjudicator and final decision"
    if final in ACCEPT:
        return "accepted", final
    if final in REJECT:
        return "rejected", final
    return "pending", "Final decision is missing"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    args = parser.parse_args()
    with args.plan.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    structures = {
        row["chembl_id"]: row
        for row in json.loads(STANDARDIZED.read_text(encoding="utf-8"))["records"]
    }
    statuses = Counter()
    issues = []
    accepted = []
    for row in rows:
        status, detail = decision_status(row)
        statuses[status] += 1
        if status == "accepted":
            functional_class = ACCEPT[detail]
            source = structures[row["chembl_id"]]
            accepted.append({
                **source,
                "dataset_partition": "reviewed_unpartitioned",
                "functional_class": functional_class,
                "primary_binary_label": 1 if functional_class == "agonist" else 0,
                "evidence_status": "verified_functional",
                "reviewed_by": [row["reviewer_1"], row["reviewer_2"]],
                "adjudicator": row.get("adjudicator") or None,
                "review_notes": row.get("review_notes") or None,
                "training_eligible": False,
                "training_blocker": "scaffold partition and locked-holdout hash not yet frozen",
            })
        elif status not in {"pending", "rejected"}:
            issues.append({"chembl_id": row.get("chembl_id"), "status": status, "detail": detail})

    output = {
        "schema_version": 1,
        "created_at": utc_now(),
        "source_plan": str(args.plan),
        "dataset_partition": "reviewed_unpartitioned",
        "training_eligible_count": 0,
        "records": accepted,
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    audit = {
        "created_at": utc_now(),
        "review_plan_sha256": hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        "plan_record_count": len(rows),
        "decision_status_counts": dict(sorted(statuses.items())),
        "accepted_class_counts": dict(sorted(Counter(row["functional_class"] for row in accepted).items())),
        "accepted_record_count": len(accepted),
        "training_eligible_count": 0,
        "issues": issues,
        "next_gate": "freeze scaffold-grouped development and locked-holdout partitions",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
