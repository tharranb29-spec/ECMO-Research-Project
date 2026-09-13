#!/usr/bin/env python3

"""Run one checkpointed v1.5 Tier A OpenMM replica after every gate passes."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import openmm as mm
from openmm import app, unit


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "md_validation.v1.5.json"
PREFLIGHT = ROOT / "outputs" / "v1.5" / "md" / "preflight_status.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def verified_bundle(bundle: Path, system_id: str) -> tuple[dict, dict[str, Path]]:
    manifest_path = bundle / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("specification_id") != "a2a-md-validation-v1.5":
        raise RuntimeError("Bundle specification ID is not the frozen v1.5 MD protocol")
    if manifest.get("system_id") != system_id or manifest.get("tier") != "A":
        raise RuntimeError("Bundle identity is not the requested Tier A control")
    if manifest.get("status") != "accepted_for_tier_a_production":
        raise RuntimeError("Bundle has not passed the completed-construct, parameter, membrane, and contact audits")
    files = {}
    for name in ["system_xml", "topology_pdb", "equilibrated_state_xml", "native_contacts"]:
        entry = manifest.get("files", {}).get(name, {})
        path = bundle / str(entry.get("path") or "")
        if not path.is_file() or sha256(path) != entry.get("sha256"):
            raise RuntimeError(f"Bundle file missing or hash mismatch: {name}")
        files[name] = path
    return manifest, files


def choose_platform(requested: str) -> mm.Platform:
    names = [requested] if requested != "auto" else ["CUDA", "OpenCL", "CPU"]
    errors = []
    for name in names:
        try:
            return mm.Platform.getPlatformByName(name)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
    raise RuntimeError("No requested OpenMM platform is available: " + "; ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-id", required=True)
    parser.add_argument("--replica", required=True, type=int, choices=[1, 2, 3])
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--platform", choices=["auto", "CUDA", "OpenCL", "CPU"], default="auto")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    allowed = {row["system_id"] for row in config["tiers"]["tier_a_controls"]}
    if args.system_id not in allowed:
        raise RuntimeError("Only the two frozen Tier A controls are accepted by this runner")
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    if preflight.get("status") != "ready_for_tier_a_production" or preflight.get("blockers"):
        reasons = [row.get("reason") for row in preflight.get("blockers", [])]
        raise RuntimeError(f"Tier A production remains locked by preflight: {reasons}")
    manifest, files = verified_bundle(args.bundle, args.system_id)
    if args.preflight_only:
        print(json.dumps({
            "status": "tier_a_replica_preflight_passed",
            "system_id": args.system_id,
            "replica": args.replica,
            "bundle_manifest_sha256": sha256(args.bundle / "bundle_manifest.json"),
        }, indent=2))
        return

    simulation_config = config["simulation"]
    timestep_fs = float(simulation_config["integration_timestep_fs"])
    production_ns = float(simulation_config["production_ns_per_replica"])
    restart_ns = float(simulation_config["restart_interval_ns"])
    seed = int(simulation_config["replica_seeds"][args.replica - 1])
    total_steps = round(production_ns * 1_000_000 / timestep_fs)
    chunk_steps = round(restart_ns * 1_000_000 / timestep_fs)
    frame_steps = round(float(simulation_config["frame_interval_ps"]) * 1000 / timestep_fs)
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
            float(config["system_preparation"]["temperature_kelvin"]) * unit.kelvin,
            seed,
        )
    simulation.reporters.append(app.DCDReporter(str(output / "trajectory.dcd"), frame_steps, append=resumed))
    simulation.reporters.append(app.StateDataReporter(
        str(output / "state.csv"), frame_steps, step=True, time=True,
        potentialEnergy=True, kineticEnergy=True, temperature=True, volume=True,
        density=True, speed=True, remainingTime=True, totalSteps=total_steps,
        separator=",", append=resumed,
    ))
    start_step = simulation.currentStep
    atomic_json(status_path, {
        "status": "running",
        "started_or_resumed_at": datetime.now(timezone.utc).isoformat(),
        "system_id": args.system_id,
        "replica": args.replica,
        "seed": seed,
        "platform": platform.getName(),
        "start_step": start_step,
        "target_steps": total_steps,
        "bundle_manifest_sha256": sha256(args.bundle / "bundle_manifest.json"),
        "native_contacts_sha256": manifest["files"]["native_contacts"]["sha256"],
    })
    while simulation.currentStep < total_steps:
        simulation.step(min(chunk_steps, total_steps - simulation.currentStep))
        simulation.saveCheckpoint(str(checkpoint))
        atomic_json(status_path, {
            "status": "running" if simulation.currentStep < total_steps else "complete",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "system_id": args.system_id,
            "replica": args.replica,
            "seed": seed,
            "platform": platform.getName(),
            "current_step": simulation.currentStep,
            "target_steps": total_steps,
            "completed_ns": simulation.currentStep * timestep_fs / 1_000_000,
            "bundle_manifest_sha256": sha256(args.bundle / "bundle_manifest.json"),
            "native_contacts_sha256": manifest["files"]["native_contacts"]["sha256"],
        })
    final_state = simulation.context.getState(getPositions=True, getVelocities=True, getParameters=True)
    (output / "final_state.xml").write_text(mm.XmlSerializer.serialize(final_state), encoding="utf-8")


if __name__ == "__main__":
    main()
