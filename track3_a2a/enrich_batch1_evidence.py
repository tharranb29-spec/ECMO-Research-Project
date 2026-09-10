#!/usr/bin/env python3

"""Enrich curation Batch 1 with official ChEMBL assay and document metadata."""

import argparse
import csv
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib import request


ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "data" / "curated" / "chembl251_curation_plan_220.csv"
PACKET = ROOT / "data" / "curated" / "chembl251_functional_review_packet.json"
CACHE = ROOT / "data" / "raw" / "chembl251_evidence"
DOSSIER = ROOT / "data" / "curated" / "chembl251_batch_01_evidence_dossier.json"
AUDIT = ROOT / "outputs" / "dataset" / "batch_01_evidence_audit.json"
API = "https://www.ebi.ac.uk/chembl/api/data"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def fetch_json(kind, chembl_id, refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{kind}_{chembl_id}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    url = f"{API}/{kind}/{chembl_id}.json"
    req = request.Request(url, headers={"User-Agent": "ZJU-ISM-A2A-Track3/1.1"})
    last_error = None
    for attempt in range(3):
        try:
            with request.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            return payload
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to retrieve {kind} {chembl_id}: {last_error}")


def document_summary(payload):
    return {
        "document_chembl_id": payload.get("document_chembl_id"),
        "document_type": payload.get("doc_type"),
        "title": payload.get("title"),
        "authors": payload.get("authors"),
        "journal": payload.get("journal_full_title") or payload.get("journal"),
        "year": payload.get("year"),
        "doi": payload.get("doi"),
        "pubmed_id": payload.get("pubmed_id"),
        "chembl_url": f"https://www.ebi.ac.uk/chembl/explore/document/{payload.get('document_chembl_id')}",
        "doi_url": f"https://doi.org/{payload['doi']}" if payload.get("doi") else None,
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{payload['pubmed_id']}/" if payload.get("pubmed_id") else None,
    }


def assay_summary(payload):
    return {
        "assay_chembl_id": payload.get("assay_chembl_id"),
        "assay_type": payload.get("assay_type"),
        "description": payload.get("description"),
        "confidence_score": payload.get("confidence_score"),
        "relationship_type": payload.get("relationship_type"),
        "target_chembl_id": payload.get("target_chembl_id"),
        "organism": payload.get("assay_organism"),
        "cell_type": payload.get("assay_cell_type"),
        "tissue": payload.get("assay_tissue"),
        "chembl_url": f"https://www.ebi.ac.uk/chembl/explore/assay/{payload.get('assay_chembl_id')}",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    with PLAN.open(newline="", encoding="utf-8") as handle:
        batch = [row for row in csv.DictReader(handle) if row["curation_batch"] == "1"]
    packet = {
        row["chembl_id"]: row
        for row in json.loads(PACKET.read_text(encoding="utf-8"))["records"]
    }

    document_cache = {}
    assay_cache = {}
    records = []
    for plan_row in batch:
        evidence = packet[plan_row["chembl_id"]]["functional_evidence"]
        document_ids = sorted({row["document_chembl_id"] for row in evidence if row.get("document_chembl_id")})
        assay_ids = sorted({row["assay_chembl_id"] for row in evidence if row.get("assay_chembl_id")})
        for document_id in document_ids:
            if document_id not in document_cache:
                document_cache[document_id] = document_summary(fetch_json("document", document_id, args.refresh))
        for assay_id in assay_ids:
            if assay_id not in assay_cache:
                assay_cache[assay_id] = assay_summary(fetch_json("assay", assay_id, args.refresh))
        records.append({
            "chembl_id": plan_row["chembl_id"],
            "molecule_name": plan_row["molecule_name"],
            "proposed_class": plan_row["proposed_class"],
            "evidence_strength": plan_row["evidence_strength"],
            "training_eligible": False,
            "documents": [document_cache[key] for key in document_ids],
            "assays": [assay_cache[key] for key in assay_ids],
            "functional_activity_evidence": evidence,
            "review_questions": [
                "Does the source report a human A2A functional response rather than binding alone?",
                "Does the source support the proposed agonist or antagonist direction?",
                "Are species, construct, mutation, and assay context acceptable?",
                "Is the tested molecular identity consistent with the standardized parent structure?",
            ],
        })

    dossier = {
        "schema_version": 1,
        "created_at": utc_now(),
        "curation_batch": 1,
        "record_count": len(records),
        "training_eligible_count": 0,
        "records": records,
    }
    DOSSIER.write_text(json.dumps(dossier, indent=2) + "\n", encoding="utf-8")
    all_documents = [doc for row in records for doc in row["documents"]]
    unique_documents = {doc["document_chembl_id"]: doc for doc in all_documents}
    all_assays = [assay for row in records for assay in row["assays"]]
    unique_assays = {assay["assay_chembl_id"]: assay for assay in all_assays}
    audit = {
        "created_at": utc_now(),
        "batch_record_count": len(records),
        "unique_document_count": len(unique_documents),
        "unique_assay_count": len(unique_assays),
        "document_type_counts": dict(sorted(Counter(doc.get("document_type") or "missing" for doc in unique_documents.values()).items())),
        "documents_with_doi": sum(bool(doc.get("doi")) for doc in unique_documents.values()),
        "documents_with_pubmed_id": sum(bool(doc.get("pubmed_id")) for doc in unique_documents.values()),
        "assay_target_counts": dict(sorted(Counter(assay.get("target_chembl_id") or "missing" for assay in unique_assays.values()).items())),
        "assay_organism_counts": dict(sorted(Counter(assay.get("organism") or "missing" for assay in unique_assays.values()).items())),
        "training_eligible_count": 0,
        "next_gate": "two independent reviewers inspect the linked assay and source publication",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
