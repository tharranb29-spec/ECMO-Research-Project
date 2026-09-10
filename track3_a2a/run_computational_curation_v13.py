#!/usr/bin/env python3

"""Run the versioned, non-human A2A functional-label evidence audit."""

import csv
import glob
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.build_evidence_review_queue import classify_readout
from track3_a2a.enrich_batch1_evidence import assay_summary, document_summary
from track3_a2a.ingest_chembl_functional import activity_class


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "computational_curation.v1.3.json"
PLAN = ROOT / "data" / "curated" / "chembl251_curation_plan_220_v1.2.csv"
PACKET = ROOT / "data" / "curated" / "chembl251_functional_review_packet.json"
STANDARDIZED = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
CACHE = ROOT / "data" / "raw" / "chembl251_evidence"
RAW_ACTIVITIES = ROOT / "data" / "raw" / "chembl251_functional" / "activities_offset_*.json"
OUTPUT_JSON = ROOT / "data" / "curated" / "chembl251_computational_audit_v1.3.json"
OUTPUT_CSV = ROOT / "data" / "curated" / "chembl251_computational_audit_v1.3.csv"
BENCHMARK = ROOT / "data" / "curated" / "chembl251_computational_benchmark_v1.3.json"
AUDIT = ROOT / "outputs" / "v1.3" / "computational_curation_audit.json"

