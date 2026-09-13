#!/usr/bin/env python3

"""Build a label-blind BindingDB pBind_Ki intake while sealing all outcomes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from standardize_quarantine import standardize_smiles


ROOT = Path(__file__).resolve().parent
DEFAULT_SEALED = ROOT.parent.parent / "sealed_external_labels" / "v1.5_bindingdb_p29274_20260913"
DEFAULT_RAW = DEFAULT_SEALED / "raw_response.json"
OUTPUT = ROOT / "outputs" / "v1.5" / "external_pbind_intake"
PRIOR_POOL = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
MODEL_SELECTION = ROOT / "outputs" / "v1.3" / "docking_clean_computational.csv"
FIELDS = [
    "candidate_id", "bindingdb_monomer_id", "standardized_smiles",
    "standardized_inchikey", "generic_murcko_scaffold_smiles", "doi", "pmid",
    "sealed_exact_ki_measurement_count", "prior_exact_structure_overlap",
    "model_selection_generic_scaffold_overlap", "primary_evidence_review_status",
    "intake_status", "quarantine_reasons",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def exact_numeric_affinity(value: object) -> bool:
    return bool(re.fullmatch(r"\s*=?\s*[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\s*", str(value or "")))


def primary_doi(value: object) -> str:
    doi = str(value or "").strip()
    return "" if not doi or doi.lower().startswith("10.7270/") else doi


def prior_structure_keys() -> set[str]:
    payload = json.loads(PRIOR_POOL.read_text(encoding="utf-8"))
    keys = set()
    for row in payload["records"]:
        value = row.get("standardized_inchikey") or row.get("inchikey")
        if value:
            keys.add(value)
    return keys


def model_selection_keys() -> tuple[set[str], set[str]]:
    rows = read_csv(MODEL_SELECTION)
    exact = {row["standardized_inchikey"] for row in rows if row.get("standardized_inchikey")}
    scaffolds = {row["generic_murcko_scaffold_smiles"] for row in rows
                 if row.get("generic_murcko_scaffold_smiles")}
    return exact, scaffolds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--sealed-output", type=Path, default=DEFAULT_SEALED / "eligible_exact_ki_outcomes.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    payload = json.loads(args.raw.read_text(encoding="utf-8"))
    records = payload["getLindsByUniprotsResponse"]["affinities"]
    ki_records = [row for row in records if row.get("affinity_type") == "Ki"]
    exact_ki = [row for row in ki_records if exact_numeric_affinity(row.get("affinity"))]
    grouped: dict[str, list[dict]] = defaultdict(list)
    invalid_smiles = 0
    chemistry_by_monomer = {}
    for row in exact_ki:
        monomer = str(row.get("monomerid") or "").strip()
        smiles = str(row.get("smile") or "").strip()
        if not monomer or not smiles:
            invalid_smiles += 1
            continue
        if monomer not in chemistry_by_monomer:
            try:
                chemistry_by_monomer[monomer] = standardize_smiles(smiles)
            except Exception:  # structure remains quarantined without exposing an outcome
                invalid_smiles += 1
                continue
        grouped[monomer].append(row)

    prior_exact = prior_structure_keys()
    model_exact, model_scaffolds = model_selection_keys()
    public_rows = []
    sealed_rows = []
    for monomer, rows in sorted(grouped.items()):
        chemistry = chemistry_by_monomer[monomer]
        inchikey = chemistry["standardized_inchikey"]
        scaffold = chemistry["generic_murcko_scaffold_smiles"]
        dois = sorted({primary_doi(row.get("doi")) for row in rows if primary_doi(row.get("doi"))})
        pmids = sorted({str(row.get("pmid") or "").strip() for row in rows if row.get("pmid")})
        reasons = []
        if inchikey in prior_exact or inchikey in model_exact:
            reasons.append("exact_structure_previously_visible")
        if scaffold and scaffold in model_scaffolds:
            reasons.append("generic_scaffold_overlaps_model_selection")
        if not dois and not pmids:
            reasons.append("primary_publication_identifier_missing")
        status = "eligible_for_primary_evidence_review" if not reasons else "quarantined_before_evidence_review"
        candidate_id = f"BDB-{monomer}"
        public_rows.append({
            "candidate_id": candidate_id,
            "bindingdb_monomer_id": monomer,
            "standardized_smiles": chemistry["standardized_smiles"],
            "standardized_inchikey": inchikey,
            "generic_murcko_scaffold_smiles": scaffold,
            "doi": "|".join(dois),
            "pmid": "|".join(pmids),
            "sealed_exact_ki_measurement_count": len(rows),
            "prior_exact_structure_overlap": inchikey in prior_exact or inchikey in model_exact,
            "model_selection_generic_scaffold_overlap": bool(scaffold and scaffold in model_scaffolds),
            "primary_evidence_review_status": "pending_dual_review",
            "intake_status": status,
            "quarantine_reasons": "|".join(reasons),
        })
        if not reasons:
            for index, row in enumerate(rows, 1):
                sealed_rows.append({
                    "candidate_id": candidate_id,
                    "sealed_measurement_id": f"{candidate_id}-KI-{index:03d}",
                    "affinity_type": "Ki",
                    "affinity_verbatim": row["affinity"],
                    "bindingdb_monomer_id": monomer,
                    "doi": str(row.get("doi") or ""),
                    "pmid": str(row.get("pmid") or ""),
                    "unmask_status": "sealed_do_not_read_before_membership_and_analysis_freeze",
                })

    args.output.mkdir(parents=True, exist_ok=True)
    eligible = [row for row in public_rows if row["intake_status"] == "eligible_for_primary_evidence_review"]
    quarantined = [row for row in public_rows if row["intake_status"] != "eligible_for_primary_evidence_review"]
    eligible_path = args.output / "eligible_for_primary_review.csv"
    quarantine_path = args.output / "quarantined_before_primary_review.csv"
    audit_path = args.output / "intake_audit.json"
    write_csv(eligible_path, eligible, FIELDS)
    write_csv(quarantine_path, quarantined, FIELDS)
    write_csv(args.sealed_output, sealed_rows, [
        "candidate_id", "sealed_measurement_id", "affinity_type", "affinity_verbatim",
        "bindingdb_monomer_id", "doi", "pmid", "unmask_status",
    ])
    reason_counts = Counter(reason for row in quarantined for reason in row["quarantine_reasons"].split("|") if reason)
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "BindingDB getLigandsByUniprots P29274 API",
        "source_url": "https://bindingdb.org/rest/getLigandsByUniprots?uniprot=P29274&cutoff=1000000000&response=application/json",
        "outcomes_exposed_to_public_workspace": False,
        "outcomes_unmasked": False,
        "membership_frozen": False,
        "source_record_count": len(records),
        "ki_record_count": len(ki_records),
        "exact_relation_ki_record_count": len(exact_ki),
        "invalid_or_missing_structure_record_count": invalid_smiles,
        "unique_standardized_structure_count": len(public_rows),
        "eligible_for_primary_evidence_review_count": len(eligible),
        "eligible_generic_scaffold_count": len({row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in eligible}),
        "quarantined_structure_count": len(quarantined),
        "quarantine_reason_counts": dict(sorted(reason_counts.items())),
        "protocol_floors": {"molecules": 60, "generic_scaffolds": 20},
        "floor_status_before_primary_review": {
            "molecules": len(eligible) >= 60,
            "generic_scaffolds": len({row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in eligible}) >= 20,
        },
        "source_hashes": {
            "sealed_raw_response": sha256(args.raw),
            "prior_visibility_pool": sha256(PRIOR_POOL),
            "model_selection_features": sha256(MODEL_SELECTION),
            "public_eligible_intake": sha256(eligible_path),
            "public_quarantine": sha256(quarantine_path),
            "sealed_outcome_file": sha256(args.sealed_output),
        },
        "next_gate": "Dual primary-publication review and assay-context verification; do not freeze membership or unmask outcomes yet.",
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
