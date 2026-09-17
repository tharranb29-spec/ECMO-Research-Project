#!/usr/bin/env python3
"""Run one checkpointable 50 ns Tier A pilot replica after the six-run gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from md_readiness_v16 import (
    DEFAULT_EQUILIBRATION_ROOT,
    DEFAULT_RELEASE_ROOT,
    GateError,
    PRODUCTION_CONFIG,
    atomic_json,
    load_json,
    materialize_release_bundle,
    sha256,
    tier_a_systems,
    verify_equilibration_gate,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_production"


def choose_platform(mm, requested: str):
    available = [mm.Platform.getPlatform(index).getName() for index in range(mm.Platform.getNumPlatforms())]
    choices = [requested] if requested != "auto" else ["CUDA", "OpenCL", "CPU", "Reference"]
    for name in choices:
        if name in available:
            properties = {"Precision": "mixed"} if name in {"CUDA", "OpenCL"} else {}
            return mm.Platform.getPlatformByName(name), properties
    raise RuntimeError(f"No requested OpenMM platform is available; found {available}")


def preflight(args: argparse.Namespace) -> dict:
    config = load_json(PRODUCTION_CONFIG)
    systems = tier_a_systems(config)
    if args.system not in systems:
        raise GateError("only the two frozen Tier A controls are accepted")
    if args.replica not in (1, 2, 3):
        raise GateError("replica must be 1, 2, or 3")
    seed = config["tier_a"]["replica_seeds"][args.replica - 1]
    gate = verify_equilibration_gate(args.equilibration_root, args.release_root, require_states=True)
    audit_path = args.equilibration_root / args.system / f"seed-{seed}" / "equilibration_audit.json"
    audit = load_json(audit_path)
    state_path = audit_path.parent / "equilibrated_state.xml"
    release = verify_release_bundle(args.system, args.release_root)
    return {
        "status": "tier_a_replica_preflight_passed",
        "specification_id": config["specification_id"],
        "system_id": args.system,
        "replica": args.replica,
        "seed": seed,
        "production_config_sha256": sha256(PRODUCTION_CONFIG),
        "equilibration_gate_sha256": gate["equilibration_gate_sha256"],
        "equilibration_audit_sha256": sha256(audit_path),
        "equilibrated_state_sha256": sha256(state_path),
        "release_archive_sha256": release["archive"]["sha256"],
        "candidate_labels_loaded": False,
        "trajectory_started": False,
    }


def run(args: argparse.Namespace, checked: dict) -> dict:
    try:
        import openmm as mm
        from openmm import XmlSerializer, unit
        from openmm.app import DCDReporter, PDBFile, Simulation, StateDataReporter
    except ImportError as exc:
        raise RuntimeError("OpenMM 8.6 is required for production execution") from exc

    config = load_json(PRODUCTION_CONFIG)
    system_id, seed = checked["system_id"], checked["seed"]
    source = materialize_release_bundle(system_id, args.output_root / "_verified_inputs", args.release_root)
    state_path = args.equilibration_root / system_id / f"seed-{seed}" / "equilibrated_state.xml"
    system = XmlSerializer.deserialize((source / "system.xml").read_text(encoding="utf-8"))
    barostat_types = (mm.MonteCarloBarostat, mm.MonteCarloMembraneBarostat, mm.MonteCarloAnisotropicBarostat)
    if any(isinstance(system.getForce(index), barostat_types) for index in range(system.getNumForces())):
        raise RuntimeError("release system unexpectedly contains a barostat")
    barostat = mm.MonteCarloMembraneBarostat(
        config["pressure_bar"] * unit.bar,
        config["surface_tension_bar_nm"] * unit.bar * unit.nanometer,
        config["temperature_kelvin"] * unit.kelvin,
        mm.MonteCarloMembraneBarostat.XYIsotropic,
        mm.MonteCarloMembraneBarostat.ZFree,
        config["barostat_frequency_steps"],
    )
    barostat.setRandomNumberSeed(seed)
    system.addForce(barostat)
    timestep_fs = float(config["integration_timestep_femtoseconds"])
    integrator = mm.LangevinMiddleIntegrator(
        config["temperature_kelvin"] * unit.kelvin,
        config["collision_rate_per_picosecond"] / unit.picosecond,
        timestep_fs * unit.femtoseconds,
    )
    integrator.setRandomNumberSeed(seed)
    integrator.setConstraintTolerance(config["constraint_tolerance"])
    platform, properties = choose_platform(mm, args.platform)
    pdb = PDBFile(str(source / "positions.pdb"))
    simulation = Simulation(pdb.topology, system, integrator, platform, properties)

    output = args.output_root / system_id / f"replica_{args.replica}"
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "restart.chk"
    status_path = output / "run_status.json"
    trajectory_path = output / "trajectory.dcd"
    state_data_path = output / "state.csv"
    production_ns = float(config["tier_a"]["pilot_ns_per_replica"])
    total_steps = round(production_ns * 1_000_000 / timestep_fs)
    checkpoint_steps = round(float(config["checkpoint_interval_ps"]) * 1000 / timestep_fs)
    frame_steps = round(float(config["frame_interval_ps"]) * 1000 / timestep_fs)
    state_steps = round(float(config["state_interval_ps"]) * 1000 / timestep_fs)
    resumed = checkpoint_path.is_file()
    if not resumed and any(path.exists() for path in (status_path, trajectory_path, state_data_path)):
        raise RuntimeError("partial output exists without a checkpoint; preserve it and use a clean output directory")
    if resumed:
        if not status_path.is_file():
            raise RuntimeError("checkpoint exists without run_status.json")
        prior = load_json(status_path)
        immutable = {
            "specification_id": config["specification_id"],
            "production_config_sha256": checked["production_config_sha256"],
            "system_id": system_id,
            "replica": args.replica,
            "seed": seed,
            "target_steps": total_steps,
            "equilibration_audit_sha256": checked["equilibration_audit_sha256"],
            "equilibrated_state_sha256": checked["equilibrated_state_sha256"],
        }
        if any(prior.get(key) != value for key, value in immutable.items()):
            raise RuntimeError("checkpoint metadata does not match the frozen production contract")
        simulation.loadCheckpoint(str(checkpoint_path))
    else:
        state = XmlSerializer.deserialize(state_path.read_text(encoding="utf-8"))
        simulation.context.setState(state)
        simulation.context.setVelocitiesToTemperature(config["temperature_kelvin"] * unit.kelvin, seed)

    simulation.reporters.append(DCDReporter(str(trajectory_path), frame_steps, append=resumed, enforcePeriodicBox=False))
    simulation.reporters.append(StateDataReporter(
        str(state_data_path), state_steps, step=True, time=True, potentialEnergy=True,
        kineticEnergy=True, temperature=True, volume=True, density=True, speed=True,
        remainingTime=True, totalSteps=total_steps, separator=",", append=resumed,
    ))
    base_status = {
        **checked,
        "status": "running",
        "platform": platform.getName(),
        "platform_properties": properties,
        "current_step": simulation.currentStep,
        "target_steps": total_steps,
        "target_ns": production_ns,
        "trajectory_started": True,
        "tier_b_unlocked": False,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(status_path, base_status)
    try:
        while simulation.currentStep < total_steps:
            simulation.step(min(checkpoint_steps, total_steps - simulation.currentStep))
            simulation.saveCheckpoint(str(checkpoint_path))
            atomic_json(status_path, {
                **base_status,
                "status": "complete" if simulation.currentStep == total_steps else "running",
                "current_step": simulation.currentStep,
                "completed_ns": simulation.currentStep * timestep_fs / 1_000_000,
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as exc:
        atomic_json(output / "failure_audit.json", {
            **base_status,
            "status": "technical_failure",
            "current_step": simulation.currentStep,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "tier_b_unlocked": False,
            "failed_replica_may_not_be_omitted": True,
        })
        raise
    final_state_path = output / "final_state.xml"
    final_state = simulation.context.getState(getPositions=True, getVelocities=True, getParameters=True)
    final_state_path.write_text(XmlSerializer.serialize(final_state), encoding="utf-8")
    complete = load_json(status_path)
    complete["files"] = {
        "trajectory.dcd": sha256(trajectory_path),
        "state.csv": sha256(state_data_path),
        "final_state.xml": sha256(final_state_path),
        "restart.chk": sha256(checkpoint_path),
    }
    atomic_json(status_path, complete)
    return complete


def main() -> None:
    config = load_json(PRODUCTION_CONFIG)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=sorted(tier_a_systems(config)), required=True)
    parser.add_argument("--replica", choices=(1, 2, 3), type=int, required=True)
    parser.add_argument("--equilibration-root", type=Path, default=DEFAULT_EQUILIBRATION_ROOT)
    parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--platform", choices=("auto", "CUDA", "OpenCL", "CPU", "Reference"), default="auto")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    try:
        checked = preflight(args)
    except GateError as exc:
        raise SystemExit(f"LOCKED: {exc}") from exc
    result = checked if args.preflight_only else run(args, checked)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
