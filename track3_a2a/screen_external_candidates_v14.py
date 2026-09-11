#!/usr/bin/env python3

"""Screen a label-free v1.4 candidate snapshot against independence rules."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.standardize_quarantine import standardize_smiles


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "external_validation.v1.4.json"
HISTORICAL = ROOT / "data" / "curated" / "chembl251_computational_partitions_v1.3.json"
PREFREEZE_REVIEW = ROOT / "data" / "curated" / "chembl251_functional_review_packet.json"
PREFREEZE_STRUCTURES = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
LABEL_FIELDS = {
    "functional_class", "primary_binary_label", "label", "proposed_class",
    "evidence_rationale", "assay_readout",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def parse_false(value: str) -> bool:
    return value.strip().lower() in {"false", "0", "no"}


def historical_indexes(records: list[dict]) -> tuple[set[str], set[str], set[str]]:
    inchikeys = {row["standardized_inchikey"] for row in records}
    structures = {row["standardized_smiles"] for row in records}
    scaffolds = {row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in records}
    return inchikeys, structures, scaffolds


def screen_rows(
    rows: list[dict], historical_records: list[dict], prefreeze_ids: set[str], cutoff: datetime,
    prefreeze_inchikeys: set[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    historical_inchikeys, historical_structures, historical_scaffolds = historical_indexes(historical_records)
    accepted, quarantined = [], []
    seen_record_ids, seen_external_inchikeys = set(), set()
    for source in rows:
        row = dict(source)
        reasons = []
        record_id = row.get("record_id", "").strip()
        if not record_id:
            reasons.append("missing_record_id")
        elif record_id in seen_record_ids:
            reasons.append("duplicate_record_id_in_snapshot")
        seen_record_ids.add(record_id)

        leaked = sorted(field for field in LABEL_FIELDS if row.get(field, "").strip())
        if leaked:
            reasons.append("label_fields_present:" + ",".join(leaked))

        required = ["canonical_smiles", "source_id", "source_url", "source_snapshot_id", "source_retrieved_at", "prior_project_visibility"]
        reasons.extend(f"missing_{field}" for field in required if not row.get(field, "").strip())

        retrieved_at = None
        if row.get("source_retrieved_at", "").strip():
            try:
                retrieved_at = parse_timestamp(row["source_retrieved_at"])
                if retrieved_at <= cutoff:
                    reasons.append("source_snapshot_not_after_historical_cutoff")
            except ValueError:
                reasons.append("invalid_source_retrieved_at")
        if row.get("prior_project_visibility", "").strip() and not parse_false(row["prior_project_visibility"]):
            reasons.append("prior_project_visibility_not_false")

        external_identifier = row.get("external_identifier", "").strip()
        if external_identifier and external_identifier in prefreeze_ids:
            reasons.append("identifier_present_in_prefreeze_review_pool")

        chemistry = None
        if row.get("canonical_smiles", "").strip():
            try:
                chemistry = standardize_smiles(row["canonical_smiles"])
            except Exception as exc:  # noqa: BLE001
                reasons.append(f"invalid_structure:{exc}")
        if chemistry:
            scaffold = chemistry["generic_murcko_scaffold_smiles"] or "ACYCLIC"
            if chemistry["standardized_inchikey"] in (prefreeze_inchikeys or set()):
                reasons.append("structure_present_in_prefreeze_source_pool")
            if chemistry["standardized_inchikey"] in historical_inchikeys:
                reasons.append("historical_inchikey_overlap")
            if chemistry["standardized_smiles"] in historical_structures:
                reasons.append("historical_standardized_structure_overlap")
            if scaffold in historical_scaffolds:
                reasons.append("historical_generic_murcko_scaffold_overlap")
            if chemistry["standardized_inchikey"] in seen_external_inchikeys:
                reasons.append("duplicate_standardized_structure_in_snapshot")
            seen_external_inchikeys.add(chemistry["standardized_inchikey"])
            row.update({
                "standardized_smiles": chemistry["standardized_smiles"],
                "standardized_inchikey": chemistry["standardized_inchikey"],
                "murcko_scaffold_smiles": chemistry["murcko_scaffold_smiles"],
                "generic_murcko_scaffold_smiles": chemistry["generic_murcko_scaffold_smiles"],
            })
        row["historical_independence_eligible"] = not reasons
        row["screening_reasons"] = ";".join(reasons)
        (accepted if not reasons else quarantined).append(row)
    return accepted, quarantined


def write_csv(path: Path, rows: list[dict], fallback_fields: list[str]) -> None:
    fields = list(rows[0]) if rows else fallback_fields
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_snapshot", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "v1.4" / "external_cohort")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    historical_payload = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    prefreeze_payload = json.loads(PREFREEZE_REVIEW.read_text(encoding="utf-8"))
    prefreeze_structures_payload = json.loads(PREFREEZE_STRUCTURES.read_text(encoding="utf-8"))
    with args.candidate_snapshot.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        source_fields = reader.fieldnames or []
        candidates = list(reader)
    cutoff = parse_timestamp(config["external_cohort"]["source_freeze"]["historical_visibility_cutoff_utc"])
    prefreeze_ids = {row["chembl_id"] for row in prefreeze_payload["records"]}
    prefreeze_inchikeys = {
        row["standardized_inchikey"] for row in prefreeze_structures_payload["records"]
    }
    accepted, quarantined = screen_rows(
        candidates, historical_payload["records"], prefreeze_ids, cutoff, prefreeze_inchikeys
    )
    accepted_path = args.output_dir / "eligible_candidates.csv"
    quarantine_path = args.output_dir / "quarantined_candidates.csv"
    report_path = args.output_dir / "screening_audit.json"
    generated_fields = [
        "standardized_smiles", "standardized_inchikey", "murcko_scaffold_smiles",
        "generic_murcko_scaffold_smiles", "historical_independence_eligible", "screening_reasons",
    ]
    fields = source_fields + [field for field in generated_fields if field not in source_fields]
    write_csv(accepted_path, accepted, fields)
    write_csv(quarantine_path, quarantined, fields)
    reason_counts = Counter(reason for row in quarantined for reason in row["screening_reasons"].split(";") if reason)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"],
        "candidate_snapshot": str(args.candidate_snapshot),
        "source_hashes": {
            "candidate_snapshot": sha256(args.candidate_snapshot),
            "external_protocol": sha256(CONFIG),
            "historical_partitions": sha256(HISTORICAL),
            "prefreeze_review_packet": sha256(PREFREEZE_REVIEW),
            "prefreeze_structure_pool": sha256(PREFREEZE_STRUCTURES),
            "screening_runner": sha256(Path(__file__)),
        },
        "input_count": len(candidates),
        "eligible_count": len(accepted),
        "quarantined_count": len(quarantined),
        "quarantine_reason_counts": dict(sorted(reason_counts.items())),
        "labels_loaded": False,
        "external_cohort_frozen": False,
        "next_gate": "independent evidence review, final power-target completion, candidate snapshot freeze, then docking with labels still masked",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
