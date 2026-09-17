#!/usr/bin/env python3
"""Build the static Track 3 dashboard from audited repository artifacts.

The builder deliberately does not read sealed outcome fields and does not perform
model promotion. It projects auditable source records into the v1 dashboard
contracts and emits a deterministic, hash-chained audit log.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
A2A = ROOT / "track3_a2a"
OUTPUT = A2A / "outputs" / "dashboard" / "v1" / "contracts.json"
JS_OUTPUT = ROOT / "track3-dashboard-data.js"
CONTRACT_VERSION = "1.0.0"
SCHEMA_BASE = "a2a-dashboard"


SOURCES = {
    "implementation": A2A / "outputs/v1.6/implementation_status.json",
    "freeze": A2A / "outputs/v1.6/protocol_freeze_manifest.json",
    "models": A2A / "outputs/v1.6/model_reproduction/development_results.json",
    "evidence": A2A / "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
    "pubmed": A2A / "outputs/v1.6/external_evidence/pubmed_retrieval_audit.json",
    "pmc": A2A / "outputs/v1.6/external_evidence/pmc_fulltext_retrieval_audit.json",
    "docking": A2A / "outputs/v1.4/docking/literature_pilot_2025_report.json",
    "md": A2A / "outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json",
    "md_plan": A2A / "outputs/v1.5/md/preflight_status.json",
    "shadow_config": A2A / "config/shadow_update.v1.4.json",
    "shadow_status": A2A / "outputs/v1.4/shadow_update_status.json",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_ref(key: str) -> dict:
    path = SOURCES[key]
    return {"path": str(path.relative_to(A2A)), "sha256": sha256(path)}


def envelope(contract: str, records: list[dict]) -> dict:
    return {
        "schema_id": f"{SCHEMA_BASE}.{contract}.v1",
        "contract_version": CONTRACT_VERSION,
        "records": records,
    }


def build() -> dict:
    data = {key: read_json(path) for key, path in SOURCES.items()}
    implementation = data["implementation"]
    model_report = data["models"]
    model_result = model_report["result"]
    evidence = data["evidence"]
    docking = data["docking"]
    md = data["md"]
    md_plan = data["md_plan"]
    shadow = data["shadow_status"]

    evidence_records = []
    evidence_labels = {
        "metadata_pass_fulltext_ready": ("Full text ready", "review"),
        "metadata_pass_needs_fulltext": ("Needs source text", "review"),
        "metadata_pass_requires_endpoint_resolution": ("Endpoint resolution", "review"),
        "metadata_pass_doi_only_needs_source_retrieval": ("DOI-only retrieval", "review"),
        "quarantine_nonprimary_source": ("Non-primary source", "quarantined"),
        "quarantine_target_not_supported": ("A2A not supported", "quarantined"),
    }
    for status, count in evidence["status_counts"].items():
        title, disposition = evidence_labels.get(status, (status.replace("_", " "), "review"))
        evidence_records.append({
            "record_id": f"evidence-lane:{status}",
            "title": title,
            "count": count,
            "status": status,
            "disposition": disposition,
            "outcome_fields_loaded": evidence["outcome_fields_loaded"],
            "membership_frozen": False,
            "source": source_ref("evidence"),
        })

    molecules = []
    docking_records = []
    portfolio = []
    for candidate in docking["results"]:
        candidate_id = candidate["candidate_id"]
        states = candidate["receptors"]
        molecules.append({
            "molecule_id": candidate_id,
            "display_name": candidate_id.replace("LIT25-", ""),
            "registry_version": "prospective-literature-pilot-v1.4",
            "role": "label-blind prospective candidate",
            "identity_status": "structure prepared",
            "functional_label_blinded": candidate.get("functional_label_blinded", True),
            "training_eligible": False,
            "source": source_ref("docking"),
        })
        state_values = {}
        for receptor_id, receptor in states.items():
            state_name = "inactive" if receptor_id == "5NM4" else "active-like"
            record = {
                "docking_id": f"{candidate_id}:{receptor_id}",
                "molecule_id": candidate_id,
                "receptor_id": receptor_id,
                "receptor_state": state_name,
                "status": receptor["status"],
                "valid_seed_count": receptor["valid_seed_count"],
                "median_affinity_kcal_mol": receptor["median_affinity_kcal_mol"],
                "median_cnn_score": receptor["median_cnn_score"],
                "retained_pose_sha256": receptor["retained_pose"]["sha256"],
                "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
                "source": source_ref("docking"),
            }
            docking_records.append(record)
            state_values[receptor_id] = record
        inactive = state_values["5NM4"]
        active = state_values["2YDO"]
        delta = active["median_affinity_kcal_mol"] - inactive["median_affinity_kcal_mol"]
        portfolio.append({
            "portfolio_id": f"portfolio:{candidate_id}",
            "molecule_id": candidate_id,
            "status": "computationally_prioritized",
            "label_status": "blinded",
            "promotion_status": "shadow_proposal",
            "dual_state_complete": all(item["status"] == "valid" for item in state_values.values()),
            "d_affinity_kcal_mol": round(delta, 4),
            "md_status": "tier_b_locked",
            "next_gate": "External potency confirmation and Tier A control production must pass before any promotion.",
            "source": source_ref("docking"),
        })

    model_records = []
    for model_id, metrics in model_result["metrics"].items():
        mapping = model_report["model_mapping"][model_id]
        display = mapping if isinstance(mapping, str) else mapping.get("name", model_id)
        model_records.append({
            "model_id": model_id,
            "display_name": display,
            "endpoint": model_report["endpoint"],
            "role": "primary external predictor" if model_id == "AB_Ridge" else "development comparator",
            "lifecycle_status": "candidate_not_served",
            "development_n": model_result["n"],
            "scaffold_count": model_result["scaffold_count"],
            "r2": metrics["r2"],
            "rmse": metrics["rmse"],
            "external_outcomes_loaded": model_report["external_outcomes_loaded"],
            "promotion_allowed": False,
            "source": source_ref("models"),
        })

    applicability = model_result["applicability_domain"]
    ridge_interval = model_result["uncertainty"]["model_intervals"]["AB_Ridge"]["r2"]
    applicability_records = [{
        "assessment_id": "pBind_Ki:AB_Ridge:development-v1.6",
        "model_id": "AB_Ridge",
        "scope": "development grouped out-of-fold predictions",
        "similarity_threshold": applicability["similarity_threshold"],
        "descriptor_distance_threshold": applicability["descriptor_distance_threshold"],
        "inside_n": applicability["inside_n"],
        "outside_n": applicability["outside_n"],
        "r2_interval": ridge_interval,
        "calibration_warning": "Empirical interval coverage is development-only and is not an external calibration claim.",
        "external_thresholds_frozen": False,
        "source": source_ref("models"),
    }]

    md_records = [{
        "gate_id": "G7:tier-a-equilibration",
        "specification_id": md["specification_id"],
        "status": md["status"],
        "observed_runs": md["observed_run_count"],
        "passed_runs": md["passed_run_count"],
        "required_runs": md["expected_run_count"],
        "missing_audits": md["missing_audits"],
        "tier_a_production_unlocked": md["tier_a_production_unlocked"],
        "tier_b_unlocked": md["tier_b_unlocked"],
        "claim_limit": md["claim_limit"],
        "source": source_ref("md"),
    }, {
        "gate_id": "G8:candidate-md",
        "specification_id": md["specification_id"],
        "status": "locked",
        "observed_runs": 0,
        "passed_runs": 0,
        "required_runs": md_plan["tier_b_system_count"] * 3,
        "missing_audits": [],
        "tier_a_production_unlocked": md["tier_a_production_unlocked"],
        "tier_b_unlocked": md["tier_b_unlocked"],
        "claim_limit": "Candidate MD cannot start until both Tier A native controls pass the frozen production rule.",
        "source": source_ref("md_plan"),
    }]

    promotion = {
        "mode": data["shadow_config"]["mode"],
        "served_model": shadow["served_track3_model"],
        "candidate_model": shadow["candidate_model"],
        "external_gate_passed": shadow["external_gate_passed"],
        "human_release_approved": shadow["human_release_approved"],
        "automatic_model_replacement_enabled": shadow["automatic_model_replacement_enabled"],
        "permitted_label": data["shadow_config"]["ui_contract"]["prediction_label"],
        "prohibited_label": data["shadow_config"]["ui_contract"]["prohibited_label"],
        "source": source_ref("shadow_status"),
    }

    contracts = {
        "evidence_inbox": envelope("evidence-inbox", evidence_records),
        "molecule_registry": envelope("molecule-registry", molecules),
        "model_registry": envelope("model-registry", model_records),
        "applicability_uncertainty": envelope("applicability-uncertainty", applicability_records),
        "dual_state_docking": envelope("dual-state-docking", docking_records),
        "md_gates": envelope("md-gates", md_records),
        "candidate_portfolio": envelope("candidate-portfolio", portfolio),
    }

    audit_events = [
        ("protocol-freeze", "protocol", data["freeze"]["specification_id"], "freeze"),
        ("evidence-pass1", "evidence_inbox", "external-pass-1", "evidence"),
        ("model-reproduction", "model_registry", "pBind_Ki-development", "models"),
        ("prospective-docking", "dual_state_docking", docking["protocol_id"], "docking"),
        ("md-gate", "md_gates", md["specification_id"], "md"),
        ("shadow-policy", "promotion", data["shadow_config"]["specification_id"], "shadow_config"),
    ]
    previous = "GENESIS"
    ledger = []
    for index, (action, record_type, record_id, source_key) in enumerate(audit_events, start=1):
        item = {
            "sequence": index,
            "event_id": f"audit-{index:04d}",
            "actor": "repository-artifact-ingest",
            "action": action,
            "record_type": record_type,
            "record_id": record_id,
            "source": source_ref(source_key),
            "previous_entry_hash": previous,
        }
        item["entry_hash"] = canonical_hash(item)
        previous = item["entry_hash"]
        ledger.append(item)
    contracts["audit_log"] = envelope("audit-log", ledger)

    snapshot_time = implementation["created_at_utc"]
    return {
        "dashboard_contract_version": CONTRACT_VERSION,
        "snapshot_created_at_utc": snapshot_time,
        "project": {
            "short_title": "A2A Evidence Command Center",
            "title": "Evidence-Gated Dual-State Docking and Machine Learning for Functional Classification and Virtual Screening of A2A Adenosine Receptor Ligands",
            "target": "Human ADORA2A · CHEMBL251",
            "protocol": implementation["specification_id"],
            "deadline": implementation["deadline"],
            "claim_level": "Retrospective association plus limited prospective prioritization; no external or biological validation.",
        },
        "summary": {
            "evidence_queue": evidence["candidate_count"],
            "pass_2_required": evidence["pass_2_required_count"],
            "external_admitted": evidence["external_cohort_admitted_count"],
            "external_outcomes_loaded": evidence["outcome_fields_loaded"],
            "primary_model": "AB_Ridge",
            "primary_model_r2": model_result["metrics"]["AB_Ridge"]["r2"],
            "docked_candidates": len(docking["results"]),
            "md_runs_passed": md["passed_run_count"],
            "md_runs_required": md["expected_run_count"],
            "tier_a_production_unlocked": md["tier_a_production_unlocked"],
            "tier_b_unlocked": md["tier_b_unlocked"],
            "promotion_mode": promotion["mode"],
        },
        "promotion": promotion,
        "contracts": contracts,
    }


def validate(payload: dict) -> None:
    expected = {
        "evidence_inbox", "molecule_registry", "model_registry",
        "applicability_uncertainty", "dual_state_docking", "md_gates",
        "candidate_portfolio", "audit_log",
    }
    if set(payload["contracts"]) != expected:
        raise ValueError("Dashboard contract set is incomplete")
    for name, contract in payload["contracts"].items():
        if contract["contract_version"] != CONTRACT_VERSION or not isinstance(contract["records"], list):
            raise ValueError(f"Invalid envelope for {name}")
    if payload["promotion"]["mode"] != "shadow_only":
        raise ValueError("Autonomous dashboard may only emit shadow proposals")
    if payload["promotion"]["served_model"] is not None:
        raise ValueError("No Track 3 model is authorized for serving")
    previous = "GENESIS"
    for entry in payload["contracts"]["audit_log"]["records"]:
        if entry["previous_entry_hash"] != previous:
            raise ValueError("Audit chain is discontinuous")
        recorded = entry["entry_hash"]
        unhashed = {key: value for key, value in entry.items() if key != "entry_hash"}
        if canonical_hash(unhashed) != recorded:
            raise ValueError("Audit entry hash mismatch")
        previous = recorded


def main() -> None:
    payload = build()
    validate(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    OUTPUT.write_text(serialized + "\n", encoding="utf-8")
    JS_OUTPUT.write_text(f"window.A2A_DASHBOARD_DATA = {serialized};\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {JS_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
