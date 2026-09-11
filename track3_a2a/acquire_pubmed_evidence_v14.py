#!/usr/bin/env python3

"""Retrieve PubMed metadata for the label-free v1.4 primary-paper queue."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / "outputs" / "v1.4" / "evidence_review" / "gtopdb_2026.2" / "primary_paper_review_queue_label_free.csv"
OUTPUT_DIR = ROOT / "outputs" / "v1.4" / "evidence_review" / "gtopdb_2026.2"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_content(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext()).strip()


def parse_article(article: ET.Element) -> dict:
    medline = article.find("MedlineCitation")
    pubmed_data = article.find("PubmedData")
    if medline is None:
        raise ValueError("PubMedArticle lacks MedlineCitation")
    pmid = text_content(medline.find("PMID"))
    article_node = medline.find("Article")
    if article_node is None:
        raise ValueError(f"PubMed article {pmid} lacks Article metadata")
    abstract_parts = []
    abstract = article_node.find("Abstract")
    if abstract is not None:
        for node in abstract.findall("AbstractText"):
            label = node.attrib.get("Label")
            value = text_content(node)
            abstract_parts.append(f"{label}: {value}" if label else value)
    identifiers = {}
    if pubmed_data is not None:
        for node in pubmed_data.findall("ArticleIdList/ArticleId"):
            identifiers[node.attrib.get("IdType", "unknown")] = text_content(node)
    journal = article_node.find("Journal")
    return {
        "pmid": pmid,
        "title": text_content(article_node.find("ArticleTitle")),
        "abstract": "\n".join(abstract_parts),
        "journal": text_content(journal.find("Title")) if journal is not None else "",
        "publication_types": [text_content(node) for node in article_node.findall("PublicationTypeList/PublicationType")],
        "doi": identifiers.get("doi"),
        "pmcid": identifiers.get("pmc"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sealed-output", type=Path, required=True)
    args = parser.parse_args()
    with QUEUE.open(newline="", encoding="utf-8") as handle:
        queue = list(csv.DictReader(handle))
    pmids = sorted({pmid for row in queue for pmid in row["primary_pmids"].split(";") if pmid})
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    })
    request = urllib.request.Request(
        f"{EFETCH}?{params}", headers={"User-Agent": "ECMO-Track3-v1.4/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_xml = response.read()
    root = ET.fromstring(raw_xml)
    articles = [parse_article(node) for node in root.findall("PubmedArticle")]
    returned = {row["pmid"] for row in articles}
    missing = sorted(set(pmids) - returned)
    args.sealed_output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "NCBI PubMed E-utilities",
        "endpoint": EFETCH,
        "access_control": "evidence_only_do_not_load_for_modeling_or_candidate_selection",
        "requested_pmids": pmids,
        "missing_pmids": missing,
        "articles": articles,
    }
    args.sealed_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit_path = OUTPUT_DIR / "primary_reference_retrieval_audit.json"
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "NCBI PubMed E-utilities",
        "source_url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/",
        "queue_sha256": sha256(QUEUE),
        "requested_pmid_count": len(pmids),
        "retrieved_article_count": len(articles),
        "missing_pmids": missing,
        "articles_with_abstract_count": sum(bool(row["abstract"]) for row in articles),
        "articles_with_doi_count": sum(bool(row["doi"]) for row in articles),
        "articles_with_pmcid_count": sum(bool(row["pmcid"]) for row in articles),
        "sealed_primary_evidence_sha256": sha256(args.sealed_output),
        "labels_written_to_repository": False,
        "next_gate": "triage the retrieved primary text for explicit human A2A functional evidence and obtain full text where abstracts are insufficient",
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
