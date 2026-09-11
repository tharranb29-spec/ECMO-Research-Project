#!/usr/bin/env python3

"""Retrieve available PMC full text for the sealed v1.4 evidence review."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "v1.4" / "evidence_review" / "gtopdb_2026.2"
FULLTEXT_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml_to_text(raw_xml: bytes) -> tuple[str, str]:
    root = ET.fromstring(raw_xml)
    title_node = root.find(".//article-title")
    body_node = root.find(".//body")
    title = "" if title_node is None else " ".join("".join(title_node.itertext()).split())
    body = "" if body_node is None else "\n".join(
        " ".join("".join(node.itertext()).split()) for node in body_node.findall(".//p")
    )
    return title, body


def fetch_fulltext(pmcid: str) -> dict:
    europe_url = FULLTEXT_URL.format(pmcid=pmcid)
    request = urllib.request.Request(europe_url, headers={"User-Agent": "ECMO-Track3-v1.4/1.0"})
    source = "Europe PMC fullTextXML"
    url = europe_url
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_xml = response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        params = urllib.parse.urlencode({"db": "pmc", "id": pmcid, "retmode": "xml"})
        url = f"{NCBI_EFETCH}?{params}"
        request = urllib.request.Request(url, headers={"User-Agent": "ECMO-Track3-v1.4/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_xml = response.read()
        source = "NCBI PMC EFetch fallback"
    title, body = xml_to_text(raw_xml)
    if not body:
        raise ValueError(f"retrieved XML for {pmcid} contains no article body")
    return {
        "pmcid": pmcid,
        "retrieval_source": source,
        "source_url": url,
        "title": title,
        "body_text": body,
        "raw_xml_sha256": hashlib.sha256(raw_xml).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sealed_pubmed_snapshot", type=Path)
    parser.add_argument("--sealed-output", type=Path, required=True)
    args = parser.parse_args()
    pubmed = json.loads(args.sealed_pubmed_snapshot.read_text(encoding="utf-8"))
    pmcids = sorted({row["pmcid"] for row in pubmed["articles"] if row.get("pmcid")})
    documents, failures = [], []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_fulltext, pmcid): pmcid for pmcid in pmcids}
        for future in as_completed(futures):
            pmcid = futures[future]
            try:
                documents.append(future.result())
            except Exception as exc:  # noqa: BLE001
                failures.append({"pmcid": pmcid, "error": str(exc)})
    documents.sort(key=lambda row: row["pmcid"])
    args.sealed_output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Europe PMC fullTextXML with NCBI PMC EFetch fallback",
        "access_control": "evidence_only_do_not_load_for_modeling_or_candidate_selection",
        "requested_pmcids": pmcids,
        "failures": failures,
        "documents": documents,
    }
    args.sealed_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Europe PMC with NCBI PMC EFetch fallback",
        "source_urls": [
            "https://europepmc.org/RestfulWebService",
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        ],
        "sealed_pubmed_snapshot_sha256": sha256(args.sealed_pubmed_snapshot),
        "requested_pmcid_count": len(pmcids),
        "retrieved_fulltext_count": len(documents),
        "failed_fulltext_count": len(failures),
        "machine_readable_fulltext_unavailable_count": len(failures),
        "failed_pmcids": [row["pmcid"] for row in failures],
        "sealed_fulltext_snapshot_sha256": sha256(args.sealed_output),
        "labels_written_to_repository": False,
        "retrieval_interpretation": "A failed XML retrieval means machine-readable article-body XML was unavailable from both endpoints; it is not a scientific evidence rejection.",
        "next_gate": "review candidate-linked passages; full-text availability does not by itself admit evidence",
    }
    audit_path = OUTPUT_DIR / "pmc_fulltext_retrieval_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
