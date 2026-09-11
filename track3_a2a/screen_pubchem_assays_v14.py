#!/usr/bin/env python3

"""Screen the sealed PubChem P29274 assay inventory for external evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.build_evidence_review_queue import classify_readout


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "v1.4" / "external_sources" / "pubchem"
DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
PMID_PATTERN = re.compile(r"\bPMID\s*[:=]\s*(\d+)\b", re.IGNORECASE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assay_text(row: dict) -> str:
    values = [row.get("Name") or ""]
    for field in ("Description", "Protocol", "Comment"):
        value = row.get(field) or []
        values.extend(value if isinstance(value, list) else [str(value)])
    return "\n".join(values)


def direct_human_a2a_target(row: dict) -> bool:
    targets = row.get("Target") or []
    return len(targets) == 1 and targets[0].get("Accession") == "P29274"


def action_direction(row: dict) -> str | None:
    name = (row.get("Name") or "").lower()
    if "antagonist" in name or ("a2a" in name and "inhibitor" in name):
        return "antagonist"
    if "agonist" in name:
        return "agonist"
    return None


def publication_identifiers(text: str) -> dict:
    return {
        "dois": sorted(set(match.rstrip(".,;)") for match in DOI_PATTERN.findall(text))),
        "pmids": sorted(set(PMID_PATTERN.findall(text))),
    }


def screen_assay(row: dict) -> dict:
    text = assay_text(row)
    source_independent = row.get("SourceName") != "ChEMBL"
    direct_target = direct_human_a2a_target(row)
    readout = classify_readout(text)
    direction = action_direction(row)
    publications = publication_identifiers(text)
    traceable_primary = bool(publications["dois"] or publications["pmids"])
    patent_derived = "patent" in text.lower()
    reasons = []
    if not source_independent:
        reasons.append("chembl_mirror")
    if not direct_target:
        reasons.append("not_single_direct_p29274_target")
    if readout != "functional":
        reasons.append(f"readout_{readout}")
    if direction is None:
        reasons.append("no_explicit_binary_action_direction")
    if not traceable_primary:
        reasons.append("no_primary_publication_doi_or_pmid")
    if patent_derived and not traceable_primary:
        reasons.append("patent_only_evidence")
    eligible = not reasons
    return {
        "aid": int(row["AID"]),
        "source_name": row.get("SourceName"),
        "source_id": row.get("SourceID"),
        "name": row.get("Name"),
        "source_independent": source_independent,
        "direct_human_a2a_target": direct_target,
        "readout_class": readout,
        "proposed_functional_class": direction,
        "publication_identifiers": publications,
        "patent_derived": patent_derived,
        "evidence_eligible": eligible,
        "screening_reasons": reasons,
        "candidate_count": row.get("CIDCountAll"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sealed_inventory", type=Path)
    parser.add_argument("--sealed-output", type=Path, required=True)
    args = parser.parse_args()
    inventory = json.loads(args.sealed_inventory.read_text(encoding="utf-8"))
    decisions = [screen_assay(row) for row in inventory["assay_summaries"]]
    args.sealed_output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-pubchem-assay-screen-v1.4",
        "access_control": "evidence_only_do_not_load_for_modeling_or_candidate_selection",
        "assay_count": len(decisions),
        "records": decisions,
    }
    args.sealed_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    independent = [row for row in decisions if row["source_independent"]]
    direct = [row for row in independent if row["direct_human_a2a_target"]]
    functional = [row for row in direct if row["readout_class"] == "functional"]
    directed = [row for row in functional if row["proposed_functional_class"]]
    eligible = [row for row in directed if row["evidence_eligible"]]
    reason_counts = Counter(reason for row in independent for reason in row["screening_reasons"])
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-pubchem-assay-screen-v1.4",
        "source_hashes": {
            "sealed_inventory": sha256(args.sealed_inventory),
            "screening_runner": sha256(Path(__file__)),
            "sealed_screening_packet": sha256(args.sealed_output),
        },
        "total_assay_count": len(decisions),
        "chembl_mirror_count": len(decisions) - len(independent),
        "independent_source_assay_count": len(independent),
        "single_direct_p29274_assay_count": len(direct),
        "functional_readout_assay_count": len(functional),
        "explicit_binary_direction_assay_count": len(directed),
        "primary_publication_eligible_assay_count": len(eligible),
        "evidence_eligible_assay_count": len(eligible),
        "independent_source_exclusion_reason_counts": dict(sorted(reason_counts.items())),
        "labels_or_activity_rows_written_to_repository": False,
        "next_gate": "do not use patent-only or ChEMBL-mirrored PubChem assays as external labels; continue to another independent primary-publication source",
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit_path = OUTPUT_DIR / "assay_inventory_screening_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
