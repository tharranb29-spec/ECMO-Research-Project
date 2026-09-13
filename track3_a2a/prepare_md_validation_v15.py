#!/usr/bin/env python3

"""Create the v1.5 MD input manifest and enforce the pre-production gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "md_validation.v1.5.json"
CANDIDATES = ROOT / "outputs" / "v1.4" / "external_cohort" / "literature_pilot_2025" / "eligible_candidates.csv"
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "outputs" / "v1.5" / "md"
STRUCTURE_REVIEW = OUTPUT / "5g53_chirality_review.json"
ENVIRONMENT_AUDIT = OUTPUT / "environment_audit.json"
CONSTRUCT_POLICY = ROOT / "config" / "md_construct_policy.v1.5.json"
BUILDER_AUDIT = OUTPUT / "builder_inputs" / "builder_input_audit.json"
CGENFF_REQUESTS = OUTPUT / "cgenff_requests" / "request_manifest.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_json_if_present(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    structure_review = read_json_if_present(STRUCTURE_REVIEW)
    environment_audit = read_json_if_present(ENVIRONMENT_AUDIT)
    builder_audit = read_json_if_present(BUILDER_AUDIT)
    cgenff_requests = read_json_if_present(CGENFF_REQUESTS)
    candidates = {row["record_id"]: row for row in read_csv(CANDIDATES)}
    declared = config["tiers"]["tier_b_blinded_candidates"]["candidate_ids"]
    if set(declared) != set(candidates):
        raise RuntimeError("Tier B IDs do not exactly match the frozen eligible-candidate file")

    systems = []
    for control in config["tiers"]["tier_a_controls"]:
        pdb_path = RAW / f"{control['pdb_id']}.pdb"
        systems.append({
            "system_id": control["system_id"],
            "tier": "A",
            "candidate_id": "",
            "receptor_pdb_id": control["pdb_id"],
            "receptor_state": control["receptor_state"],
            "ligand": control["ligand"],
            "standardized_smiles": "",
            "source_pose_required": "native_deposited_pose",
            "source_pose_path": str(pdb_path.relative_to(ROOT)) if pdb_path.exists() else "",
            "input_status": "present_unprepared" if pdb_path.exists() else "missing_receptor_structure",
            "input_sha256": sha256(pdb_path) if pdb_path.exists() else "",
            "replicas": config["simulation"]["replicas"],
            "production_ns_per_replica": config["simulation"]["production_ns_per_replica"],
        })
    for candidate_id in declared:
        row = candidates[candidate_id]
        for pdb_id in config["tiers"]["tier_b_blinded_candidates"]["receptor_structures"]:
            pose_path = ROOT / "outputs" / "v1.4" / "docking" / candidate_id / pdb_id / "retained_pose.sdf"
            systems.append({
                "system_id": f"{candidate_id}_{pdb_id}",
                "tier": "B",
                "candidate_id": candidate_id,
                "receptor_pdb_id": pdb_id,
                "receptor_state": "inactive" if pdb_id == "5NM4" else "active_like",
                "ligand": row["molecule_name"],
                "standardized_smiles": row["standardized_smiles"],
                "source_pose_required": "predeclared_retained_gnina_pose",
                "source_pose_path": str(pose_path.relative_to(ROOT)) if pose_path.exists() else "",
                "input_status": "present_unprepared" if pose_path.exists() else "missing_frozen_docking_pose",
                "input_sha256": sha256(pose_path) if pose_path.exists() else "",
                "replicas": config["simulation"]["replicas"],
                "production_ns_per_replica": config["simulation"]["production_ns_per_replica"],
            })

    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / "system_input_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(systems[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(systems)

    blockers = []
    for system in systems:
        if system["input_status"].startswith("missing"):
            blockers.append({"system_id": system["system_id"], "reason": system["input_status"]})
        elif system["tier"] == "A" and system["source_pose_path"]:
            pdb_path = ROOT / system["source_pose_path"]
            caveats = [line.strip() for line in pdb_path.read_text(errors="replace").splitlines() if line.startswith("CAVEAT")]
            review_resolves_caveat = (
                structure_review.get("source", {}).get("sha256") == sha256(pdb_path)
                and structure_review.get("decision", {}).get("status") == "resolved_by_copy_selection"
                and structure_review.get("decision", {}).get("selected_receptor_chain") == "B"
                and structure_review.get("decision", {}).get("selected_mini_gs_chain") == "D"
                and structure_review.get("decision", {}).get("deposited_coordinate_edit_performed") is False
            )
            if caveats and not review_resolves_caveat:
                blockers.append({
                    "system_id": system["system_id"],
                    "reason": "deposited_structure_caveat_requires_manual_review",
                    "details": caveats,
                })
    environment_ready = (
        environment_audit.get("status") == "openmm_and_core_force_fields_audited"
        and environment_audit.get("runtime", {}).get("openmm") == "8.6"
        and all(environment_audit.get("force_field", {}).get("required_template_status", {}).values())
    )
    if not environment_ready:
        blockers.append({"system_id": "global", "reason": "openmm_and_core_force_fields_not_audited"})
    gdp_transfer = next((system.get("gdp_transfer", {}) for system in builder_audit.get("systems", [])
                         if system.get("system_id") == "5G53_NECA_miniGs_native"), {})
    if builder_audit.get("status") != "tier_a_builder_inputs_audited_not_simulation_ready":
        blockers.append({"system_id": "global", "reason": "tier_a_builder_inputs_not_prepared_or_audited"})
    if gdp_transfer and not gdp_transfer.get("passed"):
        blockers.append({
            "system_id": "5G53_NECA_miniGs_native",
            "reason": "transferred_gdp_clash_requires_manual_resolution",
            "minimum_heavy_atom_distance_angstrom": gdp_transfer.get(
                "minimum_transferred_gdp_heavy_atom_distance_angstrom"
            ),
            "closest_pair": gdp_transfer.get("closest_pair"),
        })
    blockers.extend([
        {"system_id": "global", "reason": "tier_a_completed_construct_models_not_audited"},
        {"system_id": "global", "reason": "cgenff_ligand_parameters_not_generated_or_audited"},
        {"system_id": "global", "reason": "membrane_systems_not_built"},
        {"system_id": "global", "reason": "native_contact_lists_not_frozen"},
    ])
    status = {
        "schema_version": 1,
        "created_at": utc_now(),
        "specification_id": config["specification_id"],
        "status": "blocked_before_system_preparation" if blockers else "ready_for_system_preparation",
        "trajectory_production_started": False,
        "candidate_labels_loaded": False,
        "resolved_gates": {
            "5g53_chirality_caveat": structure_review.get("decision", {}).get("status") == "resolved_by_copy_selection",
            "openmm_and_core_force_fields": environment_ready,
            "tier_a_builder_inputs": builder_audit.get("status") == "tier_a_builder_inputs_audited_not_simulation_ready",
            "cgenff_request_inputs": cgenff_requests.get("status") == "request_inputs_ready_parameters_pending",
        },
        "compute_warnings": [
            environment_audit.get("production_compute_status")
        ] if environment_ready and environment_audit.get("production_compute_status") != "accelerator_available" else [],
        "tier_a_system_count": 2,
        "tier_b_system_count": 8,
        "planned_tier_a_plus_b_replicas": 30,
        "planned_tier_a_plus_b_sampling_microseconds": 3.0,
        "source_hashes": {
            "md_config": sha256(CONFIG),
            "candidate_manifest": sha256(CANDIDATES),
            "system_input_manifest": sha256(manifest_path),
            "md_construct_policy": sha256(CONSTRUCT_POLICY),
            **({"5g53_chirality_review": sha256(STRUCTURE_REVIEW)} if STRUCTURE_REVIEW.exists() else {}),
            **({"md_environment_audit": sha256(ENVIRONMENT_AUDIT)} if ENVIRONMENT_AUDIT.exists() else {}),
            **({"tier_a_builder_audit": sha256(BUILDER_AUDIT)} if BUILDER_AUDIT.exists() else {}),
            **({"cgenff_request_manifest": sha256(CGENFF_REQUESTS)} if CGENFF_REQUESTS.exists() else {}),
        },
        "blockers": blockers,
        "next_gate": "Resolve every listed blocker, build both native controls, and freeze native contacts before any production trajectory.",
    }
    status_path = args.output / "preflight_status.json"
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
