#!/usr/bin/env python3
"""Create a label-blind Tier B build queue without constructing system bundles."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from md_readiness_v16 import (
    DEFAULT_EQUILIBRATION_ROOT,
    GateError,
    PRODUCTION_CONFIG,
    atomic_json,
    load_json,
    sha256,
    verify_equilibration_gate,
    verify_tier_a_control_gate,
)


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "tier_b_build.v1.6.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_b_preflight" / "build_preflight.json"


def _accepted_construct(path: Path, audit_path: Path, receptor_id: str) -> tuple[bool, list[str]]:
    blockers = []
    if not path.is_file():
        blockers.append("accepted_receptor_construct_missing")
    if not audit_path.is_file():
        blockers.append("accepted_receptor_audit_missing")
        return False, blockers
    audit = load_json(audit_path)
    if audit.get("candidate_labels_loaded") is not False:
        blockers.append("receptor_audit_label_firewall_not_explicit")
    if receptor_id == "5NM4":
        rows = [row for row in audit.get("systems", []) if row.get("system_id") == "5NM4_ZMA_native"]
        if len(rows) != 1 or rows[0].get("status") != "minimized_construct_gate_passed":
            blockers.append("accepted_receptor_audit_not_passed")
        elif path.is_file() and sha256(path) != rows[0].get("output_sha256"):
            blockers.append("accepted_receptor_hash_mismatch")
    else:
        if audit.get("receptor_id") != receptor_id or audit.get("status") != "accepted_for_tier_b_build":
            blockers.append("accepted_receptor_audit_not_passed")
        elif path.is_file() and sha256(path) != audit.get("construct_sha256"):
            blockers.append("accepted_receptor_hash_mismatch")
    return not blockers, blockers


def build_preflight(control_gate: Path | None = None) -> dict:
    config = load_json(CONFIG_PATH)
    production = load_json(PRODUCTION_CONFIG)
    authority_path = ROOT / config["retained_pose_authority"]
    authority = load_json(authority_path)
    if authority.get("candidate_labels_loaded") is not False:
        raise GateError("retained-pose authority is not label-blind")
    authority_rows = {row["candidate_id"]: row for row in authority.get("results", [])}
    entries = []
    for candidate_id, ligand_code in config["candidate_ligands"].items():
        if candidate_id not in authority_rows or authority_rows[candidate_id].get("functional_label_blinded") is not True:
            raise GateError(f"retained-pose authority is incomplete or unblinded for {candidate_id}")
        ligand_root = ROOT / config["ligand_bundle_template"].format(ligand_code=ligand_code)
        ligand_audit_path = ligand_root / "audit.json"
        ligand_blockers = []
        if not ligand_audit_path.is_file():
            ligand_blockers.append("ligand_audit_missing")
            ligand_audit = {}
        else:
            ligand_audit = load_json(ligand_audit_path)
            if ligand_audit.get("status") != "accepted_for_system_building":
                ligand_blockers.append("ligand_bundle_not_accepted")
            if ligand_audit.get("molecule_id") != candidate_id or ligand_audit.get("functional_label_blinded") is not True:
                ligand_blockers.append("ligand_identity_or_label_firewall_mismatch")
            for name in config["required_ligand_files"]:
                path = ligand_root / name
                if not path.is_file() or sha256(path) != ligand_audit.get("files", {}).get(name):
                    ligand_blockers.append(f"ligand_file_missing_or_hash_mismatch:{name}")
        for receptor_id, receptor in config["receptors"].items():
            pose_path = ROOT / config["retained_pose_template"].format(candidate_id=candidate_id, receptor_id=receptor_id)
            retained = authority_rows[candidate_id].get("receptors", {}).get(receptor_id, {}).get("retained_pose", {})
            blockers = list(ligand_blockers)
            if not pose_path.is_file() or sha256(pose_path) != retained.get("sha256"):
                blockers.append("retained_pose_missing_or_hash_mismatch")
            receptor_path = ROOT / receptor["accepted_construct"]
            receptor_audit_path = ROOT / receptor["accepted_construct_audit"]
            receptor_ready, receptor_blockers = _accepted_construct(receptor_path, receptor_audit_path, receptor_id)
            blockers.extend(receptor_blockers)
            entries.append({
                "system_id": f"{candidate_id}_{receptor_id}",
                "candidate_id": candidate_id,
                "ligand_code": ligand_code,
                "receptor_id": receptor_id,
                "receptor_state": receptor["state"],
                "functional_label_blinded": True,
                "retained_pose_sha256": sha256(pose_path) if pose_path.is_file() else None,
                "ligand_audit_sha256": sha256(ligand_audit_path) if ligand_audit_path.is_file() else None,
                "receptor_construct_sha256": sha256(receptor_path) if receptor_path.is_file() else None,
                "input_preflight_passed": not blockers and receptor_ready,
                "blockers": blockers,
                "bundle_created": False,
                "trajectory_started": False,
            })

    equilibration_gate_path = DEFAULT_EQUILIBRATION_ROOT / "equilibration_gate_report.json"
    try:
        equilibration = verify_equilibration_gate(require_states=False)
        equilibration_passed = True
        equilibration_blocker = None
    except GateError as exc:
        equilibration = {}
        equilibration_passed = False
        equilibration_blocker = str(exc)
    control_passed = False
    control_gate_error = "Tier A production control-gate report not supplied"
    if control_gate is not None:
        try:
            verify_tier_a_control_gate(control_gate)
            control_passed = True
            control_gate_error = None
        except GateError as exc:
            control_gate_error = str(exc)
    all_inputs = all(row["input_preflight_passed"] for row in entries)
    build_authorized = all_inputs and control_passed
    return {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"],
        "production_specification_id": production["specification_id"],
        "candidate_labels_loaded": False,
        "system_count": len(entries),
        "input_ready_count": sum(row["input_preflight_passed"] for row in entries),
        "tier_a_equilibration_gate_passed": equilibration_passed,
        "tier_a_equilibration_gate_blocker": equilibration_blocker,
        "tier_a_control_gate_passed": control_passed,
        "tier_a_control_gate_blocker": control_gate_error,
        "tier_b_bundle_construction_authorized": build_authorized,
        "tier_b_trajectory_unlocked": False,
        "status": "tier_b_build_inputs_ready_and_control_gate_passed" if build_authorized else "tier_b_build_preflight_locked",
        "systems": entries,
        "bundles_created": 0,
        "trajectories_started": 0,
        "source_hashes": {
            "tier_b_build_config": sha256(CONFIG_PATH),
            "md_production_config": sha256(PRODUCTION_CONFIG),
            "retained_pose_authority": sha256(authority_path),
            **({"tier_a_equilibration_gate": equilibration["equilibration_gate_sha256"]} if equilibration_passed else {}),
            **({"tier_a_control_gate": sha256(control_gate)} if control_gate and control_gate.is_file() else {}),
        },
        "next_gate": "Complete and audit every Tier B receptor/system input, then require the passed Tier A production control report before constructing bundles. Trajectory launch requires separately accepted bundles.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-gate", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_preflight(args.control_gate)
    atomic_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
