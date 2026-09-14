#!/usr/bin/env python3
"""Retrieve permitted PMC full text for the outcome-blind v1.6 evidence queue."""

from __future__ import annotations

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
PUBMED = ROOT / "outputs" / "v1.6" / "external_evidence" / "pubmed_evidence.json"
OUTPUT = ROOT / "outputs" / "v1.6" / "external_evidence"
EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml_text(raw: bytes) -> tuple[str, str]:
    root = ET.fromstring(raw)
    title = root.find(".//article-title")
    body = root.find(".//body")
    title_text = "" if title is None else " ".join("".join(title.itertext()).split())
    body_text = "" if body is None else "\n".join(
        " ".join("".join(paragraph.itertext()).split()) for paragraph in body.findall(".//p")
    )
    return title_text, body_text


def fetch(pmcid: str) -> dict:
    attempts = [
        ("Europe PMC fullTextXML", EUROPE_PMC.format(pmcid=pmcid)),
        ("NCBI PMC EFetch", f"{NCBI_EFETCH}?{urllib.parse.urlencode({'db': 'pmc', 'id': pmcid, 'retmode': 'xml'})}"),
    ]
    errors = []
    for source, url in attempts:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "A2A-Track3-v1.6/1.0"})
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read()
            title, body = xml_text(raw)
            if not body:
                raise ValueError("article XML contains no body")
            return {"pmcid": pmcid, "retrieval_source": source, "source_url": url, "title": title, "body_text": body, "raw_xml_sha256": hashlib.sha256(raw).hexdigest()}
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, ET.ParseError) as exc:
            errors.append(f"{source}: {exc}")
    raise RuntimeError(" | ".join(errors))


def main() -> None:
    pubmed = json.loads(PUBMED.read_text())
    pmcids = sorted({row["pmcid"] for row in pubmed["articles"] if row.get("pmcid")})
    documents, failures = [], []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch, pmcid): pmcid for pmcid in pmcids}
        for future in as_completed(futures):
            pmcid = futures[future]
            try:
                documents.append(future.result())
            except Exception as exc:
                failures.append({"pmcid": pmcid, "error": str(exc)})
    documents.sort(key=lambda row: row["pmcid"])
    failures.sort(key=lambda row: row["pmcid"])
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-external-evidence-v1.6",
        "access_control": "evidence_only_no_activity_outcomes",
        "requested_pmcids": pmcids,
        "failures": failures,
        "documents": documents,
        "external_outcomes_loaded": False,
    }
    output_path = OUTPUT / "pmc_fulltext_evidence.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n")
    audit = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "fulltext_retrieval_complete",
        "pubmed_evidence_sha256": sha256(PUBMED),
        "requested_pmcid_count": len(pmcids),
        "retrieved_fulltext_count": len(documents),
        "failed_fulltext_count": len(failures),
        "failed_pmcids": [row["pmcid"] for row in failures],
        "output_sha256": sha256(output_path),
        "external_outcomes_loaded": False,
        "membership_frozen": False,
        "interpretation": "Full-text availability alone neither admits nor rejects a candidate.",
    }
    audit_path = OUTPUT / "pmc_fulltext_retrieval_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
