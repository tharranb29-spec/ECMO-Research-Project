#!/usr/bin/env python3

"""Triage PubMed abstracts for the sealed GtoPdb external-evidence packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.build_evidence_review_queue import classify_readout


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "v1.4" / "evidence_review" / "gtopdb_2026.2"
TARGET_PATTERN = re.compile(r"\bA\s*\(?2A\)?\b|A2A|A\(2A\)", re.IGNORECASE)
HUMAN_PATTERN = re.compile(r"\bhuman(?:s)?\b|\bHomo sapiens\b", re.IGNORECASE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def candidate_is_mentioned(name: str, text: str) -> bool:
    needle = normalized_text(name)
    return len(needle) >= 4 and needle in normalized_text(text)


def action_is_mentioned(functional_class: str, text: str) -> bool:
    if functional_class == "agonist":
        return bool(re.search(r"\b(?:full |partial )?agonist", text, re.IGNORECASE))
    if functional_class == "antagonist":
        return bool(re.search(r"\bantagonist", text, re.IGNORECASE))
    return False


def candidate_context(name: str, title: str, abstract: str, radius: int = 1) -> str:
    """Return only title/abstract sentences adjacent to a candidate mention."""
    sentences = [title] + [
        value.strip() for value in re.split(r"(?<=[.!?])\s+", abstract or "") if value.strip()
    ]
    mentioned = [index for index, sentence in enumerate(sentences) if candidate_is_mentioned(name, sentence)]
    selected = set()
    for index in mentioned:
        selected.update(range(max(0, index - radius), min(len(sentences), index + radius + 1)))
    return " ".join(sentences[index] for index in sorted(selected))


def triage_record(record: dict, articles: dict[str, dict]) -> dict:
    pmids = sorted({
        ref["pmid"]
        for row in record["evidence_rows"]
        for ref in row["primary_references"]
        if ref.get("pmid")
    })
    assessments = []
    for pmid in pmids:
        article = articles.get(str(pmid))
        if article is None:
            assessments.append({"pmid": str(pmid), "status": "metadata_missing"})
            continue
        full_text = f"{article['title']}\n{article['abstract']}"
        local_text = candidate_context(record["molecule_name"], article["title"], article["abstract"])
        flags = {
            "candidate_mentioned": bool(local_text),
            "a2a_context": bool(TARGET_PATTERN.search(local_text)),
            "human_context": bool(HUMAN_PATTERN.search(local_text)),
            "functional_readout": classify_readout(local_text) == "functional",
            "expected_action_mentioned": action_is_mentioned(record["proposed_functional_class"], local_text),
        }
        if all(flags.values()):
            status = "high_priority_full_text_review"
        elif bool(TARGET_PATTERN.search(full_text)) and classify_readout(full_text) == "functional":
            status = "possible_functional_context_needs_candidate_linkage"
        else:
            status = "abstract_insufficient"
        assessments.append({
            "pmid": str(pmid),
            "doi": article.get("doi"),
            "pmcid": article.get("pmcid"),
            "title": article.get("title"),
            "flags": flags,
            "status": status,
        })
    statuses = {row["status"] for row in assessments}
    if "high_priority_full_text_review" in statuses:
        record_status = "high_priority_full_text_review"
    elif "possible_functional_context_needs_candidate_linkage" in statuses:
        record_status = "possible_functional_context_needs_candidate_linkage"
    elif assessments:
        record_status = "abstract_insufficient"
    else:
        record_status = "no_primary_pubmed_record"
    return {
        "record_id": record["record_id"],
        "molecule_name": record["molecule_name"],
        "proposed_functional_class": record["proposed_functional_class"],
        "abstract_triage_status": record_status,
        "dataset_admission_eligible": False,
        "training_eligible": False,
        "article_assessments": assessments,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sealed_evidence_packet", type=Path)
    parser.add_argument("sealed_pubmed_snapshot", type=Path)
    parser.add_argument("--sealed-output", type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.sealed_evidence_packet.read_text(encoding="utf-8"))
    pubmed = json.loads(args.sealed_pubmed_snapshot.read_text(encoding="utf-8"))
    articles = {row["pmid"]: row for row in pubmed["articles"]}
    triage = [triage_record(row, articles) for row in evidence["records"]]
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-gtopdb-primary-evidence-triage-v1.4",
        "access_control": "evidence_only_do_not_load_for_modeling_or_candidate_selection",
        "human_validation_claimed": False,
        "record_count": len(triage),
        "records": triage,
    }
    args.sealed_output.parent.mkdir(parents=True, exist_ok=True)
    args.sealed_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    full_text_queue = OUTPUT_DIR / "full_text_review_queue_label_free.csv"
    fields = ["record_id", "molecule_name", "pmids", "pmcids", "abstract_triage_status"]
    with full_text_queue.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in triage:
            pmids = sorted({item["pmid"] for item in row["article_assessments"]})
            pmcids = sorted({item["pmcid"] for item in row["article_assessments"] if item.get("pmcid")})
            writer.writerow({
                "record_id": row["record_id"],
                "molecule_name": row["molecule_name"],
                "pmids": ";".join(pmids),
                "pmcids": ";".join(pmcids),
                "abstract_triage_status": row["abstract_triage_status"],
            })
    status_counts = Counter(row["abstract_triage_status"] for row in triage)
    article_status_counts = Counter(
        article["status"] for row in triage for article in row["article_assessments"]
    )
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-gtopdb-primary-evidence-triage-v1.4",
        "source_hashes": {
            "sealed_evidence_packet": sha256(args.sealed_evidence_packet),
            "sealed_pubmed_snapshot": sha256(args.sealed_pubmed_snapshot),
            "triage_runner": sha256(Path(__file__)),
            "sealed_triage_packet": sha256(args.sealed_output),
            "label_free_full_text_queue": sha256(full_text_queue),
        },
        "candidate_count": len(triage),
        "candidate_status_counts": dict(sorted(status_counts.items())),
        "article_assessment_counts": dict(sorted(article_status_counts.items())),
        "evidence_admitted_count": 0,
        "labels_written_to_repository": False,
        "human_validation_claimed": False,
        "next_gate": "retrieve available full text and perform record-level dual evidence review; abstract triage cannot admit a label",
    }
    audit_path = OUTPUT_DIR / "primary_evidence_triage_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
