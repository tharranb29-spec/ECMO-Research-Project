#!/usr/bin/env python3
"""Run one checkpointable 20 ns Tier B replica after the Tier A control gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from md_readiness_v16 import GateError, PRODUCTION_CONFIG, atomic_json, load_json, sha256, verify_tier_a_control_gate
from run_tier_a_production_v16 import choose_platform


ROOT = Path(__file__).resolve().parent
BUILD_CONFIG = ROOT / "config" / "tier_b_build.v1.6.json"
DEFAULT_CONTROL_GATE = ROOT / "outputs" / "v1.6" / "md" / "tier_a_production" / "control_gate_report.json"
DEFAULT_BUNDLES = ROOT / "outputs" / "v1.6" / "md" / "tier_b_release_bundles"
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_b_production"


def allowed_systems() -> set[str]:
    config = load_json(BUILD_CONFIG)
    return {
        f"{candidate}_{receptor}"
        for candidate in config["candidate_ligands"]
        for receptor in config["receptors"]
    }


def verified_bundle(bundle: Path, system_id: str, control_gate: Path) -> tuple[dict, dict[str, Path]]:
    manifest_path = bundle / "bundle_manifest.json"
    if not manifest_path.is_file():
        raise GateError(f"Tier B bundle manifest is missing: {bundle}")
    manifest = load_json(manifest_path)
    required = {
        "specification_id": "a2a-tier-b-release-bundle-v1.6",
        "system_id": system_id,
        "tier": "B",
        "status": "accepted_for_tier_b_production",
        "candidate_labels_loaded": False,
        "trajectory_started": False,
        "control_gate_sha256": sha256(control_gate),
    }
    if any(manifest.get(key) != value for key, value in required.items()):
        raise GateError(f"Tier B bundle is not accepted under the current control gate: {system_id}")
    files = {}
    for name in ("system.xml", "positions.pdb", "equilibrated_state.xml", "native_contacts.json", "assembly_audit.json", "smoke_audit.json"):
        path = bundle / name
        if not path.is_file() or sha256(path) != manifest.get("members_sha256", {}).get(name):
            raise GateError(f"Tier B bundle member missing or hash-mismatched: {system_id}/{name}")
        files[name] = path
    return manifest, files


def preflight(args: argparse.Namespace) -> tuple[dict, dict[str, Path]]:
    config = load_json(PRODUCTION_CONFIG)
    if args.system not in allowed_systems():
        raise GateError("system is not one of the eight frozen label-blind Tier B systems")
    gate = verify_tier_a_control_gate(args.control_gate)
    bundle = args.bundles_root / args.system
    manifest, files = verified_bundle(bundle, args.system, args.control_gate)
    seed = config["tier_a"]["replica_seeds"][args.replica - 1]
    checked = {
        "status": "tier_b_replica_preflight_passed",
        "specification_id": config["specification_id"],
        "system_id": args.system,
        "replica": args.replica,
        "seed": seed,
        "production_config_sha256": sha256(PRODUCTION_CONFIG),
        "tier_a_control_gate_sha256": sha256(args.control_gate),
        "bundle_manifest_sha256": sha256(bundle / "bundle_manifest.json"),
        "candidate_labels_loaded": False,
        "trajectory_started": False,
        "tier_a_gate_status": gate["status"],
    }
    return checked, files


def run(args: argparse.Namespace, checked: dict, files: dict[str, Path]) -> dict:
    try:
        import openmm as mm
        from openmm import XmlSerializer, unit
        from openmm.app import DCDReporter, PDBFile, Simulation, StateDataReporter
    except ImportError as exc:
        raise RuntimeError("OpenMM 8.6 is required for production execution") from exc
    config = load_json(PRODUCTION_CONFIG)
    system = XmlSerializer.deserialize(files["system.xml"].read_text(encoding="utf-8"))
    barostat_types = (mm.MonteCarloBarostat, mm.MonteCarloMembraneBarostat, mm.MonteCarloAnisotropicBarostat)
    if any(isinstance(system.getForce(index), barostat_types) for index in range(system.getNumForces())):
        raise RuntimeError("Tier B bundle unexpectedly contains a barostat")
    barostat = mm.MonteCarloMembraneBarostat(
        config["pressure_bar"] * unit.bar,
        config["surface_tension_bar_nm"] * unit.bar * unit.nanometer,
        config["temperature_kelvin"] * unit.kelvin,
        mm.MonteCarloMembraneBarostat.XYIsotropic,
        mm.MonteCarloMembraneBarostat.ZFree,
        config["barostat_frequency_steps"],
    )
    barostat.setRandomNumberSeed(checked["seed"])
    system.addForce(barostat)
    timestep_fs = config["integration_timestep_femtoseconds"]
    integrator = mm.LangevinMiddleIntegrator(
        config["temperature_kelvin"] * unit.kelvin,
        config["collision_rate_per_picosecond"] / unit.picosecond,
        timestep_fs * unit.femtoseconds,
    )
    integrator.setRandomNumberSeed(checked["seed"])
    integrator.setConstraintTolerance(config["constraint_tolerance"])
    platform, properties = choose_platform(mm, args.platform)
    simulation = Simulation(PDBFile(str(files["positions.pdb"])).topology, system, integrator, platform, properties)
    output = args.output_root / args.system / f"replica_{args.replica}"
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / "restart.chk"
    status_path = output / "run_status.json"
    total_steps = round(config["tier_b"]["pilot_ns_per_replica"] * 1_000_000 / timestep_fs)
    chunk_steps = round(config["checkpoint_interval_ps"] * 1000 / timestep_fs)
    resumed = checkpoint.is_file()
    trajectory = output / "trajectory.dcd"
    state_data = output / "state.csv"
    if not resumed and any(path.exists() for path in (status_path, trajectory, state_data)):
        raise RuntimeError("partial output exists without a checkpoint; preserve it and use a clean output directory")
    if resumed:
        prior = load_json(status_path)
        for key in ("specification_id", "system_id", "replica", "seed", "production_config_sha256", "tier_a_control_gate_sha256", "bundle_manifest_sha256"):
            if prior.get(key) != checked[key]:
                raise RuntimeError("Tier B checkpoint metadata does not match the frozen inputs")
        simulation.loadCheckpoint(str(checkpoint))
    else:
        simulation.context.setState(XmlSerializer.deserialize(files["equilibrated_state.xml"].read_text(encoding="utf-8")))
        simulation.context.setVelocitiesToTemperature(config["temperature_kelvin"] * unit.kelvin, checked["seed"])
    frame_steps = round(config["frame_interval_ps"] * 1000 / timestep_fs)
    state_steps = round(config["state_interval_ps"] * 1000 / timestep_fs)
    simulation.reporters.append(DCDReporter(str(trajectory), frame_steps, append=resumed, enforcePeriodicBox=False))
    simulation.reporters.append(StateDataReporter(
        str(state_data), state_steps, step=True, time=True, potentialEnergy=True, kineticEnergy=True,
        temperature=True, volume=True, density=True, speed=True, remainingTime=True,
        totalSteps=total_steps, separator=",", append=resumed,
    ))
    base = {
        **checked,
        "status": "running",
        "trajectory_started": True,
        "platform": platform.getName(),
        "platform_properties": properties,
        "target_steps": total_steps,
        "target_ns": config["tier_b"]["pilot_ns_per_replica"],
    }
    atomic_json(status_path, {**base, "current_step": simulation.currentStep, "updated_at_utc": datetime.now(timezone.utc).isoformat()})
    try:
        while simulation.currentStep < total_steps:
            simulation.step(min(chunk_steps, total_steps - simulation.currentStep))
            simulation.saveCheckpoint(str(checkpoint))
            atomic_json(status_path, {
                **base,
                "status": "complete" if simulation.currentStep == total_steps else "running",
                "current_step": simulation.currentStep,
                "completed_ns": simulation.currentStep * timestep_fs / 1_000_000,
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as exc:
        atomic_json(output / "failure_audit.json", {
            **base, "status": "technical_failure", "current_step": simulation.currentStep,
            "error_type": type(exc).__name__, "error": str(exc),
            "failed_replica_may_not_be_omitted": True,
        })
        raise
    final_state = output / "final_state.xml"
    final_state.write_text(XmlSerializer.serialize(simulation.context.getState(getPositions=True, getVelocities=True, getParameters=True)))
    complete = load_json(status_path)
    complete["files"] = {
        "trajectory.dcd": sha256(trajectory), "state.csv": sha256(state_data),
        "final_state.xml": sha256(final_state), "restart.chk": sha256(checkpoint),
    }
    atomic_json(status_path, complete)
    return complete


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=sorted(allowed_systems()), required=True)
    parser.add_argument("--replica", choices=(1, 2, 3), required=True, type=int)
    parser.add_argument("--control-gate", type=Path, default=DEFAULT_CONTROL_GATE)
    parser.add_argument("--bundles-root", type=Path, default=DEFAULT_BUNDLES)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--platform", choices=("auto", "CUDA", "OpenCL", "CPU", "Reference"), default="auto")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    try:
        checked, files = preflight(args)
    except GateError as exc:
        raise SystemExit(f"LOCKED: {exc}") from exc
    result = checked if args.preflight_only else run(args, checked, files)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
