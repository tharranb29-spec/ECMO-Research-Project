#!/usr/bin/env python3
"""Run the label-blind pass-1 literature preflight for the v1.6 external cohort.

This program deliberately projects only non-outcome fields from the source queue.
It can prioritize source-grounded pass-2 extraction, but it cannot admit a record.
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
QUEUE = ROOT / "outputs" / "v1.5" / "external_pbind_intake" / "primary_evidence_review_queue.csv"
PUBMED = ROOT / "outputs" / "v1.6" / "external_evidence" / "pubmed_evidence.json"
PMC = ROOT / "outputs" / "v1.6" / "external_evidence" / "pmc_fulltext_evidence.json"
OUTPUT = ROOT / "outputs" / "v1.6" / "external_evidence" / "pass1_metadata_preflight"

# These patterns only establish document-level context. They do not establish that
# a specific structure has a qualifying human wild-type A2A Ki measurement.
TARGET = re.compile(r"\bA\s*\(?2\s*[Aa]\)?\b|adenosine\s+A2A|A\(2A\)", re.IGNORECASE)
HUMAN = re.compile(r"\bhuman(?:s)?\b|\bHomo\s+sapiens\b", re.IGNORECASE)
BINDING = re.compile(
    r"\bbinding\b|radioligand|competition|displacement|affinit(?:y|ies)|"
    r"\bK\s*[_-]?i\b|inhibition constant",
    re.IGNORECASE,
)
KI_ENDPOINT = re.compile(r"\bp\s*K\s*[_-]?i\b|\bK\s*[_-]?i\b|inhibition constant", re.IGNORECASE)
NONPRIMARY_TYPES = {
    "review", "systematic review", "meta-analysis", "editorial", "comment", "news",
    "published erratum", "retracted publication", "retraction of publication",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_doi(value: str | None) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    return value.rstrip(". ")


def split_values(value: str | None) -> list[str]:
    return sorted({item.strip() for item in re.split(r"[|;]", value or "") if item.strip()})


def publication_is_primary(publication_types: list[str]) -> bool:
    normalized = {value.strip().lower() for value in publication_types}
    return not bool(normalized & NONPRIMARY_TYPES)


def document_flags(text: str) -> dict[str, bool]:
    return {
        "a2a_context": bool(TARGET.search(text or "")),
        "human_context": bool(HUMAN.search(text or "")),
        "binding_context": bool(BINDING.search(text or "")),
        "ki_endpoint_context": bool(KI_ENDPOINT.search(text or "")),
    }


def assess_candidate(row: dict[str, str], articles: dict[str, dict], fulltexts: dict[str, dict]) -> dict:
    """Assess source metadata without reading any outcome-derived queue column."""
    candidate = {
        "candidate_id": row["candidate_id"],
        "bindingdb_monomer_id": row["bindingdb_monomer_id"],
        "standardized_smiles": row["standardized_smiles"],
        "standardized_inchikey": row["standardized_inchikey"],
        "generic_murcko_scaffold_smiles": row["generic_murcko_scaffold_smiles"],
        "queue_rank": int(row["queue_rank"]),
        "pmids": split_values(row.get("pmid")),
        "dois": sorted({normalize_doi(value) for value in split_values(row.get("doi"))}),
    }
    linked_articles = [articles[pmid] for pmid in candidate["pmids"] if pmid in articles]
    missing_pmids = [pmid for pmid in candidate["pmids"] if pmid not in articles]
    reasons: list[str] = []
    article_assessments = []
    for article in linked_articles:
        pubmed_doi = normalize_doi(article.get("doi"))
        doi_agrees = not candidate["dois"] or not pubmed_doi or pubmed_doi in candidate["dois"]
        primary = publication_is_primary(article.get("publication_types", []))
        abstract_text = f"{article.get('title', '')}\n{article.get('abstract', '')}"
        abstract_flags = document_flags(abstract_text)
        pmcid = article.get("pmcid", "")
        fulltext = fulltexts.get(pmcid) if pmcid else None
        fulltext_flags = document_flags(fulltext.get("body_text", "")) if fulltext else None
        combined_flags = {
            name: abstract_flags[name] or bool(fulltext_flags and fulltext_flags[name])
            for name in abstract_flags
        }
        if not doi_agrees:
            article_status = "quarantine_identifier_disagreement"
        elif not primary:
            article_status = "quarantine_nonprimary_source"
        elif not combined_flags["a2a_context"]:
            article_status = "quarantine_target_not_supported"
        elif not combined_flags["binding_context"]:
            article_status = "metadata_pass_requires_endpoint_resolution"
        elif fulltext and combined_flags["human_context"] and combined_flags["ki_endpoint_context"]:
            article_status = "metadata_pass_fulltext_ready"
        elif fulltext:
            article_status = "metadata_pass_fulltext_requires_species_or_endpoint_resolution"
        else:
            article_status = "metadata_pass_needs_fulltext"
        article_assessments.append({
            "pmid": article["pmid"], "pubmed_doi": pubmed_doi, "doi_agrees": doi_agrees,
            "publication_types": article.get("publication_types", []), "publication_is_primary": primary,
            "pmcid": pmcid, "fulltext_available": bool(fulltext), "abstract_flags": abstract_flags,
            "fulltext_flags": fulltext_flags, "article_title": article.get("title", ""),
            "status": article_status,
        })

    status_priority = [
        "metadata_pass_fulltext_ready",
        "metadata_pass_fulltext_requires_species_or_endpoint_resolution",
        "metadata_pass_needs_fulltext",
        "metadata_pass_requires_endpoint_resolution",
    ]
    passing_statuses = {item["status"] for item in article_assessments if item["status"].startswith("metadata_pass")}
    if not candidate["pmids"] and not candidate["dois"]:
        status = "quarantine_missing_primary_locator"
        reasons.append("neither PMID nor DOI is available")
    elif passing_statuses:
        status = next(value for value in status_priority if value in passing_statuses)
        reasons.append("at least one linked primary source passed deterministic metadata preflight")
        if missing_pmids:
            reasons.append("additional linked PMIDs were absent from the frozen snapshot")
    elif candidate["pmids"] and not linked_articles:
        status = "quarantine_missing_pubmed_metadata"
        reasons.append("all linked PMIDs are absent from the frozen PubMed snapshot")
    elif not linked_articles:
        status = "metadata_pass_doi_only_needs_source_retrieval"
        reasons.append("DOI is available but no PMID-linked metadata was retrieved")
    else:
        statuses = {item["status"] for item in article_assessments}
        if "quarantine_identifier_disagreement" in statuses:
            status = "quarantine_identifier_disagreement"
        elif "quarantine_nonprimary_source" in statuses:
            status = "quarantine_nonprimary_source"
        else:
            status = "quarantine_target_not_supported"
        reasons.append("no linked source passed deterministic metadata preflight")
    candidate.update({
        "pmid": "|".join(candidate.pop("pmids")),
        "doi": "|".join(candidate.pop("dois")),
        "pmcids": "|".join(sorted({item["pmcid"] for item in article_assessments if item["pmcid"]})),
        "article_titles": " | ".join(item["article_title"] for item in article_assessments),
        "fulltext_available": any(item["fulltext_available"] for item in article_assessments),
        "article_assessments": article_assessments,
        "missing_pmids": missing_pmids,
    })
    candidate.update({
        "pass_1_status": status,
        "pass_1_reasons": reasons,
        "pass_2_required": status.startswith("metadata_pass"),
        "external_cohort_admitted": False,
        "outcome_fields_loaded": False,
    })
    return candidate


def main() -> None:
    rows = list(csv.DictReader(QUEUE.open(encoding="utf-8")))
    pubmed = json.loads(PUBMED.read_text(encoding="utf-8"))
    pmc = json.loads(PMC.read_text(encoding="utf-8"))
    if pubmed.get("external_outcomes_loaded") or pmc.get("external_outcomes_loaded"):
        raise RuntimeError("outcome firewall violation in evidence snapshots")
    articles = {row["pmid"]: row for row in pubmed["articles"]}
    fulltexts = {row["pmcid"]: row for row in pmc["documents"]}
    assessments = [assess_candidate(row, articles, fulltexts) for row in rows]
    assessments.sort(key=lambda row: row["queue_rank"])
    status_counts = Counter(row["pass_1_status"] for row in assessments)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    packet_path = OUTPUT / "pass1_metadata_preflight.json"
    packet = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-external-computational-evidence-pass1-v1.6",
        "access_control": "label_blind_evidence_only",
        "outcome_fields_loaded": False,
        "external_cohort_admitted_count": 0,
        "candidate_count": len(assessments),
        "records": assessments,
    }
    packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")

    queue_path = OUTPUT / "pass2_source_extraction_queue.csv"
    fields = [
        "queue_rank", "candidate_id", "bindingdb_monomer_id", "standardized_inchikey",
        "doi", "pmid", "pmcids", "article_titles", "pass_1_status", "fulltext_available",
        "pass_2_required", "external_cohort_admitted",
    ]
    with queue_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in assessments:
            writer.writerow({key: row.get(key, "") for key in fields})

    audit = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-external-computational-evidence-pass1-v1.6",
        "source_hashes": {"source_queue": sha256(QUEUE), "pubmed_snapshot": sha256(PUBMED), "pmc_snapshot": sha256(PMC)},
        "artifact_hashes": {"preflight_packet": sha256(packet_path), "pass2_queue": sha256(queue_path)},
        "candidate_count": len(assessments),
        "status_counts": dict(sorted(status_counts.items())),
        "pass_2_required_count": sum(row["pass_2_required"] for row in assessments),
        "fulltext_available_candidate_count": sum(row.get("fulltext_available", False) for row in assessments),
        "external_cohort_admitted_count": 0,
        "outcome_fields_loaded": False,
        "human_validation_claimed": False,
        "next_gate": "Run an independently configured, source-grounded pass-2 extractor and require exact agreement on every frozen field before membership freeze.",
    }
    audit_path = OUTPUT / "pass1_metadata_preflight_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