REVIEW_TITLE_RISK = re.compile(
    r"\breview\b|\bperspective\b|recent advances|therapeutic implications|"
    r"drug discovery target|challenges, successes|promising directions",
    re.IGNORECASE,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_many(paths):
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_cached_summary(kind, chembl_id):
    path = CACHE / f"{kind}_{chembl_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing cached {kind} evidence: {chembl_id}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return document_summary(payload) if kind == "document" else assay_summary(payload)


def is_primary_source(document):
    return (
        document.get("document_type") == "PUBLICATION"
        and bool(document.get("doi") or document.get("pubmed_id"))
        and not REVIEW_TITLE_RISK.search(document.get("title") or "")
    )


def evidence_url(document, assay):
    return (
        document.get("doi_url")
        or document.get("pubmed_url")
        or document.get("chembl_url")
        or assay.get("chembl_url")
    )


def load_excluded_function_evidence(plan_ids, config):
    """Recover endpoint-excluded annotations omitted from the binary review packet."""
    excluded_classes = set(config["endpoint"]["excluded"])
    records = {}
    raw_paths = [Path(path) for path in sorted(glob.glob(str(RAW_ACTIVITIES)))]
    if not raw_paths:
        raise FileNotFoundError(f"No raw ChEMBL activity pages matched {RAW_ACTIVITIES}")
    for raw_path in raw_paths:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        for row in payload.get("activities", []):
            chembl_id = row.get("parent_molecule_chembl_id") or row.get("molecule_chembl_id")
            if chembl_id not in plan_ids:
                continue
            functional_class, rule = activity_class(row)
            if functional_class not in excluded_classes:
                continue
            action_type = row.get("action_type")
            if isinstance(action_type, dict):
                action_type = action_type.get("action_type")
            records.setdefault(chembl_id, []).append({
                "functional_class": functional_class,
                "classification_rule": rule,
                "activity_id": row.get("activity_id"),
                "assay_chembl_id": row.get("assay_chembl_id"),
                "document_chembl_id": row.get("document_chembl_id"),
                "standard_type": row.get("standard_type"),
                "standard_value": row.get("standard_value"),
                "standard_units": row.get("standard_units"),
                "action_type": action_type,
            })
    return records


def adjudicate_record(plan_row, packet_row, assays, documents, config, excluded_evidence=None):
    target = config["target"]
    proposed_class = plan_row["proposed_class"]
    observed_classes = sorted({
        row.get("proposed_functional_class")
        for row in packet_row["functional_evidence"]
        if row.get("proposed_functional_class")
    })
    qualifying = []
    context_failures = []
    binding_only = []

    for row in packet_row["functional_evidence"]:
        assay = assays[row["assay_chembl_id"]]
        document = documents[row["document_chembl_id"]]
        readout = classify_readout(row.get("description"))
        reasons = []
        if readout != "functional":
            reasons.append(f"readout={readout}")
            if readout == "binding_only":
                binding_only.append(row)
        if assay.get("target_chembl_id") != target["chembl_id"]:
            reasons.append(f"target={assay.get('target_chembl_id') or 'missing'}")
        if assay.get("organism") != target["organism"]:
            reasons.append(f"organism={assay.get('organism') or 'missing'}")
        confidence = assay.get("confidence_score")
        if confidence is None or int(confidence) < int(target["minimum_target_confidence"]):
            reasons.append(f"target_confidence={confidence}")
        if row.get("proposed_functional_class") != proposed_class:
            reasons.append("class_direction_disagrees")

        item = {"activity": row, "assay": assay, "document": document}
        if reasons:
            context_failures.append({"activity_id": row.get("activity_id"), "reasons": reasons})
        else:
            qualifying.append(item)

    primary = [item for item in qualifying if is_primary_source(item["document"])]
    primary_documents = sorted({item["document"]["document_chembl_id"] for item in primary})
    qualifying_assays = sorted({item["assay"]["assay_chembl_id"] for item in qualifying})
    class_conflict = observed_classes != [proposed_class]
    excluded_evidence = excluded_evidence or []
    excluded_classes = sorted({row["functional_class"] for row in excluded_evidence})

    if excluded_evidence:
        decision = "quarantine_excluded_function"
        tier = None
        rationale = (
            f"Raw ChEMBL evidence contains endpoint-excluded functional class(es) {excluded_classes}; "
            "the record cannot enter the binary agonist-versus-antagonist endpoint."
        )
    elif class_conflict:
        decision = "quarantine_conflict"
        tier = None
        rationale = f"Observed functional classes {observed_classes} do not uniquely support {proposed_class}."
    elif primary:
        decision = f"accept_{proposed_class}"
        tier = "tier_1"
        rationale = (
            f"{len(primary)} qualifying activity row(s) link an explicit human A2A functional "
            f"{proposed_class} direction to {len(primary_documents)} traceable primary publication(s)."
        )
    elif qualifying:
        decision = "needs_full_text"
        tier = None
        rationale = "Functional evidence passed target/context checks, but no qualifying primary publication was established."
    elif binding_only:
        decision = "reject_binding_only"
        tier = None
        rationale = "Available evidence is binding-only and cannot establish agonist-versus-antagonist function."
    elif context_failures:
        decision = "reject_context"
        tier = None
        rationale = "No evidence row passed the target, organism, confidence, readout, and class-direction checks."
    else:
        decision = "needs_full_text"
        tier = None
        rationale = "No classifiable evidence was available."

    representative = primary[0] if primary else qualifying[0] if qualifying else None
    source = representative or {
        "activity": packet_row["functional_evidence"][0],
        "assay": assays[packet_row["functional_evidence"][0]["assay_chembl_id"]],
        "document": documents[packet_row["functional_evidence"][0]["document_chembl_id"]],
    }
    accepted = decision in {"accept_agonist", "accept_antagonist"}
    return {
        "chembl_id": plan_row["chembl_id"],
        "molecule_name": plan_row["molecule_name"],
        "curation_batch": int(plan_row["curation_batch"]),
        "proposed_class": proposed_class,
        "decision": decision,
        "functional_class": proposed_class if accepted else "unknown",
        "primary_binary_label": (1 if proposed_class == "agonist" else 0) if accepted else None,
        "evidence_tier": tier,
        "dataset_admission_eligible": accepted,
        "primary_analysis_eligible": accepted and tier == "tier_1",
        "training_eligible": False,
        "training_blocker": "scaffold partition and locked-holdout manifest must be rebuilt and hashed",
        "curation_mode": "machine_curated_computational_audit",
        "decision_engine": "deterministic_evidence_rules",
        "human_validation_claimed": False,
        "human_approval_required": False,
        "decision_rationale": rationale,
        "observed_functional_classes": observed_classes,
        "excluded_functional_classes": excluded_classes,
        "excluded_function_evidence": excluded_evidence,
        "functional_activity_rows": len(packet_row["functional_evidence"]),
        "qualifying_activity_rows": len(qualifying),
        "qualifying_assays": qualifying_assays,
        "primary_source_documents": primary_documents,
        "representative_activity_id": source["activity"].get("activity_id"),
        "representative_assay_id": source["assay"].get("assay_chembl_id"),
        "representative_document_id": source["document"].get("document_chembl_id"),
        "representative_source_url": evidence_url(source["document"], source["assay"]),
        "representative_evidence_passage": source["activity"].get("description"),
        "context_failures": context_failures,
        "audited_at_utc": utc_now(),
        "ruleset_version": config["specification_id"],
    }


def write_csv(path, rows):
    scalar_fields = [
        "chembl_id", "molecule_name", "curation_batch", "proposed_class", "decision",
        "functional_class", "primary_binary_label", "evidence_tier",
        "dataset_admission_eligible", "primary_analysis_eligible", "training_eligible",
        "curation_mode", "decision_engine", "human_validation_claimed",
        "human_approval_required", "decision_rationale", "functional_activity_rows",
        "qualifying_activity_rows", "representative_activity_id", "representative_assay_id",
        "representative_document_id", "representative_source_url",
        "representative_evidence_passage", "audited_at_utc", "ruleset_version",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=scalar_fields)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in scalar_fields} for row in rows)


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    raw_activity_paths = [Path(path) for path in sorted(glob.glob(str(RAW_ACTIVITIES)))]
    with PLAN.open(newline="", encoding="utf-8") as handle:
        plan = list(csv.DictReader(handle))
    packet = {row["chembl_id"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["records"]}
    structures = {row["chembl_id"]: row for row in json.loads(STANDARDIZED.read_text(encoding="utf-8"))["records"]}
    if len(plan) != 220 or len({row["chembl_id"] for row in plan}) != len(plan):
        raise RuntimeError("The frozen 220-record plan is missing records or contains duplicate identifiers.")
    excluded_evidence = load_excluded_function_evidence({row["chembl_id"] for row in plan}, config)

    plan_evidence = [item for row in plan for item in packet[row["chembl_id"]]["functional_evidence"]]
    assay_ids = sorted({row["assay_chembl_id"] for row in plan_evidence})
    document_ids = sorted({row["document_chembl_id"] for row in plan_evidence})
    assays = {key: load_cached_summary("assay", key) for key in assay_ids}
    documents = {key: load_cached_summary("document", key) for key in document_ids}
    decisions = [
        adjudicate_record(
            row,
            packet[row["chembl_id"]],
            assays,
            documents,
            config,
            excluded_evidence.get(row["chembl_id"]),
        )
        for row in plan
    ]
    accepted = [row for row in decisions if row["dataset_admission_eligible"]]

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    OUTPUT_JSON.write_text(json.dumps({
        "schema_version": 1,
        "created_at": generated_at,
        "specification_id": config["specification_id"],
        "review_type": "machine-curated computational evidence audit",
        "human_validation_claimed": False,
        "record_count": len(decisions),
        "records": decisions,
    }, indent=2) + "\n", encoding="utf-8")
    write_csv(OUTPUT_CSV, decisions)

    benchmark_records = []
    for decision in accepted:
        structure = structures[decision["chembl_id"]]
        benchmark_records.append({
            **structure,
            "dataset_partition": "computationally_curated_unpartitioned",
            "functional_class": decision["functional_class"],
            "primary_binary_label": decision["primary_binary_label"],
            "evidence_status": "computationally_adjudicated_functional",
            "evidence_tier": decision["evidence_tier"],
            "primary_analysis_eligible": decision["primary_analysis_eligible"],
            "curation_mode": decision["curation_mode"],
            "decision_engine": decision["decision_engine"],
            "human_validation_claimed": False,
            "evidence_source_url": decision["representative_source_url"],
            "evidence_passage": decision["representative_evidence_passage"],
            "decision_rationale": decision["decision_rationale"],
            "training_eligible": False,
            "training_blocker": decision["training_blocker"],
        })
    BENCHMARK.write_text(json.dumps({
        "schema_version": 1,
        "created_at": generated_at,
        "specification_id": config["specification_id"],
        "dataset_partition": "computationally_curated_unpartitioned",
        "human_validation_claimed": False,
        "training_eligible_count": 0,
        "records": benchmark_records,
    }, indent=2) + "\n", encoding="utf-8")

    decision_counts = Counter(row["decision"] for row in decisions)
    accepted_class_counts = Counter(row["functional_class"] for row in accepted)
    audit = {
        "created_at": generated_at,
        "specification_id": config["specification_id"],
        "amendment_status": config["status"],
        "source_hashes": {
            "config": sha256(CONFIG),
            "frozen_plan_v1.2": sha256(PLAN),
            "evidence_packet": sha256(PACKET),
            "standardized_structures": sha256(STANDARDIZED),
            "raw_activity_snapshot": sha256_many(raw_activity_paths),
        },
        "plan_record_count": len(plan),
        "decision_record_count": len(decisions),
        "decision_counts": dict(sorted(decision_counts.items())),
        "accepted_record_count": len(accepted),
        "accepted_class_counts": dict(sorted(accepted_class_counts.items())),
        "quarantined_or_rejected_count": len(decisions) - len(accepted),
        "raw_excluded_function_record_count": len(excluded_evidence),
        "raw_excluded_function_classes": dict(sorted(Counter(
            evidence["functional_class"]
            for rows in excluded_evidence.values()
            for evidence in rows
        ).items())),
        "human_approval_required": False,
        "human_validation_claimed": False,
        "label_admission_uses_auc": False,
        "label_admission_uses_scaffold_agreement": False,
        "training_eligible_count": 0,
        "next_gate": "rebuild and hash scaffold-separated development and untouched holdout manifests from accepted computational labels",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
