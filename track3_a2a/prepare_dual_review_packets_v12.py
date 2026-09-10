#!/usr/bin/env python3

"""Create independent blinded evidence-review packets for named reviewers."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "curated" / "chembl251_curation_plan_220_v1.2.csv"
OUTPUT = ROOT / "outputs" / "v1.2" / "formal_review"
REVIEWERS = ("Tharran", "Lucky")
FIELDS = [
    "chembl_id", "molecule_name", "standardized_smiles", "standardized_inchikey",
    "functional_activity_rows", "unique_assays", "unique_documents",
    "representative_assay", "representative_document", "representative_readout",
    "representative_description", "reviewer", "decision", "evidence_tier",
    "source_checked", "review_notes", "reviewed_at_utc",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    packet_hashes = {}
    for reviewer in REVIEWERS:
        path = OUTPUT / f"{reviewer.lower()}_blinded_review.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    **{field: row.get(field, "") for field in FIELDS},
                    "reviewer": reviewer,
                    "decision": "",
                    "evidence_tier": "",
                    "source_checked": "",
                    "review_notes": "",
                    "reviewed_at_utc": "",
                })
        packet_hashes[reviewer] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "record_count_per_reviewer": len(rows),
        "reviewers": list(REVIEWERS),
        "blinding": "proposed class, other reviewer decision, and model outputs omitted",
        "allowed_decisions": [
            "accept_agonist", "accept_antagonist", "reject_binding_only",
            "reject_context", "reject_conflict", "needs_full_text",
        ],
        "allowed_evidence_tiers_for_accepted_records": ["tier_1", "tier_2"],
        "attestation": "Each named reviewer must personally check the cited source and enter their own decision, tier, notes, and review time.",
        "packets": packet_hashes,
        "formal_review_complete": False,
    }
    path = OUTPUT / "review_packet_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
