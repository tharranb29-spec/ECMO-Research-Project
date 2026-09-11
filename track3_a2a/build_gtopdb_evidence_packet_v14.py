#!/usr/bin/env python3

"""Build a sealed GtoPdb evidence packet and a label-free review queue."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.build_evidence_review_queue import classify_readout


ROOT = Path(__file__).resolve().parent
ELIGIBLE = ROOT / "outputs" / "v1.4" / "external_cohort" / "gtopdb_2026.2" / "eligible_candidates.csv"
ACQUISITION_AUDIT = ROOT / "data" / "raw" / "external" / "gtopdb_2026.2" / "source_acquisition_audit.json"
OUTPUT_DIR = ROOT / "outputs" / "v1.4" / "evidence_review" / "gtopdb_2026.2"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_class(action: str) -> str | None:
    value = (action or "").strip().lower()
    if value in {"agonist", "full agonist"}:
        return "agonist"
    if value == "antagonist":
        return "antagonist"
    return None


def primary_references(interaction: dict) -> list[dict]:
    return [
        {
            "reference_id": ref.get("referenceId"),
            "pmid": str(ref["pmid"]) if ref.get("pmid") else None,
            "title": ref.get("articleTitle"),
            "journal": ref.get("title"),
            "year": ref.get("year"),
        }
        for ref in interaction.get("refs", [])
        if ref.get("type") == "Journal" and ref.get("pmid")
    ]


def adjudicate_candidate(candidate: dict, interactions: list[dict]) -> dict:
    classes = sorted({
        normalized for row in interactions
        if (normalized := normalized_class(row.get("action"))) is not None
    })
    evidence_rows = []
    for row in interactions:
        refs = primary_references(row)
        readout = classify_readout(row.get("assayDescription"))
        evidence_rows.append({
            "interaction_id": row.get("interactionId"),
            "proposed_class": normalized_class(row.get("action")),
            "source_action": row.get("action"),
            "assay_description": row.get("assayDescription") or "",
            "readout_class": readout,
            "primary_references": refs,
            "qualifies_automatically": readout == "functional" and bool(refs),
        })
    functional = [row for row in evidence_rows if row["qualifies_automatically"]]
    has_primary = any(row["primary_references"] for row in evidence_rows)
    nonempty_readouts = [row["readout_class"] for row in evidence_rows if row["assay_description"]]
    if len(classes) != 1:
        decision = "quarantine_action_conflict_or_unclassified"
    elif functional:
        decision = "provisional_functional_support_pending_dual_review"
    elif nonempty_readouts and all(value == "binding_only" for value in nonempty_readouts):
        decision = "reject_database_description_binding_only"
    elif has_primary:
        decision = "needs_primary_paper_review"
    else:
        decision = "needs_traceable_primary_source"
    return {
        "record_id": candidate["record_id"],
        "molecule_name": candidate["molecule_name"],
        "source_id": candidate["source_id"],
        "proposed_functional_class": classes[0] if len(classes) == 1 else None,
        "provisional_binary_label": (
            1 if classes == ["agonist"] else 0 if classes == ["antagonist"] else None
        ),
        "evidence_decision": decision,
        "dataset_admission_eligible": False,
        "training_eligible": False,
        "human_validation_status": "pending_dual_review",
        "evidence_rows": evidence_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sealed_interaction_snapshot", type=Path)
    parser.add_argument("--sealed-output", type=Path, required=True)
    args = parser.parse_args()
    acquisition = json.loads(ACQUISITION_AUDIT.read_text(encoding="utf-8"))
    if sha256(args.sealed_interaction_snapshot) != acquisition["sealed_interaction_snapshot_sha256"]:
        raise RuntimeError("Sealed GtoPdb interaction snapshot hash does not match acquisition audit")
    interactions = json.loads(args.sealed_interaction_snapshot.read_text(encoding="utf-8"))
    with ELIGIBLE.open(newline="", encoding="utf-8") as handle:
        candidates = list(csv.DictReader(handle))
    by_ligand = defaultdict(list)
    for row in interactions:
        if row.get("targetId") == 19 and row.get("targetSpecies") == "Human":
            by_ligand[str(row["ligandId"])].append(row)
    missing = sorted(candidate["source_id"] for candidate in candidates if candidate["source_id"] not in by_ligand)
    if missing:
        raise RuntimeError(f"Eligible candidates lack sealed interaction records: {missing}")
    decisions = [adjudicate_candidate(candidate, by_ligand[candidate["source_id"]]) for candidate in candidates]

    args.sealed_output.parent.mkdir(parents=True, exist_ok=True)
    sealed_payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-gtopdb-evidence-review-v1.4",
        "access_control": "evidence_only_do_not_load_for_modeling_or_candidate_selection",
        "human_validation_claimed": False,
        "record_count": len(decisions),
        "records": decisions,
    }
    args.sealed_output.write_text(json.dumps(sealed_payload, indent=2) + "\n", encoding="utf-8")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    queue_path = OUTPUT_DIR / "primary_paper_review_queue_label_free.csv"
    queue_fields = [
        "record_id", "molecule_name", "source_id", "source_url", "database_readout_status",
        "primary_reference_count", "primary_pmids", "evidence_review_status",
    ]
    with queue_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=queue_fields, lineterminator="\n")
        writer.writeheader()
        for candidate, decision in zip(candidates, decisions):
            evidence_rows = decision["evidence_rows"]
            pmids = sorted({
                ref["pmid"] for row in evidence_rows for ref in row["primary_references"] if ref["pmid"]
            })
            readouts = sorted({row["readout_class"] for row in evidence_rows})
            writer.writerow({
                "record_id": candidate["record_id"],
                "molecule_name": candidate["molecule_name"],
                "source_id": candidate["source_id"],
                "source_url": candidate["source_url"],
                "database_readout_status": ";".join(readouts),
                "primary_reference_count": len(pmids),
                "primary_pmids": ";".join(pmids),
                "evidence_review_status": decision["evidence_decision"],
            })

    audit_path = OUTPUT_DIR / "evidence_gate_audit.json"
    decision_counts = Counter(row["evidence_decision"] for row in decisions)
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-gtopdb-evidence-review-v1.4",
        "source_hashes": {
            "sealed_interaction_snapshot": sha256(args.sealed_interaction_snapshot),
            "eligible_candidates": sha256(ELIGIBLE),
            "evidence_runner": sha256(Path(__file__)),
            "sealed_evidence_packet": sha256(args.sealed_output),
            "label_free_review_queue": sha256(queue_path),
        },
        "candidate_count": len(candidates),
        "decision_counts": dict(sorted(decision_counts.items())),
        "automatically_evidence_admitted_count": 0,
        "labels_written_to_repository": False,
        "model_or_docking_artifacts_accessed": False,
        "human_validation_claimed": False,
        "next_gate": "retrieve and review the cited primary papers; database action annotations alone cannot admit labels",
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
