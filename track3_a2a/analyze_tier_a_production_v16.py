#!/usr/bin/env python3
"""Analyze all six Tier A pilot replicas and emit the Tier B unlock gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from md_readiness_v16 import (
    DEFAULT_RELEASE_ROOT,
    GateError,
    PRODUCTION_CONFIG,
    atomic_json,
    load_json,
    materialize_release_bundle,
    sha256,
    tier_a_systems,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_RUNS = ROOT / "outputs" / "v1.6" / "md" / "tier_a_production"
DEFAULT_OUTPUT = DEFAULT_RUNS / "control_gate_report.json"


def _finite_state_data(path: Path) -> tuple[bool, int]:
    if not path.is_file():
        return False, 0
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    finite = bool(rows)
    for row in rows:
        for value in row.values():
            if value in (None, ""):
                continue
            try:
                finite = finite and math.isfinite(float(value))
            except ValueError:
                pass
    return finite, len(rows)


def analyze_replica(system_spec: dict, replica: int, run: Path, bundle: Path, config: dict) -> dict:
    try:
        import mdtraj as md
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("mdtraj and numpy are required for production analysis") from exc

    status_path = run / "run_status.json"
    if not status_path.is_file():
        raise GateError(f"missing run status: {run}")
    status = load_json(status_path)
    seed = config["tier_a"]["replica_seeds"][replica - 1]
    expected_steps = round(
        config["tier_a"]["pilot_ns_per_replica"] * 1_000_000
        / config["integration_timestep_femtoseconds"]
    )
    required_status = {
        "status": "complete",
        "specification_id": config["specification_id"],
        "production_config_sha256": sha256(PRODUCTION_CONFIG),
        "system_id": system_spec["system_id"],
        "replica": replica,
        "seed": seed,
        "target_steps": expected_steps,
        "current_step": expected_steps,
        "trajectory_started": True,
    }
    if any(status.get(key) != value for key, value in required_status.items()):
        raise GateError(f"incomplete or provenance-mismatched replica: {run}")
    trajectory_path = run / "trajectory.dcd"
    state_path = run / "state.csv"
    for name, path in (("trajectory.dcd", trajectory_path), ("state.csv", state_path)):
        if not path.is_file() or sha256(path) != status.get("files", {}).get(name):
            raise GateError(f"missing or hash-mismatched {name}: {run}")
    finite_state, state_rows = _finite_state_data(state_path)
    trajectory = md.load_dcd(str(trajectory_path), top=str(bundle / "positions.pdb"))
    if len(trajectory) == 0:
        raise GateError(f"empty trajectory: {run}")
    reference = md.load(str(bundle / "positions.pdb"))
    contacts = load_json(bundle / "native_contacts.json")["native_contacts"]
    receptor_chain_counts = Counter(
        trajectory.topology.atom(int(row["receptor_atom_index"])).residue.chain.index
        for row in contacts
    )
    if not receptor_chain_counts:
        raise GateError(f"native-contact definition is empty for {system_spec['system_id']}")
    receptor_chain_index = receptor_chain_counts.most_common(1)[0][0]
    tm_ranges = config["transmembrane_alignment_residue_ranges"]
    allowed = {value for start, end in tm_ranges for value in range(start, end + 1)}
    alignment = [
        atom.index for atom in trajectory.topology.atoms
        if atom.name == "CA" and atom.residue.chain.index == receptor_chain_index
        and int(atom.residue.resSeq) in allowed
    ]
    ligand = [
        atom.index for atom in trajectory.topology.atoms
        if atom.residue.name == system_spec["ligand_residue"] and atom.element.symbol != "H"
    ]
    if len(alignment) < 100 or not ligand:
        raise GateError(f"analysis selections are incomplete for {system_spec['system_id']}")
    trajectory.superpose(reference, atom_indices=alignment, ref_atom_indices=alignment)
    window_fraction = config["tier_a"]["analysis_gate"]["analysis_window_fraction"]
    start = int(math.floor(len(trajectory) * (1.0 - window_fraction)))
    window = trajectory[start:]
    ligand_indices = np.asarray(ligand, dtype=int)
    reference_xyz = reference.xyz[0, ligand_indices]
    rmsd_nm = np.sqrt(np.mean(np.sum((window.xyz[:, ligand_indices] - reference_xyz[None, :, :]) ** 2, axis=2), axis=1))
    masses = np.asarray([trajectory.topology.atom(index).element.mass for index in ligand_indices], dtype=float)
    masses /= masses.sum()
    com = np.sum(window.xyz[:, ligand_indices] * masses[None, :, None], axis=1)
    reference_com = np.sum(reference_xyz * masses[:, None], axis=0)
    displacement_nm = np.linalg.norm(com - reference_com[None, :], axis=1)
    pairs = np.asarray([[row["ligand_atom_index"], row["receptor_atom_index"]] for row in contacts], dtype=int)
    distances = md.compute_distances(window, pairs, periodic=True)
    thresholds = config["tier_a"]["analysis_gate"]
    occupancies = np.mean(distances <= thresholds["native_contact_distance_angstrom"] / 10.0, axis=0)
    retained_fraction = float(np.mean(occupancies >= thresholds["minimum_per_contact_occupancy"]))
    median_rmsd = float(np.median(rmsd_nm) * 10.0)
    median_displacement = float(np.median(displacement_nm) * 10.0)
    passed = (
        finite_state
        and median_rmsd <= thresholds["maximum_median_ligand_rmsd_angstrom"]
        and median_displacement <= thresholds["maximum_median_ligand_com_displacement_angstrom"]
        and retained_fraction >= thresholds["minimum_fraction_native_contacts_meeting_occupancy"]
    )
    return {
        "replica": replica,
        "seed": seed,
        "passed": passed,
        "analysis_frame_count": len(window),
        "state_data_row_count": state_rows,
        "finite_state_data": finite_state,
        "median_ligand_rmsd_angstrom": median_rmsd,
        "median_ligand_com_displacement_angstrom": median_displacement,
        "native_contact_count": len(contacts),
        "native_contacts_with_occupancy_at_least_0_5_fraction": retained_fraction,
        "trajectory_sha256": sha256(trajectory_path),
        "run_status_sha256": sha256(status_path),
    }


def analyze(runs_root: Path, release_root: Path, output: Path) -> dict:
    config = load_json(PRODUCTION_CONFIG)
    scratch = output.parent / "_analysis_inputs"
    systems = []
    for system_id, system_spec in tier_a_systems(config).items():
        bundle = materialize_release_bundle(system_id, scratch, release_root)
        replicas = [
            analyze_replica(system_spec, replica, runs_root / system_id / f"replica_{replica}", bundle, config)
            for replica in (1, 2, 3)
        ]
        passed_count = sum(row["passed"] for row in replicas)
        required = config["tier_a"]["analysis_gate"]["required_passing_replicas_per_control"]
        systems.append({
            "system_id": system_id,
            "passed_replica_count": passed_count,
            "passed": passed_count >= required,
            "replicas": replicas,
        })
    passed = all(row["passed"] for row in systems)
    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"],
        "production_config_sha256": sha256(PRODUCTION_CONFIG),
        "status": "both_tier_a_controls_passed" if passed else "tier_a_control_gate_failed",
        "candidate_labels_loaded": False,
        "all_six_replicas_reported": True,
        "best_replica_selection": "prohibited",
        "systems": systems,
        "tier_b_unlocked": passed,
        "interpretation": config["claim_limit"],
    }
    atomic_json(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        report = analyze(args.runs_root, args.release_root, args.output)
    except GateError as exc:
        raise SystemExit(f"LOCKED: {exc}") from exc
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
