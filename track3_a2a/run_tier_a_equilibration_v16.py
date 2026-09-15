#!/usr/bin/env python3
"""Run the frozen, checkpointable v1.6 Tier A staged equilibration."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import Platform, XmlSerializer, unit
from openmm.app import PDBFile, Simulation, StateDataReporter


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "tier_a_equilibration.v1.6.json"
LOCAL_INPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_periodic_systems"
LOCAL_SMOKE = ROOT / "outputs" / "v1.6" / "md" / "tier_a_smoke_tests"
RELEASE = ROOT / "outputs" / "v1.6" / "md" / "tier_a_release_bundles"
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_equilibration"
PROTEIN = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "CYX", "GLN", "GLU", "GLY", "HIS", "HID", "HIE", "HIP",
    "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}
LIGANDS = {"ZMA", "NEC"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose_platform(requested: str) -> tuple[Platform, dict[str, str]]:
    available = [Platform.getPlatform(i).getName() for i in range(Platform.getNumPlatforms())]
    name = requested
    if name == "auto":
        name = "Reference"
        for candidate in ("CUDA", "OpenCL", "CPU", "Reference"):
            if candidate not in available:
                continue
            probe_system = mm.System()
            probe_system.addParticle(1.0)
            probe_integrator = mm.VerletIntegrator(0.001)
            try:
                mm.Context(probe_system, probe_integrator, Platform.getPlatformByName(candidate))
                name = candidate
                break
            except Exception:
                continue
    if name not in available:
        raise RuntimeError(f"Requested platform {name!r} unavailable; found {available}")
    properties: dict[str, str] = {}
    if name == "CUDA":
        properties = {"Precision": "mixed"}
    elif name == "OpenCL":
        properties = {"Precision": "mixed"}
    return Platform.getPlatformByName(name), properties


def materialize_bundle(system_id: str, scratch: Path) -> Path:
    local = LOCAL_INPUT / system_id
    if (local / "system.xml").is_file() and (LOCAL_SMOKE / system_id / "smoke_final_state.xml").is_file():
        return local
    archive = RELEASE / f"{system_id}.tar.gz"
    manifest_path = RELEASE / f"{system_id}.manifest.json"
    if not archive.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"No local raw system or release bundle for {system_id}")
    manifest = json.loads(manifest_path.read_text())
    if sha256(archive) != manifest["archive"]["sha256"]:
        raise RuntimeError(f"Archive hash mismatch for {system_id}")
    destination = scratch / system_id
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        names = set(tar.getnames())
        required = set(manifest["members_sha256"]) | {"bundle_manifest.json"}
        if not required.issubset(names) or any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise RuntimeError(f"Unsafe or incomplete archive for {system_id}")
        for name in required:
            member = tar.getmember(name)
            handle = tar.extractfile(member)
            if not member.isfile() or handle is None:
                raise RuntimeError(f"Invalid archive member: {system_id}/{name}")
            (destination / name).write_bytes(handle.read())
    for name, expected in manifest["members_sha256"].items():
        if sha256(destination / name) != expected:
            raise RuntimeError(f"Member hash mismatch: {system_id}/{name}")
    return destination


def read_smoke_state(source: Path, system_id: str):
    local = LOCAL_SMOKE / system_id / "smoke_final_state.xml"
    path = local if local.is_file() else source / "smoke_final_state.xml"
    return XmlSerializer.deserialize(path.read_text()), path


def contact_fraction(positions, contacts: list[dict], cutoff_angstrom: float = 6.0) -> float:
    xyz = positions.value_in_unit(unit.angstrom)
    retained = sum(np.linalg.norm(xyz[row["ligand_atom_index"]] - xyz[row["receptor_atom_index"]]) <= cutoff_angstrom for row in contacts)
    return retained / len(contacts) if contacts else 0.0


def add_restraints(system, pdb: PDBFile) -> tuple[mm.CustomExternalForce, int]:
    force = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    force.addGlobalParameter("k", 1000.0 * unit.kilojoule_per_mole / unit.nanometer**2)
    for name in ("x0", "y0", "z0"):
        force.addPerParticleParameter(name)
    count = 0
    for atom, position in zip(pdb.topology.atoms(), pdb.positions):
        if atom.element.symbol != "H" and (atom.residue.name in PROTEIN or atom.residue.name in LIGANDS):
            force.addParticle(atom.index, position.value_in_unit(unit.nanometer))
            count += 1
    system.addForce(force)
    return force, count


def stage_steps(duration_ps: float, timestep_fs: float, scale: float) -> int:
    return max(1, round(duration_ps * 1000.0 / timestep_fs * scale))


def run(system_id: str, seed: int, output_root: Path, platform_name: str, scale: float) -> dict:
    config = json.loads(CONFIG_PATH.read_text())
    scratch = output_root / "_inputs"
    source = materialize_bundle(system_id, scratch)
    pdb = PDBFile(str(source / "positions.pdb"))
    system = XmlSerializer.deserialize((source / "system.xml").read_text())
    smoke_state, smoke_path = read_smoke_state(source, system_id)
    contacts = json.loads((source / "native_contacts.json").read_text())["native_contacts"]
    _, restrained_count = add_restraints(system, pdb)
    barostat = mm.MonteCarloMembraneBarostat(
        config["pressure_bar"] * unit.bar,
        config["surface_tension_bar_nm"] * unit.bar * unit.nanometer,
        config["temperature_kelvin"] * unit.kelvin,
        mm.MonteCarloMembraneBarostat.XYIsotropic,
        mm.MonteCarloMembraneBarostat.ZFree,
        0,
    )
    system.addForce(barostat)
    timestep = config["timestep_femtoseconds"] * unit.femtoseconds
    integrator = mm.LangevinMiddleIntegrator(
        config["temperature_kelvin"] * unit.kelvin,
        config["collision_rate_per_picosecond"] / unit.picosecond,
        timestep,
    )
    integrator.setRandomNumberSeed(seed)
    platform, properties = choose_platform(platform_name)
    simulation = Simulation(pdb.topology, system, integrator, platform, properties)
    simulation.context.setPeriodicBoxVectors(*smoke_state.getPeriodicBoxVectors())
    simulation.context.setPositions(smoke_state.getPositions())
    simulation.context.applyConstraints(1e-6)
    degrees_of_freedom = 3 * system.getNumParticles() - system.getNumConstraints()
    if any(isinstance(system.getForce(i), mm.CMMotionRemover) for i in range(system.getNumForces())):
        degrees_of_freedom -= 3

    destination = output_root / system_id / f"seed-{seed}"
    destination.mkdir(parents=True, exist_ok=True)
    checkpoint = destination / "equilibration.chk"
    progress = destination / "progress.json"
    completed: list[dict] = []
    start_index = 0
    if checkpoint.is_file() and progress.is_file():
        saved = json.loads(progress.read_text())
        if saved.get("config_sha256") != sha256(CONFIG_PATH) or saved.get("system_id") != system_id or saved.get("seed") != seed:
            raise RuntimeError("Checkpoint metadata does not match the frozen run")
        simulation.loadCheckpoint(str(checkpoint))
        completed = saved["completed_stages"]
        start_index = len(completed)
    else:
        simulation.context.setParameter("k", config["minimization"]["protein_ligand_heavy_restraint_k_kj_mol_nm2"])
        simulation.minimizeEnergy(
            tolerance=config["minimization"]["tolerance_kj_mol_nm"] * unit.kilojoule_per_mole / unit.nanometer,
            maxIterations=(
                config["minimization"]["maximum_iterations"]
                if scale == 1.0 else max(25, round(config["minimization"]["maximum_iterations"] * scale))
            ),
        )
        simulation.context.setVelocitiesToTemperature(100 * unit.kelvin, seed)

    log_path = destination / "state_data.csv"
    simulation.reporters.append(StateDataReporter(
        str(log_path), max(1, round(config["report_interval_steps"] * scale)),
        step=True, time=True, potentialEnergy=True, kineticEnergy=True, temperature=True,
        volume=True, density=True, separator=",", append=start_index > 0,
    ))
    npt_enabled = start_index > 0 and any(row["ensemble"] == "NPT" for row in completed)
    if npt_enabled:
        barostat.setFrequency(config["barostat_frequency_steps"])
        simulation.context.reinitialize(preserveState=True)
    for index, stage in enumerate(config["stages"][start_index:], start=start_index):
        integrator.setTemperature(stage["temperature_kelvin"] * unit.kelvin)
        simulation.context.setParameter("k", stage["restraint_k_kj_mol_nm2"])
        barostat.setDefaultTemperature(stage["temperature_kelvin"] * unit.kelvin)
        if stage["ensemble"] == "NPT" and not npt_enabled:
            barostat.setFrequency(config["barostat_frequency_steps"])
            simulation.context.reinitialize(preserveState=True)
            npt_enabled = True
        simulation.context.setParameter(mm.MonteCarloMembraneBarostat.Temperature(), stage["temperature_kelvin"])
        steps = stage_steps(stage["duration_ps"], config["timestep_femtoseconds"], scale)
        simulation.step(steps)
        state = simulation.context.getState(getEnergy=True, getPositions=True)
        pe = float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
        ke = float(state.getKineticEnergy().value_in_unit(unit.kilojoule_per_mole))
        temp = 2 * ke / (degrees_of_freedom * unit.MOLAR_GAS_CONSTANT_R.value_in_unit(unit.kilojoule_per_mole / unit.kelvin))
        vectors = state.getPeriodicBoxVectors(asNumpy=True).value_in_unit(unit.nanometer)
        volume = float(abs(np.linalg.det(np.asarray(vectors))))
        row = {
            "name": stage["name"], "ensemble": stage["ensemble"], "steps": steps,
            "effective_duration_ps": steps * config["timestep_femtoseconds"] / 1000.0,
            "potential_energy_kj_mol": pe, "kinetic_energy_kj_mol": ke,
            "instantaneous_temperature_kelvin": temp, "volume_nm3": volume,
            "native_contact_fraction_at_6A": contact_fraction(state.getPositions(asNumpy=True), contacts),
        }
        completed.append(row)
        simulation.saveCheckpoint(str(checkpoint))
        progress.write_text(json.dumps({
            "system_id": system_id, "seed": seed, "config_sha256": sha256(CONFIG_PATH),
            "completed_stages": completed,
        }, indent=2) + "\n")

    final_state = simulation.context.getState(getEnergy=True, getPositions=True, getVelocities=True)
    final_path = destination / "equilibrated_state.xml"
    final_path.write_text(XmlSerializer.serialize(final_state))
    gate = config["equilibration_gate"]
    final = completed[-1]
    finite = all(math.isfinite(value) for row in completed for value in (
        row["potential_energy_kj_mol"], row["kinetic_energy_kj_mol"],
        row["instantaneous_temperature_kelvin"], row["volume_nm3"], row["native_contact_fraction_at_6A"],
    ))
    # Stage-end samples are deliberately conservative; full-density CV is computed
    # from the state-data series when enough unrestrained observations exist.
    volumes: list[float] = []
    if log_path.is_file():
        with log_path.open(newline="") as handle:
            lines = (line[1:] if line.startswith("#") else line for line in handle)
            for row in csv.DictReader(lines):
                key = next((name for name in row if "Volume" in name), None)
                if key and row[key]:
                    volumes.append(float(row[key]))
    tail = volumes[len(volumes) // 2:] if volumes else [final["volume_nm3"]]
    volume_cv = float(np.std(tail) / np.mean(tail)) if np.mean(tail) else math.inf
    passed = (
        scale == 1.0 and finite
        and final["native_contact_fraction_at_6A"] >= gate["minimum_final_native_contact_fraction_at_6A"]
        and abs(final["instantaneous_temperature_kelvin"] - config["temperature_kelvin"]) <= gate["maximum_absolute_final_temperature_deviation_kelvin"]
        and volume_cv <= gate["maximum_last_half_volume_coefficient_of_variation"]
    )
    audit = {
        "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"], "system_id": system_id, "seed": seed,
        "status": "equilibration_gate_passed" if passed else ("scaled_preflight_passed_not_equilibration" if scale < 1.0 and finite else "equilibration_gate_blocked"),
        "platform": platform.getName(), "platform_properties": properties,
        "scale": scale, "config_sha256": sha256(CONFIG_PATH), "source_system_sha256": sha256(source / "system.xml"),
        "source_smoke_state_sha256": sha256(smoke_path), "restrained_heavy_atom_count": restrained_count,
        "temperature_degrees_of_freedom": degrees_of_freedom,
        "completed_stages": completed, "last_half_volume_coefficient_of_variation": volume_cv,
        "finite_energy_temperature_volume": finite, "production_trajectory_started": False,
        "tier_b_unlocked": False, "claim_limit": config["claim_limit"],
        "files": {"equilibrated_state.xml": sha256(final_path), "state_data.csv": sha256(log_path)},
    }
    (destination / "equilibration_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return audit


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=config["systems"], required=True)
    parser.add_argument("--seed", choices=config["replica_seeds"], required=True, type=int)
    parser.add_argument("--platform", choices=["auto", "CUDA", "OpenCL", "CPU", "Reference"], default="auto")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--scale", type=float, default=1.0, help="Development-only duration multiplier; values below 1 cannot pass the gate.")
    args = parser.parse_args()
    if not 0 < args.scale <= 1:
        parser.error("--scale must be in (0, 1]")
    print(json.dumps(run(args.system, args.seed, args.output.resolve(), args.platform, args.scale), indent=2))


if __name__ == "__main__":
    main()
