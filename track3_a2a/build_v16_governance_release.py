#!/usr/bin/env python3
"""Build and verify the deterministic Track 3 v1.6 governance release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6" / "governance"

INPUTS = {
    "protocol": "config/protocol.v1.6.json",
    "amendment": "V16_PROTOCOL_AMENDMENT.md",
    "freeze": "outputs/v1.6/protocol_freeze_manifest.json",
    "model": "outputs/v1.6/model_reproduction/development_results.json",
    "predictions": "outputs/v1.6/model_reproduction/development_oof_predictions.csv",
    "pass1": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
    "implementation": "outputs/v1.6/implementation_status.json",
    "equilibration": "outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(root: Path, key: str) -> dict[str, Any]:
    return json.loads((root / INPUTS[key]).read_text(encoding="utf-8"))


def check(check_id: str, passed: bool, evidence: str, failure: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "status": "pass" if passed else "fail",
        "evidence": evidence,
        "failure_message": "" if passed else failure,
    }


def freeze_signature(manifest: dict[str, Any]) -> str:
    payload = {key: value for key, value in manifest.items() if key != "computational_release_signature_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def evaluate_invariants(root: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    protocol = load_json(root, "protocol")
    freeze = load_json(root, "freeze")
    model = load_json(root, "model")
    pass1 = load_json(root, "pass1")
    implementation = load_json(root, "implementation")
    equilibration = load_json(root, "equilibration")
    primary = protocol["models"]["primary_external_predictor"]
    rf = protocol["models"]["chemistry_rf_comparator"]["parameters"]
    external = protocol["external_confirmation"]

    checks = [
        check("primary_endpoint_frozen", protocol["endpoints"]["primary"]["name"] == "pBind_Ki", protocol["endpoints"]["primary"]["name"], "Primary endpoint drifted from pBind_Ki."),
        check("primary_model_frozen", primary["name"] == "AB_Ridge" and primary["parameters"] == {"alpha": 1.0}, f"{primary['name']} {primary['parameters']}", "Primary predictor drifted from AB_Ridge(alpha=1.0)."),
        check("rf_comparator_frozen", rf == {"n_estimators": 500, "max_features": "sqrt", "min_samples_leaf": 1, "random_state": 20260914, "n_jobs": 1}, json.dumps(rf, sort_keys=True), "RF comparator drifted from 500/sqrt/1, seed 20260914, n_jobs=1."),
        check("outcome_firewall_declared", external["membership_freeze_before_outcome_join"] is True and external["one_time_outcome_join"] is True, external["outcome_firewall"], "Outcome-firewall contract is incomplete."),
        check("external_outcomes_not_loaded", model["external_outcomes_loaded"] is False and implementation["external_outcomes_joined"] is False and pass1["outcome_fields_loaded"] is False, "model=false; implementation=false; pass1=false", "An audited artifact indicates external outcomes were loaded or joined."),
        check("historical_holdout_not_reused", model["historical_locked_holdout_rows_used"] == 0, str(model["historical_locked_holdout_rows_used"]), "The historical locked holdout was reused."),
        check("external_membership_not_premature", pass1["external_cohort_admitted_count"] == 0 and "membership_not_frozen" in implementation["workstreams"]["B_external_confirmation"]["status"], implementation["workstreams"]["B_external_confirmation"]["status"], "External membership was admitted or represented as frozen before pass 2."),
        check("model_promotion_prohibited", model["promotion_allowed"] is False and protocol["release"]["automatic_model_replacement"] is False, "development promotion=false; automatic replacement=false", "Model promotion is allowed before the external gate."),
        check("model_mapping_matches_protocol", model["model_mapping"]["AB_Ridge"] == primary and model["model_mapping"]["AB_RF"] == protocol["models"]["chemistry_rf_comparator"] and model["model_mapping"]["E_RF"] == protocol["models"]["docking_increment_comparator"], "development model mapping equals protocol", "Development model mapping does not match the frozen protocol."),
        check("prediction_hash_reconciles", model["prediction_sha256"] == sha256(root / model["prediction_file"]), model["prediction_sha256"], "Development prediction artifact hash mismatch."),
        check("freeze_signature_reconciles", freeze["computational_release_signature_sha256"] == freeze_signature(freeze), freeze["computational_release_signature_sha256"], "Protocol freeze signature mismatch."),
        check("tier_a_production_locked", equilibration["tier_a_production_unlocked"] is False, equilibration["status"], "Tier A production was unlocked without a complete equilibration gate."),
        check("tier_b_locked", equilibration["tier_b_unlocked"] is False, equilibration["status"], "Tier B was unlocked before the declared control gate."),
        check("no_best_replica_selection", equilibration["best_replica_selection"] == "prohibited", equilibration["best_replica_selection"], "Best-replica selection is no longer prohibited."),
    ]

    for relative, expected in freeze["files"].items():
        actual = sha256(root / relative)
        checks.append(check(f"freeze_file_hash:{relative}", actual == expected, actual, f"Frozen file hash mismatch: {relative}."))
    for relative, expected in implementation["artifact_hashes"].items():
        actual = sha256(root / relative)
        checks.append(check(f"status_artifact_hash:{relative}", actual == expected, actual, f"Implementation-status artifact hash mismatch: {relative}."))

    context = {
        "protocol": protocol,
        "freeze": freeze,
        "model": model,
        "pass1": pass1,
        "implementation": implementation,
        "equilibration": equilibration,
    }
    return checks, context


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_release(root: Path, output: Path) -> dict[str, Any]:
    checks, context = evaluate_invariants(root)
    failures = [item for item in checks if item["status"] != "pass"]
    if failures:
        detail = "; ".join(f"{item['check_id']}: {item['failure_message']}" for item in failures)
        raise RuntimeError(f"Governance release blocked: {detail}")

    output.mkdir(parents=True, exist_ok=True)
    checks_path = output / "governance_checks.csv"
    write_csv(checks_path, checks, ["check_id", "status", "evidence", "failure_message"])

    model = context["model"]
    metrics = model["result"]["metrics"]
    model_rows = []
    for model_id, governance_role in [
        ("Mean", "required_baseline"),
        ("AB_Ridge", "primary_external_predictor"),
        ("AB_RF", "chemistry_rf_comparator"),
        ("E_RF", "docking_increment_comparator"),
    ]:
        values = metrics[model_id]
        model_rows.append({
            "model_id": model_id,
            "governance_role": governance_role,
            "endpoint": "pBind_Ki",
            "development_n": model["result"]["n"],
            "generic_murcko_scaffolds": model["result"]["scaffold_count"],
            "r2": values["r2"],
            "rmse": values["rmse"],
            "mae": values["mae"],
            "spearman_rho": values["spearman_rho"],
            "claim_status": model["claim_status"],
            "external_confirmation_status": "not_run",
            "promotion_allowed": "false",
        })
    model_path = output / "model_evidence_table.csv"
    write_csv(model_path, model_rows, list(model_rows[0]))

    implementation = context["implementation"]
    equilibration = context["equilibration"]
    gate_rows = [
        {"gate_id": "A_protocol_and_governance", "status": "passed", "decision": "release governance evidence package", "next_required_action": "preserve frozen decisions through external evaluation"},
        {"gate_id": "B_external_membership", "status": "locked", "decision": "no cohort admitted", "next_required_action": "complete independent source-grounded pass 2 and freeze exact agreement cohort"},
        {"gate_id": "external_model_confirmation", "status": "not_run", "decision": "promotion prohibited", "next_required_action": "join outcomes once only after cohort, predictions, applicability thresholds, and hashes are frozen"},
        {"gate_id": "tier_a_production", "status": "locked", "decision": f"{equilibration['passed_run_count']}/{equilibration['expected_run_count']} equilibration audits passed", "next_required_action": "complete the missing prospectively declared equilibration replica and rebuild aggregate gate"},
        {"gate_id": "tier_b_candidate_md", "status": "locked", "decision": "both Tier A controls have not passed production rule", "next_required_action": "do not start Tier B"},
    ]
    gate_path = output / "gate_status_table.csv"
    write_csv(gate_path, gate_rows, ["gate_id", "status", "decision", "next_required_action"])

    inventory_rows = []
    roles = {
        "protocol": "machine-readable frozen authority",
        "amendment": "human-readable frozen authority",
        "freeze": "freeze signature and source hashes",
        "model": "development-only model evidence",
        "predictions": "reproducible development OOF predictions",
        "pass1": "label-blind external evidence preflight",
        "implementation": "cross-workstream audited status",
        "equilibration": "current MD lock authority",
    }
    for key, relative in INPUTS.items():
        path = root / relative
        inventory_rows.append({
            "artifact_id": key,
            "path": relative,
            "role": roles[key],
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        })
    inventory_path = output / "evidence_artifact_inventory.csv"
    write_csv(inventory_path, inventory_rows, ["artifact_id", "path", "role", "sha256", "bytes"])

    status = {
        "schema_version": 1,
        "specification_id": context["protocol"]["specification_id"],
        "deadline": context["protocol"]["competition_deadline"],
        "status": "governance_controls_passed_external_confirmation_pending",
        "all_governance_checks_passed": True,
        "governance_check_count": len(checks),
        "primary_endpoint": "pBind_Ki",
        "primary_external_predictor": "AB_Ridge(alpha=1.0)",
        "rf_comparators": "500/sqrt/1; seed=20260914; n_jobs=1",
        "external_outcome_firewall": "sealed",
        "external_membership_frozen": False,
        "external_confirmation_run": False,
        "model_promotion_allowed": False,
        "tier_a_production_unlocked": False,
        "tier_b_unlocked": False,
        "current_equilibration_progress": f"{equilibration['passed_run_count']}/{equilibration['expected_run_count']}",
        "claim_boundary": "Development metrics are not external confirmation; docking and MD cannot create labels or rescue a failed potency gate.",
        "implementation_status_source_sha256": sha256(root / INPUTS["implementation"]),
    }
    status_path = output / "governance_status.json"
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

    generated = [checks_path, model_path, gate_path, inventory_path, status_path]
    manifest = {
        "schema_version": 1,
        "specification_id": context["protocol"]["specification_id"],
        "release_id": "a2a-track3-v1.6-governance",
        "status": "verified",
        "source_artifacts": {row["path"]: row["sha256"] for row in inventory_rows},
        "release_artifacts": {path.name: sha256(path) for path in generated},
        "frozen_decisions": {
            "primary_endpoint": "pBind_Ki",
            "primary_external_predictor": "AB_Ridge(alpha=1.0)",
            "rf_comparators": "500/sqrt/1; seed=20260914; n_jobs=1",
            "outcome_firewall": "sealed",
            "retroactive_tuning": "prohibited",
        },
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["release_signature_sha256"] = hashlib.sha256(canonical).hexdigest()
    manifest_path = output / "governance_release_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="track3_a2a directory")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="release output directory")
    args = parser.parse_args()
    manifest = build_release(args.root.resolve(), args.output.resolve())
    print(json.dumps({"status": manifest["status"], "release_signature_sha256": manifest["release_signature_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
