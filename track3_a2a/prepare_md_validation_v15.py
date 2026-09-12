#!/usr/bin/env python3

"""Create the v1.5 MD input manifest and enforce the pre-production gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "md_validation.v1.5.json"
CANDIDATES = ROOT / "outputs" / "v1.4" / "external_cohort" / "literature_pilot_2025" / "eligible_candidates.csv"
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "outputs" / "v1.5" / "md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
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
            if caveats:
                blockers.append({
                    "system_id": system["system_id"],
                    "reason": "deposited_structure_caveat_requires_manual_review",
                    "details": caveats,
                })
    if importlib.util.find_spec("openmm") is None:
        blockers.append({"system_id": "global", "reason": "openmm_not_installed"})
    blockers.extend([
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
        "tier_a_system_count": 2,
        "tier_b_system_count": 8,
        "planned_tier_a_plus_b_replicas": 30,
        "planned_tier_a_plus_b_sampling_microseconds": 3.0,
        "source_hashes": {
            "md_config": sha256(CONFIG),
            "candidate_manifest": sha256(CANDIDATES),
            "system_input_manifest": sha256(manifest_path),
        },
        "blockers": blockers,
        "next_gate": "Resolve every listed blocker, build both native controls, and freeze native contacts before any production trajectory.",
    }
    status_path = args.output / "preflight_status.json"
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
