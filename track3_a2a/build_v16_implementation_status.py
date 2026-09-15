#!/usr/bin/env python3
"""Build the machine-readable v1.6 workstream status from audited artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "v1.6" / "implementation_status.json"


def load(relative: str) -> tuple[dict, Path]:
    path = ROOT / relative
    return json.loads(path.read_text()), path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    freeze, freeze_path = load("outputs/v1.6/protocol_freeze_manifest.json")
    model, model_path = load("outputs/v1.6/model_reproduction/development_results.json")
    ligands, ligand_path = load("outputs/v1.6/md/ligand_bundles/campaign_manifest.json")
    pubmed, pubmed_path = load("outputs/v1.6/external_evidence/pubmed_retrieval_audit.json")
    pmc, pmc_path = load("outputs/v1.6/external_evidence/pmc_fulltext_retrieval_audit.json")
    pass1, pass1_path = load("outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json")
    constructs, constructs_path = load("outputs/v1.6/md/tier_a_constructs/construct_audit.json")
    minimized, minimized_path = load("outputs/v1.6/md/tier_a_constructs/minimized/minimization_audit.json")
    native_poses, native_poses_path = load("outputs/v1.6/md/native_control_ligands/native_pose_mapping_audit.json")
    membrane, membrane_path = load("outputs/v1.6/md/membrane_patch/patch_audit.json")
    membrane_relaxation, membrane_relaxation_path = load("outputs/v1.6/md/membrane_patch/patch_relaxation_audit.json")
    complexes, complexes_path = load("outputs/v1.6/md/tier_a_complex_preflight/complex_preflight_audit.json")
    periodic, periodic_path = load("outputs/v1.6/md/tier_a_periodic_systems/periodic_assembly_audit.json")
    smoke, smoke_path = load("outputs/v1.6/md/tier_a_smoke_tests/smoke_campaign_audit.json")
    releases, releases_path = load("outputs/v1.6/md/tier_a_release_bundles/campaign_manifest.json")
    equilibration_gate, equilibration_gate_path = load("outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json")
    equilibration_config_path = ROOT / "config" / "tier_a_equilibration.v1.6.json"
    metrics = model["result"]["metrics"]
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-track3-protocol-v1.6",
        "deadline": "2026-09-30",
        "external_outcomes_joined": False,
        "md_trajectory_production_started": False,
        "candidate_labels_loaded_for_md": False,
        "workstreams": {
            "A_protocol_and_governance": {
                "status": "exit_gate_passed",
                "freeze_signature": freeze["computational_release_signature_sha256"],
                "primary_endpoint": "pBind_Ki",
                "primary_model": "AB_Ridge",
                "rf_comparator": "500/sqrt/1",
                "development_reproduction": {
                    "n": model["result"]["n"],
                    "generic_murcko_scaffolds": model["result"]["scaffold_count"],
                    "r2": {name: values["r2"] for name, values in metrics.items()},
                },
            },
            "B_external_confirmation": {
                "status": "pass_1_complete_pass_2_pending_membership_not_frozen",
                "queue_candidates": 240,
                "pubmed_requested": pubmed["requested_pmid_count"],
                "pubmed_retrieved": pubmed["retrieved_article_count"],
                "pmc_requested": pmc["requested_pmcid_count"],
                "pmc_fulltext_retrieved": pmc["retrieved_fulltext_count"],
                "pmc_fulltext_unavailable": pmc["failed_fulltext_count"],
                "pass_1_status_counts": pass1["status_counts"],
                "pass_2_required_candidates": pass1["pass_2_required_count"],
                "external_cohort_admitted": pass1["external_cohort_admitted_count"],
                "next_gate": "independent source-grounded pass-2 extraction; freeze membership only after exact field agreement",
            },
            "C_open_md": {
                "status": "periodic_and_smoke_gates_passed_staged_equilibration_pending",
                "ambertools_image": ligands["image"],
                "ambertools_image_id": ligands["image_id"],
                "accepted_ligand_bundles": ligands["accepted_count"],
                "required_ligand_bundles": 6,
                "gdp_policy": "nucleotide-free selected 5G53 B/D mini-Gs control",
                "initial_construct_candidates_geometry_passed": constructs["geometry_pass_count"],
                "pre_membrane_minimized_constructs_passed": minimized["passed_count"],
                "native_control_pose_mappings_passed": native_poses["accepted_count"],
                "unsolvated_tier_a_complex_preflights_passed": complexes["accepted_count"],
                "mixed_membrane_patch_status": membrane["status"],
                "mixed_membrane_cholesterol_fraction": membrane["cholesterol_mole_fraction"],
                "relaxed_membrane_patch_status": membrane_relaxation["status"],
                "periodic_tier_a_systems_passed": periodic["passed_count"],
                "minimization_nvt_npt_smoke_systems_passed": smoke["passed_count"],
                "github_safe_release_bundles_passed": releases["accepted_count"],
                "tier_a_unlocked_for_staged_equilibration": True,
                "staged_equilibration_gate_status": equilibration_gate["status"],
                "staged_equilibration_runs_passed": equilibration_gate["passed_run_count"],
                "staged_equilibration_runs_required": equilibration_gate["expected_run_count"],
                "tier_a_production_unlocked": False,
                "tier_b_unlocked": False,
                "next_gate": "complete the frozen full-duration staged equilibration for both controls and all three seeds, then pass the aggregate equilibration gate before Tier A pilot production",
            },
            "D_dashboard": {
                "status": "scheduled_to_start_2026-09-16",
                "current_mode": "legacy_dashboard_preserved",
                "next_gate": "static versioned Track 3 evidence contracts before autonomous shadow-mode integration",
            },
        },
        "artifact_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in [
                freeze_path, model_path, ligand_path, pubmed_path, pmc_path, pass1_path,
                constructs_path, minimized_path, native_poses_path, membrane_path,
                membrane_relaxation_path, complexes_path, periodic_path, smoke_path,
                releases_path, equilibration_config_path, equilibration_gate_path,
            ]
        },
        "timeline_status": "ahead_of_September_18_20_periodic_system_milestone_equilibration_execution_pending",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
