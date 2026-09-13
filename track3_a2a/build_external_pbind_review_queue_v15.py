#!/usr/bin/env python3

"""Create a label-blind, scaffold-diverse primary-paper review queue."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INTAKE = ROOT / "outputs" / "v1.5" / "external_pbind_intake" / "eligible_for_primary_review.csv"
OUTPUT = ROOT / "outputs" / "v1.5" / "external_pbind_intake"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_key(value: str) -> str:
    return hashlib.sha256(f"a2a-pbind-review-v1.5|{value}".encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=240)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    with INTAKE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    by_scaffold = defaultdict(list)
    for row in rows:
        by_scaffold[row["generic_murcko_scaffold_smiles"] or "ACYCLIC"].append(row)
    scaffold_order = sorted(by_scaffold, key=stable_key)
    queue = []
    round_index = 0
    while len(queue) < args.size:
        added = 0
        for scaffold in scaffold_order:
            candidates = sorted(
                by_scaffold[scaffold],
                key=lambda row: (
                    not bool(row["doi"] and row["pmid"]),
                    stable_key(row["candidate_id"]),
                ),
            )
            if round_index < len(candidates):
                queue.append(candidates[round_index])
                added += 1
                if len(queue) == args.size:
                    break
        if not added:
            break
        round_index += 1
    fields = list(rows[0]) + [
        "queue_rank", "reviewer_1", "reviewer_1_decision", "reviewer_2",
        "reviewer_2_decision", "adjudicator", "final_evidence_decision", "review_notes",
    ]
    prepared = []
    for rank, row in enumerate(queue, 1):
        prepared.append({
            **row,
            "queue_rank": rank,
            "reviewer_1": "",
            "reviewer_1_decision": "",
            "reviewer_2": "",
            "reviewer_2_decision": "",
            "adjudicator": "",
            "final_evidence_decision": "",
            "review_notes": "",
        })
    args.output.mkdir(parents=True, exist_ok=True)
    queue_path = args.output / "primary_evidence_review_queue.csv"
    with queue_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(prepared)
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "label_blind_review_queue_ready_not_cohort_membership",
        "outcomes_loaded": False,
        "membership_frozen": False,
        "source_candidate_count": len(rows),
        "queue_candidate_count": len(prepared),
        "queue_generic_scaffold_count": len({row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in prepared}),
        "selection_rule": (
            "Deterministic hash order, one candidate per generic scaffold before any second candidate; "
            "within a scaffold, candidates carrying both DOI and PMID are preferred. No outcome field is read."
        ),
        "source_hash": sha256(INTAKE),
        "queue_hash": sha256(queue_path),
        "next_gate": "Complete dual primary-evidence review; this queue is not the frozen external cohort.",
    }
    audit_path = args.output / "primary_evidence_review_queue_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
