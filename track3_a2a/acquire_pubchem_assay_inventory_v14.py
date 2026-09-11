#!/usr/bin/env python3

"""Acquire a sealed PubChem human ADORA2A assay-summary inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "v1.4" / "external_sources" / "pubchem"
AID_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P29274/aids/TXT"
SUMMARY_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/{aids}/summary/JSON"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request_bytes(url: str, attempts: int = 4) -> bytes:
    error = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ECMO-Track3-v1.4/1.0"})
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001
            error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"PubChem request failed after {attempts} attempts: {url}: {error}")


def parse_summary_payload(payload: dict) -> list[dict]:
    return payload.get("AssaySummaries", {}).get("AssaySummary", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sealed-output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()
    aids = sorted({int(value) for value in request_bytes(AID_URL).decode("utf-8").split()})
    summaries = []
    for start in range(0, len(aids), args.batch_size):
        batch = aids[start:start + args.batch_size]
        url = SUMMARY_URL.format(aids=",".join(str(value) for value in batch))
        payload = json.loads(request_bytes(url).decode("utf-8"))
        summaries.extend(parse_summary_payload(payload))
        time.sleep(0.25)
    by_aid = {int(row["AID"]): row for row in summaries}
    missing = sorted(set(aids) - set(by_aid))
    args.sealed_output.parent.mkdir(parents=True, exist_ok=True)
    sealed = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "NCBI PubChem PUG REST",
        "target_accession": "P29274",
        "access_control": "evidence_only_do_not_load_for_modeling_or_candidate_selection",
        "requested_aids": aids,
        "missing_aids": missing,
        "assay_summaries": [by_aid[key] for key in sorted(by_aid)],
    }
    args.sealed_output.write_text(json.dumps(sealed, indent=2) + "\n", encoding="utf-8")
    sources = Counter(row.get("SourceName") or "missing" for row in summaries)
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "NCBI PubChem PUG REST",
        "official_documentation": "https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest-tutorial",
        "target_accession": "P29274",
        "requested_aid_count": len(aids),
        "retrieved_assay_summary_count": len(by_aid),
        "missing_aid_count": len(missing),
        "source_name_counts": dict(sorted(sources.items())),
        "sealed_inventory_sha256": sha256(args.sealed_output),
        "labels_or_activity_rows_written_to_repository": False,
        "next_gate": "exclude ChEMBL mirrors and binding-only or non-A2A assays, then retrieve candidate structures from qualifying independent functional assays",
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit_path = OUTPUT_DIR / "assay_inventory_acquisition_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
