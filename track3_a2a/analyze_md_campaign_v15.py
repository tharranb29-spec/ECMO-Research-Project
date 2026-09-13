#!/usr/bin/env python3

"""Analyze frozen Tier A or blinded Tier B trajectories and enforce the control gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import mdtraj as md
import numpy as np


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "md_validation.v1.5.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_replica(bundle: Path, run: Path) -> dict:
    manifest_path = bundle / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contacts_path = bundle / manifest["files"]["native_contacts"]["path"]
    definition = json.loads(contacts_path.read_text(encoding="utf-8"))
    topology_path = bundle / manifest["files"]["topology_pdb"]["path"]
    trajectory_path = run / "trajectory.dcd"
    status_path = run / "run_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("status") != "complete":
        raise RuntimeError(f"Replica is not complete: {run}")
    trajectory = md.load_dcd(str(trajectory_path), top=str(topology_path))
    reference = md.load(str(topology_path))
    alignment = np.asarray(definition["alignment_atom_indices"], dtype=int)
    ligand = np.asarray(definition["ligand_heavy_atom_indices"], dtype=int)
    trajectory.superpose(reference, atom_indices=alignment, ref_atom_indices=alignment)
    start = int(np.floor(len(trajectory) * 0.20))
    window = trajectory[start:]
    reference_xyz = reference.xyz[0, ligand]
    rmsd_nm = np.sqrt(np.mean(np.sum((window.xyz[:, ligand] - reference_xyz[None, :, :]) ** 2, axis=2), axis=1))
    masses = np.asarray([trajectory.topology.atom(int(index)).element.mass for index in ligand], dtype=float)
    masses /= masses.sum()
    com = np.sum(window.xyz[:, ligand] * masses[None, :, None], axis=1)
    reference_com = np.sum(reference_xyz * masses[:, None], axis=0)
    displacement_nm = np.linalg.norm(com - reference_com[None, :], axis=1)
    pairs = np.asarray([
        [int(row["ligand_atom_index"]), int(row["receptor_atom_index"])]
        for row in definition["native_contacts"]
    ], dtype=int)
    occupancies = []
    if len(pairs):
        distances = md.compute_distances(window, pairs, periodic=True)
        occupancies = np.mean(distances <= 0.40, axis=0).tolist()
    retained_fraction = float(np.mean(np.asarray(occupancies) >= 0.50)) if occupancies else 0.0
    median_rmsd_a = float(np.median(rmsd_nm) * 10.0)
    median_displacement_a = float(np.median(displacement_nm) * 10.0)
    passed = median_rmsd_a <= 3.0 and median_displacement_a <= 5.0 and retained_fraction >= 0.50
    return {
        "replica": status["replica"], "passed": passed, "analysis_frame_count": len(window),
        "median_ligand_rmsd_angstrom": median_rmsd_a,
        "median_ligand_com_displacement_angstrom": median_displacement_a,
        "native_contact_count": len(occupancies),
        "native_contacts_with_occupancy_at_least_0_5_fraction": retained_fraction,
        "trajectory_sha256": sha256(trajectory_path), "run_status_sha256": sha256(status_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=["A", "B"], required=True)
    parser.add_argument("--bundles-root", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if args.tier == "A":
        system_ids = [row["system_id"] for row in config["tiers"]["tier_a_controls"]]
    else:
        tier_b = config["tiers"]["tier_b_blinded_candidates"]
        system_ids = [f"{candidate}_{pdb}" for candidate in tier_b["candidate_ids"] for pdb in tier_b["receptor_structures"]]
    systems = []
    for system_id in system_ids:
        replicas = [
            analyze_replica(args.bundles_root / system_id, args.runs_root / system_id / f"replica_{replica}")
            for replica in (1, 2, 3)
        ]
        passed_count = sum(row["passed"] for row in replicas)
        systems.append({"system_id": system_id, "passed_replica_count": passed_count, "passed": passed_count >= 2, "replicas": replicas})
    tier_passed = all(row["passed"] for row in systems)
    if args.tier == "A":
        status = "both_tier_a_controls_passed" if tier_passed else "tier_a_control_gate_failed"
    else:
        status = "tier_b_blinded_analysis_complete" if tier_passed else "tier_b_blinded_analysis_complete_with_failures"
    report = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"], "tier": args.tier, "status": status,
        "candidate_labels_loaded": False, "systems": systems,
        "tier_b_unlocked": bool(args.tier == "A" and tier_passed),
        "interpretation": "MD stability evidence only; not an affinity or functional label.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
