#!/usr/bin/env python3
"""Retrieve outcome-blind PubMed evidence for the frozen v1.6 pBind_Ki queue."""

from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / "outputs" / "v1.5" / "external_pbind_intake" / "primary_evidence_review_queue.csv"
OUTPUT = ROOT / "outputs" / "v1.6" / "external_evidence"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext()).strip()


def parse_article(node: ET.Element) -> dict:
    citation = node.find("MedlineCitation")
    pubmed = node.find("PubmedData")
    if citation is None:
        raise RuntimeError("missing MedlineCitation")
    article = citation.find("Article")
    if article is None:
        raise RuntimeError("missing Article")
    identifiers = {}
    if pubmed is not None:
        for item in pubmed.findall("ArticleIdList/ArticleId"):
            identifiers[item.attrib.get("IdType", "unknown")] = text(item)
    abstract = []
    for part in article.findall("Abstract/AbstractText"):
        value = text(part)
        label = part.attrib.get("Label")
        abstract.append(f"{label}: {value}" if label else value)
    return {
        "pmid": text(citation.find("PMID")),
        "doi": identifiers.get("doi", ""),
        "pmcid": identifiers.get("pmc", ""),
        "title": text(article.find("ArticleTitle")),
        "abstract": "\n".join(abstract),
        "journal": text(article.find("Journal/Title")),
        "publication_types": [text(item) for item in article.findall("PublicationTypeList/PublicationType")],
        "mesh_terms": [text(item.find("DescriptorName")) for item in citation.findall("MeshHeadingList/MeshHeading")],
    }


def fetch_batch(pmids: list[str]) -> bytes:
    query = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    request = urllib.request.Request(f"{EFETCH}?{query}", headers={"User-Agent": "A2A-Track3-v1.6/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def main() -> None:
    with QUEUE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    pmids = sorted({value for row in rows for value in row["pmid"].split("|") if value}, key=int)
    articles = []
    raw_hashes = []
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for index in range(0, len(pmids), 80):
        batch = pmids[index:index + 80]
        raw = fetch_batch(batch)
        raw_path = OUTPUT / f"pubmed_batch_{index // 80 + 1:02d}.xml"
        raw_path.write_bytes(raw)
        raw_hashes.append({"path": str(raw_path.relative_to(ROOT)), "sha256": sha256(raw_path)})
        root = ET.fromstring(raw)
        articles.extend(parse_article(node) for node in root.findall("PubmedArticle"))
        if index + 80 < len(pmids):
            time.sleep(0.4)

    returned = {article["pmid"] for article in articles}
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-external-evidence-v1.6",
        "source": "NCBI PubMed E-utilities",
        "endpoint": EFETCH,
        "outcome_fields_requested": False,
        "external_outcomes_loaded": False,
        "requested_pmids": pmids,
        "missing_pmids": sorted(set(pmids) - returned, key=int),
        "articles": sorted(articles, key=lambda row: int(row["pmid"])),
    }
    evidence_path = OUTPUT / "pubmed_evidence.json"
    evidence_path.write_text(json.dumps(payload, indent=2) + "\n")
    audit = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "retrieved_outcome_blind_metadata_and_abstracts",
        "queue_sha256": sha256(QUEUE),
        "requested_pmid_count": len(pmids),
        "retrieved_article_count": len(articles),
        "articles_with_abstract_count": sum(bool(row["abstract"]) for row in articles),
        "articles_with_pmcid_count": sum(bool(row["pmcid"]) for row in articles),
        "missing_pmids": payload["missing_pmids"],
        "raw_batches": raw_hashes,
        "evidence_path": str(evidence_path.relative_to(ROOT)),
        "evidence_sha256": sha256(evidence_path),
        "external_outcomes_loaded": False,
        "membership_frozen": False,
        "next_gate": "Run deterministic publication/identifier triage, retrieve permitted full text, and require a separate source-grounded extraction pass before admission.",
    }
    audit_path = OUTPUT / "pubmed_retrieval_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
