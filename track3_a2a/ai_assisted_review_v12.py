#!/usr/bin/env python3

"""Create non-admitting AI-assisted evidence recommendations for all 220 records."""

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.build_evidence_review_queue import classify_readout
from track3_a2a.enrich_batch1_evidence import assay_summary, document_summary, fetch_json


ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "data" / "curated" / "chembl251_curation_plan_220_v1.2.csv"
PACKET = ROOT / "data" / "curated" / "chembl251_functional_review_packet.json"
OUTPUT_CSV = ROOT / "data" / "curated" / "chembl251_ai_assisted_review_v1.2.csv"
OUTPUT_JSON = ROOT / "data" / "curated" / "chembl251_ai_assisted_review_v1.2.json"
AUDIT = ROOT / "outputs" / "dataset" / "ai_assisted_review_v1.2_audit.json"

REVIEW_TITLE_RISK = re.compile(
    r"\breview\b|\bperspective\b|recent advances|therapeutic implications|"
    r"drug discovery target|challenges, successes|promising directions",
    re.IGNORECASE,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def is_primary_source_candidate(document):
    return (
        document.get("document_type") == "PUBLICATION"
        and bool(document.get("doi") or document.get("pubmed_id"))
        and not REVIEW_TITLE_RISK.search(document.get("title") or "")
    )


def assess_record(plan_row, packet_row, documents, assays):
    evidence = packet_row["functional_evidence"]
    proposed = plan_row["proposed_class"]
    qualifying = []
    warnings = []
    observed_classes = sorted({row.get("proposed_functional_class") for row in evidence if row.get("proposed_functional_class")})
    if observed_classes != [proposed]:
        warnings.append(f"functional class signals differ: {observed_classes}")

    for row in evidence:
        assay = assays.get(row.get("assay_chembl_id"), {})
        document = documents.get(row.get("document_chembl_id"), {})
        reasons = []
        if classify_readout(row.get("description")) != "functional":
            reasons.append("readout is not explicitly functional")
        if assay.get("target_chembl_id") != "CHEMBL251":
            reasons.append(f"target is {assay.get('target_chembl_id') or 'missing'}")
        if assay.get("organism") != "Homo sapiens":
            reasons.append(f"organism is {assay.get('organism') or 'missing'}")
        confidence = assay.get("confidence_score")
        if confidence is None or int(confidence) < 8:
            reasons.append(f"ChEMBL target confidence is {confidence}")
        if row.get("proposed_functional_class") != proposed:
            reasons.append("row class disagrees with proposed class")
        if not reasons:
            qualifying.append({"row": row, "assay": assay, "document": document})
        else:
            warnings.append(f"activity {row.get('activity_id')}: " + "; ".join(reasons))

    primary_rows = [item for item in qualifying if is_primary_source_candidate(item["document"])]
    unique_primary_documents = {item["document"].get("document_chembl_id") for item in primary_rows}
    unique_qualifying_assays = {item["assay"].get("assay_chembl_id") for item in qualifying}
    if primary_rows and observed_classes == [proposed]:
        tier = "tier_1"
        recommendation = f"provisional_accept_{proposed}"
        confidence = "high" if len(unique_primary_documents) >= 2 and len(unique_qualifying_assays) >= 2 else "moderate"
    elif qualifying and observed_classes == [proposed]:
        tier = "unresolved"
        recommendation = "needs_primary_source_review"
        confidence = "low"
        warnings.append("qualifying assay evidence is linked only to review/perspective-risk publications")
    else:
        tier = "excluded"
        recommendation = "reject_or_resolve"
        confidence = "low"

    return {
        "chembl_id": plan_row["chembl_id"],
        "molecule_name": plan_row["molecule_name"],
        "curation_batch": int(plan_row["curation_batch"]),
        "proposed_class": proposed,
        "ai_recommendation": recommendation,
        "recommended_evidence_tier": tier,
        "recommendation_confidence": confidence,
        "functional_activity_rows": len(evidence),
        "qualifying_activity_rows": len(qualifying),
        "qualifying_assays": len(unique_qualifying_assays),
        "primary_source_documents": len(unique_primary_documents),
        "warning_count": len(warnings),
        "warnings": warnings,
        "human_review_required": True,
        "training_eligible": False,
    }


def main():
    with PLAN.open(newline="", encoding="utf-8") as handle:
        plan = list(csv.DictReader(handle))
    packet = {row["chembl_id"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["records"]}
    evidence_rows = [item for row in plan for item in packet[row["chembl_id"]]["functional_evidence"]]
    document_ids = sorted({row["document_chembl_id"] for row in evidence_rows if row.get("document_chembl_id")})
    assay_ids = sorted({row["assay_chembl_id"] for row in evidence_rows if row.get("assay_chembl_id")})
    documents = {key: document_summary(fetch_json("document", key)) for key in document_ids}
    assays = {key: assay_summary(fetch_json("assay", key)) for key in assay_ids}
    reviews = [assess_record(row, packet[row["chembl_id"]], documents, assays) for row in plan]

    flat_rows = []
    for row in reviews:
        flat = dict(row)
        flat["warnings"] = " | ".join(row["warnings"])
        flat_rows.append(flat)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0]))
        writer.writeheader()
        writer.writerows(flat_rows)
    OUTPUT_JSON.write_text(json.dumps({
        "schema_version": 1,
        "created_at": utc_now(),
        "specification_id": "a2a-functional-classification-v1.2",
        "review_type": "AI-assisted preliminary evidence review",
        "human_validation_claimed": False,
        "training_eligible_count": 0,
        "records": reviews,
    }, indent=2) + "\n", encoding="utf-8")

    audit = {
        "created_at": utc_now(),
        "plan_record_count": len(plan),
        "activity_row_count": len(evidence_rows),
        "official_document_count": len(documents),
        "official_assay_count": len(assays),
        "recommendation_counts": dict(sorted(Counter(row["ai_recommendation"] for row in reviews).items())),
        "recommended_tier_counts": dict(sorted(Counter(row["recommended_evidence_tier"] for row in reviews).items())),
        "recommendation_confidence_counts": dict(sorted(Counter(row["recommendation_confidence"] for row in reviews).items())),
        "records_with_warnings": sum(bool(row["warnings"]) for row in reviews),
        "human_validation_claimed": False,
        "training_eligible_count": 0,
        "next_gate": "targeted human confirmation or explicitly provisional computational-only partition"
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
