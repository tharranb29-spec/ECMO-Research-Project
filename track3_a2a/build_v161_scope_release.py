#!/usr/bin/env python3
"""Build the deterministic Track 3 v1.6.1 competition-scope release."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6.1" / "governance"
SOURCES = {
    "scope": "config/competition_scope.v1.6.1.json",
    "amendment": "V16_1_COMPETITION_SCOPE_AMENDMENT.md",
    "builder": "build_v161_scope_release.py",
    "protocol": "config/protocol.v1.6.json",
    "protocol_freeze": "outputs/v1.6/protocol_freeze_manifest.json",
    "model": "outputs/v1.6/model_reproduction/development_results.json",
    "model_runner": "run_continuous_activity_v15.py",
    "external_freeze": "outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json",
    "implementation": "outputs/v1.6/implementation_status.json",
    "equilibration": "outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json",
    "md_production": "config/md_production.v1.6.json",
    "dashboard_contracts": "outputs/dashboard/v1/contracts.json",
    "dashboard_schema": "dashboard_contracts/v1/governance-scope.schema.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(root: Path, key: str) -> dict[str, Any]:
    return json.loads((root / SOURCES[key]).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_list_constant(path: Path, name: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            value = ast.literal_eval(node.value)
            require(isinstance(value, list) and all(isinstance(item, str) for item in value), f"{name} is not a string list.")
            return value
    raise RuntimeError(f"Missing frozen source constant: {name}.")


def validate_sources(root: Path) -> dict[str, Any]:
    scope = load_json(root, "scope")
    protocol = load_json(root, "protocol")
    model = load_json(root, "model")
    external = load_json(root, "external_freeze")
    implementation = load_json(root, "implementation")
    equilibration = load_json(root, "equilibration")
    md = load_json(root, "md_production")
    dashboard = load_json(root, "dashboard_contracts")

    frozen = scope["scientific_freeze"]
    model_runner = root / SOURCES["model_runner"]
    require(scope["status"].startswith("prospectively_frozen"), "Scope amendment is not prospective.")
    require(frozen["endpoint"]["name"] == protocol["endpoints"]["primary"]["name"] and frozen["endpoint"]["definition"] == protocol["endpoints"]["primary"]["definition"], "Endpoint definition drifted from v1.6.")
    require(frozen["features"]["AB"]["fingerprint"] == protocol["models"]["primary_external_predictor"]["features"].split(", plus frozen physicochemical descriptors")[0], "Fingerprint definition drifted.")
    require(frozen["features"]["AB"]["descriptors"] == source_list_constant(model_runner, "DESCRIPTORS"), "Descriptor features drifted.")
    require(frozen["features"]["E_additional_docking"] == protocol["models"]["docking_increment_comparator"]["additional_features"], "Docking features drifted.")
    require(frozen["features"]["E_additional_docking"] == source_list_constant(model_runner, "DOCKING"), "Docking implementation constants drifted.")
    require(frozen["estimators"]["AB_Ridge"]["parameters"] == protocol["models"]["primary_external_predictor"]["parameters"], "Ridge parameters drifted.")
    require(frozen["estimators"]["AB_RF"]["parameters"] == protocol["models"]["chemistry_rf_comparator"]["parameters"], "RF parameters drifted.")
    require(frozen["development_evaluation"]["folds"] == protocol["development_reproduction"]["folds"], "Fold count drifted.")
    require(frozen["development_evaluation"]["repeat_seeds"] == protocol["development_reproduction"]["repeat_seeds"], "Repeat seeds drifted.")
    require(frozen["development_evaluation"]["interval_method"] == model["result"]["interval_method"], "Development interval method drifted.")
    require(frozen["external_intervals"]["resamples"] == protocol["external_confirmation"]["bootstrap_resamples"], "External bootstrap count drifted.")
    require(frozen["external_intervals"]["random_seed"] == protocol["external_confirmation"]["random_seed"], "External bootstrap seed drifted.")
    require(model["model_mapping"]["AB_Ridge"] == protocol["models"]["primary_external_predictor"], "AB_Ridge mapping drifted.")
    require(model["model_mapping"]["AB_RF"] == protocol["models"]["chemistry_rf_comparator"], "AB_RF mapping drifted.")
    require(model["model_mapping"]["E_RF"] == protocol["models"]["docking_increment_comparator"], "E_RF mapping drifted.")
    require(model["model_mapping"]["Mean"] == protocol["models"]["required_baseline"], "Mean baseline mapping drifted.")
    require(frozen["model_mapping"] == {"Mean": "training-development mean pBind_Ki", "AB_Ridge": "primary external predictor", "AB_RF": "chemistry RF comparator", "E_RF": "chemistry plus docking RF comparator"}, "Scope model role mapping drifted.")

    firewall = scope["outcome_firewall"]
    require(firewall["status"] == "sealed" and model["external_outcomes_loaded"] is False, "Model outcome firewall is not sealed.")
    require(external["numeric_ki_extracted"] is False and external["external_outcomes_joined"] is False, "External outcomes were exposed.")
    require(external["one_time_outcome_join_authorized"] is False and implementation["external_outcomes_joined"] is False, "Outcome join was authorized or recorded.")

    floor = scope["external_confirmation_floor"]
    require((floor["minimum_molecules"], floor["minimum_generic_murcko_scaffolds"]) == (60, 20), "External confirmation floors drifted.")
    require(floor["unlabeled_review_queue_satisfies_floor"] is False, "Unlabeled queue cannot satisfy the confirmation floor.")
    require(external["minimum_floors_passed"] is False and external["admitted_molecule_count"] == 0 and external["admitted_generic_murcko_scaffold_count"] == 0, "Frozen external floor result drifted.")

    queue = scope["candidate_review_scope"]
    require(queue["per_position_candidate_ranking_defensible"] is False, "Per-position ranking must be prohibited.")
    require(queue["per_candidate_hit_probability_defensible"] is False, "Per-candidate hit probability must be prohibited.")
    require(queue["allowed_candidate_status"] == "screen_eligible_not_ruled_out", "Screen-eligible terminology drifted.")
    require(queue["prohibited_candidate_status"] == "certified_hit", "Certified-hit prohibition drifted.")
    require(queue["queue_count"]["authorized_count"] is None and queue["queue_count"]["fixed_count_authorized"] is False, "A fixed queue count was encoded without authority.")
    require(queue["interval_bound_selection_rule"] is None, "An interval-bound inclusion rule was encoded without authority.")

    require(equilibration["tier_a_production_unlocked"] is True and equilibration["passed_run_count"] == 6, "Tier A equilibration authority drifted.")
    require(not (root / "outputs/v1.6/md/tier_a_production/control_gate_report.json").exists(), "A Tier A production control gate now exists; issue a new scope status version.")
    require(scope["md_cutoff_policy"]["tier_b"]["status"] == "locked", "Tier B scope lock drifted.")
    require(implementation["workstreams"]["C_open_md"]["tier_b_unlocked"] is False, "Implementation status shows Tier B unlocked.")
    require(md["tier_b"]["trajectory_start_requires_tier_a_control_report"] is True, "Tier B start gate drifted.")

    autonomy = scope["dashboard_autonomy"]
    require(autonomy["mode"] == "shadow_only_evidence_orchestration", "Dashboard is not shadow-only.")
    require(dashboard["promotion"]["mode"] == "shadow_only" and dashboard["promotion"]["served_model"] is None, "Dashboard promotion state drifted.")
    require(dashboard["promotion"]["automatic_model_replacement_enabled"] is False, "Automatic model replacement is enabled.")

    return {
        "scope": scope,
        "protocol": protocol,
        "model": model,
        "external": external,
        "implementation": implementation,
        "equilibration": equilibration,
        "md": md,
        "dashboard": dashboard,
    }


def build_claim_matrix(scope: dict[str, Any]) -> dict[str, Any]:
    claims = [
        {
            "claim_id": "frozen_scientific_analysis",
            "disposition": "allowed_with_qualification",
            "authorized_language": "The v1.6 pBind_Ki analysis remains frozen and development-only.",
            "prohibited_language": "The modified scope refit, retuned, or externally confirmed the model.",
            "dashboard_behavior": "display frozen specification and source hashes",
        },
        {
            "claim_id": "human_review_queue",
            "disposition": "allowed_with_qualification",
            "authorized_language": "An uncertainty-aware, scaffold-composed set is available for human review.",
            "prohibited_language": "The queue is an externally confirmed cohort.",
            "dashboard_behavior": "display review bands and set composition without scientific rank numbers",
        },
        {
            "claim_id": "per_position_candidate_ranking",
            "disposition": "prohibited",
            "authorized_language": None,
            "prohibited_language": "Candidate position is a defensible potency, activity, or hit ranking.",
            "dashboard_behavior": "omit scientific rank and sortable hit-rank fields",
        },
        {
            "claim_id": "per_candidate_hit_probability",
            "disposition": "prohibited",
            "authorized_language": None,
            "prohibited_language": "A candidate has a calibrated probability of being a hit.",
            "dashboard_behavior": "omit hit_probability and success_probability fields",
        },
        {
            "claim_id": "screen_eligible_status",
            "disposition": "allowed_with_qualification",
            "authorized_language": "Screen-eligible / not ruled out by the declared label-blind checks.",
            "prohibited_language": "Certified hit, validated hit, confirmed active, or equivalent.",
            "dashboard_behavior": "use the exact screen-eligible / not ruled out label",
        },
        {
            "claim_id": "set_level_rates",
            "disposition": "allowed_with_qualification",
            "authorized_language": "Report only the authorized review-set composition rates.",
            "prohibited_language": "Hit rate, success probability, or certified-hit fraction.",
            "dashboard_behavior": "allowlist rates from the scope specification; reject all others",
        },
        {
            "claim_id": "fixed_queue_count_or_interval_bound",
            "disposition": "prohibited_without_new_audited_artifact",
            "authorized_language": None,
            "prohibited_language": "A fixed queue size or interval-bound inclusion rule is frozen.",
            "dashboard_behavior": "render no governed count and no interval-bound selection rule",
        },
        {
            "claim_id": "external_confirmation_floor",
            "disposition": "allowed_only_for_external_confirmation",
            "authorized_language": "The external confirmation floor is at least 60 molecules and 20 independent generic Murcko scaffolds; the frozen attempt failed it.",
            "prohibited_language": "An unlabeled review queue passes or contributes to the external confirmation floor.",
            "dashboard_behavior": "keep review-queue counts separate from external-cohort floor status",
        },
        {
            "claim_id": "tier_a_production",
            "disposition": "incomplete_at_cutoff_without_signed_control_gate",
            "authorized_language": "Tier A production is ongoing or staged but incomplete at cutoff.",
            "prohibited_language": "Tier A controls passed production or established stability.",
            "dashboard_behavior": "show incomplete until a new governed release verifies the signed six-run control gate",
        },
        {
            "claim_id": "tier_b",
            "disposition": "locked_not_submission_critical",
            "authorized_language": "Tier B remains locked and is not submission-critical.",
            "prohibited_language": "Tier B is unlocked, completed, or required for the competition claim.",
            "dashboard_behavior": "show locked and do not offer an unlock action",
        },
        {
            "claim_id": "dashboard_autonomy",
            "disposition": "shadow_only",
            "authorized_language": "The autonomous module orchestrates evidence in shadow mode.",
            "prohibited_language": "The dashboard automatically validates science, changes protocol, promotes models, unseals outcomes, or unlocks MD.",
            "dashboard_behavior": "ingest additive shadow proposals only; all scientific state transitions remain disabled",
        },
    ]
    return {
        "schema_version": 1,
        "specification_id": scope["specification_id"],
        "claim_matrix_version": "1.0.0",
        "claims": claims,
    }


def build_dashboard_contract(scope: dict[str, Any], source_hash: str) -> dict[str, Any]:
    queue = scope["candidate_review_scope"]
    return {
        "contract_version": "1.1.0",
        "scope_specification_id": scope["specification_id"],
        "claim_matrix_path": "outputs/v1.6.1/governance/claim_matrix.json",
        "candidate_review": {
            "mode": "human_review_queue",
            "display_label": "screen-eligible / not ruled out",
            "scientific_rank_allowed": False,
            "candidate_probability_allowed": False,
            "fixed_queue_count": None,
            "interval_bound_rule": None,
            "allowed_set_level_rates": queue["allowed_set_level_rates"],
            "prohibited_fields": [
                "scientific_rank",
                "hit_probability",
                "success_probability",
                "certified_hit",
                "predicted_hit",
                "interval_bound_selected",
            ],
        },
        "external_confirmation": {
            "minimum_molecules": 60,
            "minimum_scaffolds": 20,
            "queue_can_satisfy_floor": False,
            "outcomes_sealed": True,
            "confirmation_passed": False,
        },
        "md_cutoff": {
            "tier_a_status": "incomplete_at_cutoff_without_signed_control_gate",
            "tier_a_completion_claim_allowed": False,
            "tier_b_status": "locked",
            "tier_b_submission_critical": False,
        },
        "autonomy": {
            "mode": "shadow_only_evidence_orchestration",
            "automatic_scientific_validation": False,
            "protocol_change": False,
            "model_promotion": False,
            "outcome_unsealing": False,
            "md_unlock": False,
        },
        "source": {"path": SOURCES["scope"], "sha256": source_hash},
    }


def build_release(root: Path, output: Path) -> dict[str, Any]:
    context = validate_sources(root)
    scope = context["scope"]
    output.mkdir(parents=True, exist_ok=True)

    claim_matrix = build_claim_matrix(scope)
    claim_path = output / "claim_matrix.json"
    claim_path.write_text(json.dumps(claim_matrix, indent=2) + "\n", encoding="utf-8")

    scope_hash = sha256(root / SOURCES["scope"])
    dashboard_contract = build_dashboard_contract(scope, scope_hash)
    dashboard_path = output / "dashboard_scope_contract.json"
    dashboard_path.write_text(json.dumps(dashboard_contract, indent=2) + "\n", encoding="utf-8")

    status = {
        "schema_version": 1,
        "specification_id": scope["specification_id"],
        "status": "scope_frozen_claims_narrowed",
        "competition_cutoff": scope["competition_cutoff"],
        "outcome_firewall": "sealed",
        "external_confirmation": "frozen_floor_failure_not_reopened",
        "review_queue": "uncertainty_aware_scaffold_composed_human_review_only",
        "candidate_level_scientific_ranking": "prohibited",
        "candidate_hit_probability": "prohibited",
        "candidate_status": "screen_eligible_not_ruled_out",
        "certified_hit_claim": "prohibited",
        "fixed_queue_count": None,
        "interval_bound_selection_rule": None,
        "tier_a_production": "incomplete_at_cutoff_without_signed_control_gate",
        "tier_b": "locked_not_submission_critical",
        "dashboard_autonomy": "shadow_only_evidence_orchestration",
    }
    status_path = output / "scope_status.json"
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

    source_hashes = {relative: sha256(root / relative) for relative in SOURCES.values()}
    release_hashes = {
        path.name: sha256(path)
        for path in [claim_path, dashboard_path, status_path]
    }
    manifest = {
        "schema_version": 1,
        "specification_id": scope["specification_id"],
        "release_id": "a2a-track3-v1.6.1-scope-governance",
        "status": "prospectively_frozen_and_verified",
        "source_artifacts": source_hashes,
        "release_artifacts": release_hashes,
        "immutable_scientific_parent": context["protocol"]["specification_id"],
        "outcomes_sealed": True,
    }
    manifest["release_signature_sha256"] = canonical_hash(manifest)
    manifest_path = output / "scope_release_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_release(args.root.resolve(), args.output.resolve())
    print(json.dumps({"status": manifest["status"], "release_signature_sha256": manifest["release_signature_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
