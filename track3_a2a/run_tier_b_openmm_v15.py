#!/usr/bin/env python3

"""Run one checkpointed Tier B replica only after both Tier A controls pass."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import openmm as mm
from openmm import app, unit

from run_tier_a_openmm_v15 import ROOT, atomic_json, choose_platform, sha256


CONFIG = ROOT / "config" / "md_validation.v1.5.json"
DEFAULT_CONTROL_GATE = ROOT / "outputs" / "v1.5" / "md" / "control_gate_report.json"


def verified_bundle(bundle: Path, system_id: str) -> tuple[dict, dict[str, Path]]:
    manifest_path = bundle / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("specification_id") != "a2a-md-validation-v1.5":
        raise RuntimeError("Bundle specification ID is not the frozen v1.5 MD protocol")
    if manifest.get("system_id") != system_id or manifest.get("tier") != "B":
        raise RuntimeError("Bundle identity is not the requested Tier B system")
    if manifest.get("status") != "accepted_for_tier_b_production":
        raise RuntimeError("Tier B bundle has not passed every computational setup audit")
    files = {}
    for name in ["system_xml", "topology_pdb", "equilibrated_state_xml", "native_contacts"]:
        entry = manifest.get("files", {}).get(name, {})
        path = bundle / str(entry.get("path") or "")
        if not path.is_file() or sha256(path) != entry.get("sha256"):
            raise RuntimeError(f"Bundle file missing or hash mismatch: {name}")
        files[name] = path
    return manifest, files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-id", required=True)
    parser.add_argument("--replica", required=True, type=int, choices=[1, 2, 3])
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--control-gate", type=Path, default=DEFAULT_CONTROL_GATE)
    parser.add_argument("--platform", choices=["auto", "CUDA", "OpenCL", "CPU"], default="auto")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    tier_b = config["tiers"]["tier_b_blinded_candidates"]
    allowed = {f"{candidate}_{pdb}" for candidate in tier_b["candidate_ids"] for pdb in tier_b["receptor_structures"]}
    if args.system_id not in allowed:
        raise RuntimeError("System is not one of the eight frozen blinded Tier B systems")
    gate = json.loads(args.control_gate.read_text(encoding="utf-8"))
    if gate.get("status") != "both_tier_a_controls_passed" or gate.get("tier_b_unlocked") is not True:
        raise RuntimeError("Tier B remains locked because both Tier A controls have not passed")
    manifest, files = verified_bundle(args.bundle, args.system_id)
    if args.preflight_only:
        print(json.dumps({
            "status": "tier_b_replica_preflight_passed",
            "system_id": args.system_id,
            "replica": args.replica,
            "control_gate_sha256": sha256(args.control_gate),
            "bundle_manifest_sha256": sha256(args.bundle / "bundle_manifest.json"),
        }, indent=2))
        return

    simulation_config = config["simulation"]
    timestep_fs = float(simulation_config["integration_timestep_fs"])
    total_steps = round(float(simulation_config["production_ns_per_replica"]) * 1_000_000 / timestep_fs)
    chunk_steps = round(float(simulation_config["restart_interval_ns"]) * 1_000_000 / timestep_fs)
    frame_steps = round(float(simulation_config["frame_interval_ps"]) * 1000 / timestep_fs)
    seed = int(simulation_config["replica_seeds"][args.replica - 1])
    output = args.output_root / args.system_id / f"replica_{args.replica}"
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / "restart.chk"
    status_path = output / "run_status.json"
    system = mm.XmlSerializer.deserialize(files["system_xml"].read_text(encoding="utf-8"))
    topology_file = app.PDBFile(str(files["topology_pdb"]))
    integrator = mm.LangevinMiddleIntegrator(
        float(config["system_preparation"]["temperature_kelvin"]) * unit.kelvin,
        1 / unit.picosecond,
        timestep_fs * unit.femtoseconds,
    )
    integrator.setRandomNumberSeed(seed)
    platform = choose_platform(args.platform)
    properties = {"Threads": "12"} if platform.getName() == "CPU" else {}
    simulation = app.Simulation(topology_file.topology, system, integrator, platform, properties)
    resumed = checkpoint.exists()
    if resumed:
        simulation.loadCheckpoint(str(checkpoint))
    else:
        state = mm.XmlSerializer.deserialize(files["equilibrated_state_xml"].read_text(encoding="utf-8"))
        simulation.context.setState(state)
        simulation.context.setVelocitiesToTemperature(
            float(config["system_preparation"]["temperature_kelvin"]) * unit.kelvin, seed
        )
    simulation.reporters.append(app.DCDReporter(str(output / "trajectory.dcd"), frame_steps, append=resumed))
    simulation.reporters.append(app.StateDataReporter(
        str(output / "state.csv"), frame_steps, step=True, time=True, potentialEnergy=True,
        kineticEnergy=True, temperature=True, volume=True, density=True, speed=True,
        remainingTime=True, totalSteps=total_steps, separator=",", append=resumed,
    ))
    atomic_json(status_path, {
        "status": "running", "updated_at": datetime.now(timezone.utc).isoformat(),
        "system_id": args.system_id, "replica": args.replica, "seed": seed,
        "platform": platform.getName(), "current_step": simulation.currentStep,
        "target_steps": total_steps, "candidate_labels_loaded": False,
        "control_gate_sha256": sha256(args.control_gate),
        "bundle_manifest_sha256": sha256(args.bundle / "bundle_manifest.json"),
    })
    while simulation.currentStep < total_steps:
        simulation.step(min(chunk_steps, total_steps - simulation.currentStep))
        simulation.saveCheckpoint(str(checkpoint))
        atomic_json(status_path, {
            "status": "running" if simulation.currentStep < total_steps else "complete",
            "updated_at": datetime.now(timezone.utc).isoformat(), "system_id": args.system_id,
            "replica": args.replica, "seed": seed, "platform": platform.getName(),
            "current_step": simulation.currentStep, "target_steps": total_steps,
            "completed_ns": simulation.currentStep * timestep_fs / 1_000_000,
            "candidate_labels_loaded": False, "control_gate_sha256": sha256(args.control_gate),
            "bundle_manifest_sha256": sha256(args.bundle / "bundle_manifest.json"),
        })
    state = simulation.context.getState(getPositions=True, getVelocities=True, getParameters=True)
    (output / "final_state.xml").write_text(mm.XmlSerializer.serialize(state), encoding="utf-8")


if __name__ == "__main__":
    main()
