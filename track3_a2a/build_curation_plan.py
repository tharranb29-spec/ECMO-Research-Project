#!/usr/bin/env python3

"""Create a scaffold-diverse, dual-review curation plan for the A2A benchmark."""

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / "data" / "curated" / "chembl251_functional_review_queue.csv"
PLAN = ROOT / "data" / "curated" / "chembl251_curation_plan_220.csv"
AUDIT = ROOT / "outputs" / "dataset" / "curation_plan_220_audit.json"

TARGET_COUNTS = {"agonist": 65, "antagonist": 155}
STRENGTH_ORDER = {"high": 0, "medium": 1, "initial": 2}
BATCH_SIZES = [19, 51, 50, 50, 50]


def evidence_sort_key(row):
    return (
        STRENGTH_ORDER[row["evidence_strength"]],
        -int(row["unique_documents"]),
        -int(row["unique_assays"]),
        -int(row["functional_activity_rows"]),
        row["chembl_id"],
    )


def scaffold_diverse_order(rows, already_used=None):
    """Prefer one representative per new scaffold before scaffold repeats."""
    used = set(already_used or ())
    remaining = sorted(rows, key=evidence_sort_key)
    ordered = []
    while remaining:
        new_scaffold = next((row for row in remaining if row["generic_scaffold"] not in used), None)
        selected = new_scaffold or remaining[0]
        remaining.remove(selected)
        ordered.append(selected)
        used.add(selected["generic_scaffold"])
    return ordered


def interleave_to_ratio(rows_by_class, initial_counts, required):
    """Interleave class pools to approach the final class ratio in every batch."""
    selected = []
    counts = Counter(initial_counts)
    total_target = sum(TARGET_COUNTS.values())
    for _ in range(required):
        next_total = sum(counts.values()) + 1
        deficits = {
            label: (TARGET_COUNTS[label] * next_total / total_target) - counts[label]
            for label in TARGET_COUNTS
            if rows_by_class[label]
        }
        label = max(deficits, key=deficits.get)
        selected.append(rows_by_class[label].pop(0))
        counts[label] += 1
    return selected


def assign_batches(rows):
    start = 0
    for batch_number, size in enumerate(BATCH_SIZES, start=1):
        for priority, row in enumerate(rows[start:start + size], start=1):
            row["curation_batch"] = batch_number
            row["batch_priority"] = priority
        start += size
    if start != len(rows):
        raise ValueError("Batch sizes do not cover the selected plan")


def build_plan(queue_rows):
    high = sorted((row for row in queue_rows if row["evidence_strength"] == "high"), key=evidence_sort_key)
    high_counts = Counter(row["proposed_class"] for row in high)
    if len(high) != BATCH_SIZES[0]:
        raise ValueError(f"Expected {BATCH_SIZES[0]} high-evidence records, found {len(high)}")
    for label, target in TARGET_COUNTS.items():
        if high_counts[label] > target:
            raise ValueError(f"High-evidence {label} records exceed target")

    high_ids = {row["chembl_id"] for row in high}
    used_scaffolds = {row["generic_scaffold"] for row in high}
    pools = {}
    for label, target in TARGET_COUNTS.items():
        candidates = [
            row for row in queue_rows
            if row["proposed_class"] == label and row["chembl_id"] not in high_ids
        ]
        ordered = scaffold_diverse_order(candidates, used_scaffolds)
        needed = target - high_counts[label]
        if len(ordered) < needed:
            raise ValueError(f"Not enough {label} records for target")
        pools[label] = ordered[:needed]

    selected = [dict(row) for row in high]
    selected.extend(dict(row) for row in interleave_to_ratio(pools, high_counts, sum(TARGET_COUNTS.values()) - len(high)))
    assign_batches(selected)
    for row in selected:
        row.update({
            "reviewer_1": "",
            "decision_1": "",
            "reviewer_2": "",
            "decision_2": "",
            "adjudicator": "",
            "final_decision": "",
            "review_notes": "",
        })
        row.pop("review_decision", None)
        row.pop("reviewer", None)
    return selected


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def main():
    with QUEUE.open(newline="", encoding="utf-8") as handle:
        queue_rows = list(csv.DictReader(handle))
    selected = build_plan(queue_rows)
    with PLAN.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)

    class_counts = Counter(row["proposed_class"] for row in selected)
    batch_counts = Counter(int(row["curation_batch"]) for row in selected)
    unique_scaffolds = len({row["generic_scaffold"] for row in selected})
    audit = {
        "created_at": utc_now(),
        "plan_status": "review_required_not_training_eligible",
        "planned_record_count": len(selected),
        "planned_class_counts": dict(sorted(class_counts.items())),
        "planned_agonist_fraction": round(class_counts["agonist"] / len(selected), 4),
        "curation_batch_counts": {str(key): value for key, value in sorted(batch_counts.items())},
        "unique_generic_scaffolds": unique_scaffolds,
        "records_in_repeated_scaffolds": len(selected) - unique_scaffolds,
        "training_eligible_count": 0,
        "replacement_rule": "Rejected, conflicting, or unresolved records do not count toward 220 and require a new reviewed replacement.",
        "next_gate": "independent dual review followed by adjudication and scaffold partitioning",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
