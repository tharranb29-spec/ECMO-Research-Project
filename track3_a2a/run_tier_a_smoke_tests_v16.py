#!/usr/bin/env python3
"""Run bounded minimization, NVT, and membrane-NPT smoke tests for Tier A."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import Platform, XmlSerializer, unit
from openmm.app import PDBFile, Simulation


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_periodic_systems"
OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_smoke_tests"
SYSTEMS = ["5NM4_ZMA_native", "5G53_NECA_miniGs_native_nucleotide_free"]
PROTEIN = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "CYX", "GLN", "GLU", "GLY", "HIS", "HID", "HIE", "HIP",
    "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}
LIGANDS = {"ZMA", "NEC"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def energy(context) -> tuple[float, float]:
    state = context.getState(getEnergy=True)
    return (
        float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)),
        float(state.getKineticEnergy().value_in_unit(unit.kilojoule_per_mole)),
    )


def volume_nm3(state) -> float:
    vectors = state.getPeriodicBoxVectors(asNumpy=True).value_in_unit(unit.nanometer)
    return float(abs(np.linalg.det(np.asarray(vectors))))


def native_contact_fraction(positions, contacts: list[dict], cutoff_angstrom: float = 6.0) -> float:
    xyz = positions.value_in_unit(unit.angstrom)
    retained = 0
    for contact in contacts:
        left = contact["ligand_atom_index"]
        right = contact["receptor_atom_index"]
        retained += np.linalg.norm(xyz[left] - xyz[right]) <= cutoff_angstrom
    return retained / len(contacts) if contacts else 0.0


def run(system_id: str, steps_per_stage: int) -> dict:
    source = INPUT / system_id
    topology_file = source / "positions.pdb"
    system_file = source / "system.xml"
    contacts_file = source / "native_contacts.json"
    pdb = PDBFile(str(topology_file))
    system = XmlSerializer.deserialize(system_file.read_text())
    contacts = json.loads(contacts_file.read_text())["native_contacts"]

    restraint = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    restraint.addGlobalParameter("k", 1000.0 * unit.kilojoule_per_mole / unit.nanometer**2)
    for name in ("x0", "y0", "z0"):
        restraint.addPerParticleParameter(name)
    restrained = 0
    for atom, position in zip(pdb.topology.atoms(), pdb.positions):
        if atom.element.symbol != "H" and (atom.residue.name in PROTEIN or atom.residue.name in LIGANDS):
            restraint.addParticle(atom.index, position.value_in_unit(unit.nanometer))
            restrained += 1
    system.addForce(restraint)
    barostat = mm.MonteCarloMembraneBarostat(
        1.0 * unit.bar, 0.0 * unit.bar * unit.nanometer, 310 * unit.kelvin,
        mm.MonteCarloMembraneBarostat.XYIsotropic,
        mm.MonteCarloMembraneBarostat.ZFree,
        0,
    )
    system.addForce(barostat)
    integrator = mm.LangevinMiddleIntegrator(310 * unit.kelvin, 1 / unit.picosecond, 0.002 * unit.picoseconds)
    integrator.setRandomNumberSeed(20260915)
    simulation = Simulation(pdb.topology, system, integrator, Platform.getPlatformByName("CPU"))
    simulation.context.setPositions(pdb.positions)
    simulation.context.applyConstraints(1e-6)
    initial_pe, _ = energy(simulation.context)
    print(f"{system_id}: minimizing", flush=True)
    simulation.minimizeEnergy(tolerance=100 * unit.kilojoule_per_mole / unit.nanometer, maxIterations=25)
    minimized_pe, _ = energy(simulation.context)
    simulation.context.setVelocitiesToTemperature(310 * unit.kelvin, 20260915)
    print(f"{system_id}: NVT smoke ({steps_per_stage} steps)", flush=True)
    simulation.step(steps_per_stage)
    nvt_state = simulation.context.getState(getEnergy=True, getPositions=True)
    nvt_pe = float(nvt_state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
    nvt_ke = float(nvt_state.getKineticEnergy().value_in_unit(unit.kilojoule_per_mole))
    nvt_volume = volume_nm3(nvt_state)
    nvt_contacts = native_contact_fraction(nvt_state.getPositions(asNumpy=True), contacts)

    barostat.setFrequency(25)
    simulation.context.reinitialize(preserveState=True)
    print(f"{system_id}: membrane-NPT smoke ({steps_per_stage} steps)", flush=True)
    simulation.step(steps_per_stage)
    npt_state = simulation.context.getState(getEnergy=True, getPositions=True)
    npt_pe = float(npt_state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
    npt_ke = float(npt_state.getKineticEnergy().value_in_unit(unit.kilojoule_per_mole))
    npt_volume = volume_nm3(npt_state)
    npt_contacts = native_contact_fraction(npt_state.getPositions(asNumpy=True), contacts)
    coordinates = npt_state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)

    destination = OUTPUT / system_id
    destination.mkdir(parents=True, exist_ok=True)
    state_path = destination / "smoke_final_state.xml"
    system_path = destination / "smoke_system.xml"
    state_path.write_text(XmlSerializer.serialize(npt_state))
    system_path.write_text(XmlSerializer.serialize(system))
    finite = all(math.isfinite(value) for value in [initial_pe, minimized_pe, nvt_pe, nvt_ke, npt_pe, npt_ke, nvt_volume, npt_volume]) and bool(np.all(np.isfinite(coordinates)))
    accepted = finite and minimized_pe < initial_pe and nvt_contacts >= 0.80 and npt_contacts >= 0.80
    return {
        "system_id": system_id,
        "status": "minimization_nvt_npt_smoke_gate_passed" if accepted else "smoke_gate_blocked",
        "purpose": "initialization smoke test only; not equilibration or production sampling",
        "particle_count": system.getNumParticles(),
        "restrained_protein_ligand_heavy_atom_count": restrained,
        "minimization_max_iterations": 25,
        "pre_minimization_constraints_applied": True,
        "steps_per_nvt_npt_stage": steps_per_stage,
        "timestep_femtoseconds": 2.0,
        "initial_potential_energy_kj_mol": initial_pe,
        "minimized_potential_energy_kj_mol": minimized_pe,
        "energy_decreased_during_minimization": minimized_pe < initial_pe,
        "nvt": {"potential_energy_kj_mol": nvt_pe, "kinetic_energy_kj_mol": nvt_ke, "volume_nm3": nvt_volume, "native_contact_fraction_at_6A": nvt_contacts},
        "npt": {"potential_energy_kj_mol": npt_pe, "kinetic_energy_kj_mol": npt_ke, "volume_nm3": npt_volume, "native_contact_fraction_at_6A": npt_contacts},
        "finite_energy_volume_coordinates": finite,
        "barostat": "MonteCarloMembraneBarostat 1 bar, zero surface tension, XY isotropic, Z free",
        "trajectory_production_started": False,
        "tier_a_production_unlocked": False,
        "files": {"smoke_final_state.xml": sha256(state_path), "smoke_system.xml": sha256(system_path)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=["all", *SYSTEMS], default="all")
    parser.add_argument("--steps-per-stage", type=int, default=50)
    parser.add_argument("--aggregate-only", action="store_true")
    args = parser.parse_args()
    selected = SYSTEMS if args.system == "all" else [args.system]
    if args.aggregate_only:
        results = [json.loads((OUTPUT / system_id / "smoke_audit.json").read_text()) for system_id in selected]
    else:
        results = []
        for system_id in selected:
            result = run(system_id, args.steps_per_stage)
            (OUTPUT / system_id / "smoke_audit.json").write_text(json.dumps(result, indent=2) + "\n")
            results.append(result)
    if args.system == "all":
        report = {
            "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "specification_id": "a2a-tier-a-minimization-nvt-npt-smoke-v1.6",
            "candidate_labels_loaded": False, "trajectory_production_started": False,
            "systems": results,
            "passed_count": sum(row["status"] == "minimization_nvt_npt_smoke_gate_passed" for row in results),
            "status": "all_tier_a_smoke_gates_passed" if all(row["status"] == "minimization_nvt_npt_smoke_gate_passed" for row in results) else "tier_a_smoke_gate_blocked",
            "claim_limit": "Smoke success establishes runnable periodic systems only; it does not establish equilibrated or stable trajectories.",
            "next_gate": "Run the frozen staged equilibration protocol, audit density/area/contact stability, then start all three Tier A replicas without best-replica selection.",
            "runner_sha256": sha256(Path(__file__)),
        }
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / "smoke_campaign_audit.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(results[0], indent=2))


if __name__ == "__main__":
    main()
