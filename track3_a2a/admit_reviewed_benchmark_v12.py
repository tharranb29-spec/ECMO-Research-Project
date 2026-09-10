#!/usr/bin/env python3

"""Admit only independently reviewed A2A labels with agreed evidence tiers."""

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "data" / "curated" / "chembl251_curation_plan_220_v1.2.csv"
STANDARDIZED = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
OUTPUT = ROOT / "data" / "curated" / "chembl251_reviewed_benchmark_v1.2.json"
AUDIT = ROOT / "outputs" / "dataset" / "reviewed_benchmark_v1.2_admission_audit.json"

ACCEPT = {"accept_agonist": "agonist", "accept_antagonist": "antagonist"}
REJECT = {"reject_binding_only", "reject_context", "reject_conflict", "needs_full_text"}
ALLOWED_DECISIONS = set(ACCEPT) | REJECT | {""}
ALLOWED_TIERS = {"tier_1", "tier_2", ""}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def review_status(row):
    reviewers = [row.get("reviewer_1", "").strip(), row.get("reviewer_2", "").strip()]
    decisions = [row.get("decision_1", "").strip(), row.get("decision_2", "").strip()]
    tiers = [row.get("evidence_tier_1", "").strip(), row.get("evidence_tier_2", "").strip()]
    final_decision = row.get("final_decision", "").strip()
    final_tier = row.get("final_evidence_tier", "").strip()
    invalid_decisions = sorted({value for value in decisions + [final_decision] if value not in ALLOWED_DECISIONS})
    invalid_tiers = sorted({value for value in tiers + [final_tier] if value not in ALLOWED_TIERS})
    if invalid_decisions or invalid_tiers:
        return "invalid", f"unsupported decisions={invalid_decisions}; tiers={invalid_tiers}"
    if not all(reviewers) or not all(decisions):
        return "pending", "two completed named reviews are required"
    if reviewers[0].casefold() == reviewers[1].casefold():
        return "invalid", "reviewers must be different people"

    decisions_agree = decisions[0] == decisions[1]
    if decisions_agree:
        if final_decision and final_decision != decisions[0]:
            return "invalid", "final decision conflicts with reviewer agreement"
        final_decision = decisions[0]
    elif not row.get("adjudicator", "").strip() or not final_decision:
        return "needs_adjudication", "class disagreement requires an adjudicator and final decision"

    if final_decision in REJECT:
        return "rejected", final_decision
    if final_decision not in ACCEPT:
        return "pending", "accepted class is unresolved"
    if not all(tiers):
        return "pending", "accepted records require evidence tiers from both reviewers"

    tiers_agree = tiers[0] == tiers[1]
    if tiers_agree:
        if final_tier and final_tier != tiers[0]:
            return "invalid", "final tier conflicts with reviewer agreement"
        final_tier = tiers[0]
    elif not row.get("adjudicator", "").strip() or not final_tier:
        return "needs_adjudication", "tier disagreement requires an adjudicator and final tier"
    return "accepted", {"decision": final_decision, "tier": final_tier}


def main():
    with PLAN.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    structures = {row["chembl_id"]: row for row in json.loads(STANDARDIZED.read_text(encoding="utf-8"))["records"]}
    statuses = Counter()
    accepted = []
    issues = []
    for row in rows:
        status, detail = review_status(row)
        statuses[status] += 1
        if status == "accepted":
            functional_class = ACCEPT[detail["decision"]]
            accepted.append({
                **structures[row["chembl_id"]],
                "dataset_partition": "reviewed_unpartitioned",
                "functional_class": functional_class,
                "primary_binary_label": 1 if functional_class == "agonist" else 0,
                "evidence_status": "verified_functional",
                "evidence_tier": detail["tier"],
                "primary_analysis_eligible": detail["tier"] == "tier_1",
                "reviewed_by": [row["reviewer_1"], row["reviewer_2"]],
                "adjudicator": row.get("adjudicator") or None,
                "tier_rationale": row.get("tier_rationale") or None,
                "review_notes": row.get("review_notes") or None,
                "training_eligible": False,
                "training_blocker": "scaffold partition and locked-holdout hash not yet frozen"
            })
        elif status in {"invalid", "needs_adjudication"}:
            issues.append({"chembl_id": row.get("chembl_id"), "status": status, "detail": detail})

    output = {
        "schema_version": 2,
        "created_at": utc_now(),
        "specification_id": "a2a-functional-classification-v1.2",
        "dataset_partition": "reviewed_unpartitioned",
        "training_eligible_count": 0,
        "records": accepted
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    audit = {
        "created_at": utc_now(),
        "specification_id": "a2a-functional-classification-v1.2",
        "review_plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "plan_record_count": len(rows),
        "decision_status_counts": dict(sorted(statuses.items())),
        "accepted_record_count": len(accepted),
        "accepted_class_counts": dict(sorted(Counter(row["functional_class"] for row in accepted).items())),
        "accepted_tier_counts": dict(sorted(Counter(row["evidence_tier"] for row in accepted).items())),
        "primary_analysis_eligible_count": sum(row["primary_analysis_eligible"] for row in accepted),
        "training_eligible_count": 0,
        "issues": issues,
        "next_gate": "freeze scaffold-grouped development and locked-holdout partitions"
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
