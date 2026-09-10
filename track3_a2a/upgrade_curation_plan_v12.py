#!/usr/bin/env python3

"""Version the 220-record curation plan with independent evidence-tier review."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "curated" / "chembl251_curation_plan_220.csv"
OUTPUT = ROOT / "data" / "curated" / "chembl251_curation_plan_220_v1.2.csv"
AUDIT = ROOT / "outputs" / "dataset" / "curation_plan_220_v1.2_audit.json"
REVIEW_FIELDS = [
    "reviewer_1", "decision_1", "evidence_tier_1",
    "reviewer_2", "decision_2", "evidence_tier_2",
    "adjudicator", "final_decision", "final_evidence_tier",
    "tier_rationale", "review_notes",
]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def main():
    if OUTPUT.exists():
        raise RuntimeError(
            "The versioned v1.2 review plan already exists and is immutable. "
            "Create a new specification version rather than overwriting reviewer evidence."
        )
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    existing_review_fields = {
        "reviewer_1", "decision_1", "reviewer_2", "decision_2",
        "adjudicator", "final_decision", "review_notes",
    }
    if any(row.get(field, "").strip() for row in rows for field in existing_review_fields):
        raise RuntimeError("Source plan already contains review decisions; migration stopped to protect human evidence")

    base_fields = [field for field in rows[0] if field not in existing_review_fields]
    versioned = []
    for row in rows:
        clean = {field: row.get(field, "") for field in base_fields}
        clean.update({field: "" for field in REVIEW_FIELDS})
        versioned.append(clean)
    with OUTPUT.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=base_fields + REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(versioned)

    audit = {
        "created_at": utc_now(),
        "specification_id": "a2a-functional-classification-v1.2",
        "source_plan": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "output_plan": str(OUTPUT.relative_to(ROOT)),
        "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "record_count": len(versioned),
        "completed_review_fields": 0,
        "training_eligible_count": 0,
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
