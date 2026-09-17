#!/usr/bin/env python3
"""Run the outcome-blind, source-grounded pass-2 external evidence gate.

The extractor intentionally records categorical evidence only.  It never reads the
sealed BindingDB outcome columns and never extracts or stores numeric Ki values.
Candidate identity is accepted only when the retrieved primary source contains a
machine-verifiable structure identifier that matches the frozen queue record.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PASS1 = ROOT / "outputs" / "v1.6" / "external_evidence" / "pass1_metadata_preflight" / "pass1_metadata_preflight.json"
PMC = ROOT / "outputs" / "v1.6" / "external_evidence" / "pmc_fulltext_evidence.json"
OUTPUT = ROOT / "outputs" / "v1.6" / "external_evidence" / "pass2_source_extraction"

MINIMUM_MOLECULES = 60
MINIMUM_SCAFFOLDS = 20
AGREEMENT_FIELDS = [
    "molecule_identity", "stereochemistry", "target_species", "wild_type_status",
    "assay_type", "endpoint", "relation", "units", "primary_source_locator",
]

# This lexicon is intentionally independent from pass 1.  It resolves only
# categorical assay context and never captures a measurement value.
FIELD_PATTERNS = {
    "target_species": re.compile(
        r"(?:human.{0,100}(?:adenosine\s+)?A\s*\(?2\s*A\)?(?:\s+receptor)?|"
        r"(?:adenosine\s+)?A\s*\(?2\s*A\)?(?:\s+receptor)?.{0,100}human)", re.I | re.S
    ),
    "wild_type_status": re.compile(r"\bwild[ -]?type\b|\bWT\b", re.I),
    "assay_type": re.compile(
        r"radioligand\s+(?:binding|displacement)|competitive\s+binding|"
        r"binding\s+(?:assay|affinit)|displacement\s+(?:assay|of)", re.I
    ),
    "endpoint": re.compile(r"\bK\s*[_-]?i\b|inhibition\s+constant", re.I),
    # A table/header declaring Ki in a unit is categorical support for an exact
    # Ki field.  Censored relations are not parsed or admitted.
    "relation": re.compile(r"\bK\s*[_-]?i\s*(?:\([^)]*\)|\[[^]]*\])", re.I),
    "units": re.compile(r"\bK\s*[_-]?i\s*(?:\(|\[)\s*(?:pM|nM|uM|µM|μM)\s*(?:\)|\])", re.I),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_locator(document: dict) -> dict:
    return {
        "pmcid": document["pmcid"],
        "source_url": document["source_url"],
        "raw_xml_sha256": document["raw_xml_sha256"],
        "body_text_sha256": text_sha256(document["body_text"]),
    }


def categorical_source_fields(record: dict, document: dict) -> dict[str, dict]:
    """Extract categorical fields without extracting measurement values."""
    body = document["body_text"]
    fields: dict[str, dict] = {}
    for name, pattern in FIELD_PATTERNS.items():
        match = pattern.search(body)
        fields[name] = {
            "resolved": bool(match),
            "value": {
                "target_species": "Homo sapiens",
                "wild_type_status": "wild_type",
                "assay_type": "direct_binding",
                "endpoint": "Ki",
                "relation": "=",
                "units": "molar_convertible",
            }[name] if match else None,
            "source_locator": source_locator(document) if match else None,
        }

    # Exact molecule linkage must be independently visible in the source.  A
    # paper-level assay description alone cannot map a queued structure to a row.
    identity_tokens = [record["standardized_inchikey"], record["standardized_smiles"]]
    matched_token = next((token for token in identity_tokens if token and token in body), None)
    if not matched_token:
        bindingdb_id = re.search(
            rf"\bBindingDB(?:\s+MonomerID)?\s*[:#]?\s*{re.escape(record['bindingdb_monomer_id'])}\b",
            body,
            re.I,
        )
        matched_token = bindingdb_id.group(0) if bindingdb_id else None
    fields["molecule_identity"] = {
        "resolved": matched_token is not None,
        "value": record["standardized_inchikey"] if matched_token else None,
        "match_type": "source_structure_identifier" if matched_token else None,
        "source_locator": source_locator(document) if matched_token else None,
    }
    has_defined_stereo = "@" in record["standardized_smiles"]
    fields["stereochemistry"] = {
        "resolved": matched_token is not None,
        "value": "defined_as_queued" if matched_token and has_defined_stereo else (
            "no_tetrahedral_stereochemistry_in_queued_parent" if matched_token else None
        ),
        "source_locator": source_locator(document) if matched_token else None,
    }
    fields["primary_source_locator"] = {
        "resolved": True,
        "value": document["pmcid"],
        "source_locator": source_locator(document),
    }
    return fields


def assess_record(record: dict, documents: dict[str, dict]) -> dict:
    pass1_status = record["pass_1_status"]
    pmcids = [value for value in record.get("pmcids", "").split("|") if value]
    sources = []
    for pmcid in pmcids:
        document = documents.get(pmcid)
        if document:
            sources.append({
                "primary_source_locator": pmcid,
                "categorical_fields": categorical_source_fields(record, document),
            })

    accepted_source = next(
        (source for source in sources if all(source["categorical_fields"][name]["resolved"] for name in AGREEMENT_FIELDS)),
        None,
    )
    pass1_fields = record.get("pass_1_extracted_fields", {})
    exact_agreement = bool(accepted_source) and all(
        name in pass1_fields
        and pass1_fields[name] == accepted_source["categorical_fields"][name]["value"]
        for name in AGREEMENT_FIELDS
    )
    reasons = []
    if not pass1_status.startswith("metadata_pass"):
        reasons.append("pass_1_rejected")
    if not sources:
        reasons.append("retrieved_primary_full_text_unavailable")
    elif accepted_source is None:
        unresolved = sorted({
            name for source in sources for name in AGREEMENT_FIELDS
            if not source["categorical_fields"][name]["resolved"]
        })
        reasons.extend(f"unresolved_{name}" for name in unresolved)
    elif not pass1_fields:
        reasons.append("pass_1_agreement_fields_unavailable")
    elif not exact_agreement:
        reasons.append("pass_1_pass_2_field_disagreement")

    pass2_accept = accepted_source is not None
    final_admit = pass1_status.startswith("metadata_pass") and pass2_accept and exact_agreement
    return {
        "queue_rank": record["queue_rank"],
        "candidate_id": record["candidate_id"],
        "bindingdb_monomer_id": record["bindingdb_monomer_id"],
        "standardized_smiles": record["standardized_smiles"],
        "standardized_inchikey": record["standardized_inchikey"],
        "generic_murcko_scaffold_smiles": record["generic_murcko_scaffold_smiles"],
        "pass_1_status": pass1_status,
        "pass_2_status": "accept" if pass2_accept else "quarantine",
        "pass_1_pass_2_exact_agreement": exact_agreement,
        "final_membership_decision": "admit" if final_admit else "quarantine",
        "quarantine_reasons": reasons,
        "source_assessments": sources,
        "agreement_fields": AGREEMENT_FIELDS,
        "numeric_ki_extracted": False,
        "outcome_fields_loaded": False,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "queue_rank", "candidate_id", "bindingdb_monomer_id", "standardized_smiles",
        "standardized_inchikey", "generic_murcko_scaffold_smiles", "pass_1_status",
        "pass_2_status", "final_membership_decision", "quarantine_reasons",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            projected = {name: row.get(name, "") for name in fields}
            projected["quarantine_reasons"] = "|".join(row["quarantine_reasons"])
            writer.writerow(projected)


def main() -> None:
    pass1 = json.loads(PASS1.read_text(encoding="utf-8"))
    pmc = json.loads(PMC.read_text(encoding="utf-8"))
    if pass1.get("outcome_fields_loaded") or pmc.get("external_outcomes_loaded"):
        raise RuntimeError("outcome firewall violation in evidence inputs")
    documents = {row["pmcid"]: row for row in pmc["documents"]}
    assessments = [assess_record(row, documents) for row in pass1["records"]]
    assessments.sort(key=lambda row: int(row["queue_rank"]))
    admitted = [row for row in assessments if row["final_membership_decision"] == "admit"]
    quarantined = [row for row in assessments if row["final_membership_decision"] == "quarantine"]
    scaffold_count = len({row["generic_murcko_scaffold_smiles"] for row in admitted})
    floors_passed = len(admitted) >= MINIMUM_MOLECULES and scaffold_count >= MINIMUM_SCAFFOLDS

    OUTPUT.mkdir(parents=True, exist_ok=True)
    packet_path = OUTPUT / "pass2_source_extraction.json"
    packet = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-external-computational-evidence-pass2-v1.6",
        "access_control": "label_blind_categorical_evidence_only",
        "numeric_ki_extracted": False,
        "outcome_fields_loaded": False,
        "records": assessments,
    }
    packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")

    admitted_path = OUTPUT / "admitted_external_cohort.csv"
    quarantine_path = OUTPUT / "quarantined_external_cohort.csv"
    write_csv(admitted_path, admitted)
    write_csv(quarantine_path, quarantined)

    reason_counts = Counter(reason for row in quarantined for reason in row["quarantine_reasons"])
    manifest_path = OUTPUT / "cohort_freeze_manifest.json"
    manifest = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-external-cohort-membership-freeze-v1.6",
        "status": "frozen_nonconfirmatory_floor_failure" if not floors_passed else "frozen_confirmatory_cohort",
        "membership_frozen": True,
        "membership_selected_without_outcomes": True,
        "numeric_ki_extracted": False,
        "external_outcomes_joined": False,
        "one_time_outcome_join_authorized": floors_passed,
        "candidate_count": len(assessments),
        "source_grounded_candidate_count": sum(bool(row["source_assessments"]) for row in assessments),
        "pass_1_eligible_source_grounded_candidate_count": sum(
            bool(row["source_assessments"]) and row["pass_1_status"].startswith("metadata_pass")
            for row in assessments
        ),
        "admitted_molecule_count": len(admitted),
        "admitted_generic_murcko_scaffold_count": scaffold_count,
        "minimum_molecule_floor": MINIMUM_MOLECULES,
        "minimum_generic_murcko_scaffold_floor": MINIMUM_SCAFFOLDS,
        "minimum_floors_passed": floors_passed,
        "quarantine_reason_counts": dict(sorted(reason_counts.items())),
        "source_hashes": {"pass1_packet": sha256(PASS1), "pmc_fulltext_evidence": sha256(PMC)},
        "artifact_hashes": {
            "pass2_packet": sha256(packet_path),
            "admitted_external_cohort": sha256(admitted_path),
            "quarantined_external_cohort": sha256(quarantine_path),
        },
        "decision": (
            "The frozen floors passed; the separately controlled outcome join may proceed."
            if floors_passed else
            "The frozen 60-molecule/20-scaffold floors were not met. This is a non-confirmatory "
            "stress-test freeze; the one-time outcome join remains prohibited."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    audit_path = OUTPUT / "pass2_source_extraction_audit.json"
    audit = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-external-computational-evidence-pass2-v1.6",
        "candidate_count": len(assessments),
        "source_grounded_candidate_count": manifest["source_grounded_candidate_count"],
        "pass_1_eligible_source_grounded_candidate_count": manifest["pass_1_eligible_source_grounded_candidate_count"],
        "admitted_count": len(admitted),
        "quarantined_count": len(quarantined),
        "pass_2_status_counts": dict(sorted(Counter(row["pass_2_status"] for row in assessments).items())),
        "quarantine_reason_counts": dict(sorted(reason_counts.items())),
        "numeric_ki_extracted": False,
        "outcome_fields_loaded": False,
        "membership_frozen": True,
        "minimum_floors_passed": floors_passed,
        "one_time_outcome_join_authorized": floors_passed,
        "cohort_freeze_manifest_sha256": sha256(manifest_path),
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
