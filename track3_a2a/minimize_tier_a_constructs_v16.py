#!/usr/bin/env python3
"""Restrained implicit-solvent minimization and geometry re-audit for Tier A constructs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openmm import CustomExternalForce, LangevinMiddleIntegrator, Platform, unit
from openmm.app import ForceField, HBonds, NoCutoff, PDBFile, Simulation

from prepare_tier_a_constructs_v16 import audit_construct


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_constructs"
OUTPUT = INPUT / "minimized"
FORCE_FIELD = ["amber19-all.xml", "implicit/obc2.xml"]
BACKBONE = {"N", "CA", "C", "O"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def energy_kj(context) -> float:
    return float(context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))


def minimize(
    source: Path,
    destination: Path,
    system_id: str,
    expected: dict[str, set[int]],
    names: dict[tuple[str, int], str],
    max_iterations: int,
) -> dict:
    print(f"Minimizing {system_id} with max_iterations={max_iterations}", flush=True)
    pdb = PDBFile(str(source))
    forcefield = ForceField(*FORCE_FIELD)
    system = forcefield.createSystem(pdb.topology, nonbondedMethod=NoCutoff, constraints=HBonds)
    restraint = CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    restraint.addGlobalParameter("k", 1000.0 * unit.kilojoule_per_mole / unit.nanometer**2)
    for parameter in ["x0", "y0", "z0"]:
        restraint.addPerParticleParameter(parameter)
    restrained = 0
    for atom, position in zip(pdb.topology.atoms(), pdb.positions):
        if atom.name in BACKBONE and atom.element.symbol != "H":
            restraint.addParticle(atom.index, position.value_in_unit(unit.nanometer))
            restrained += 1
    system.addForce(restraint)
    integrator = LangevinMiddleIntegrator(310 * unit.kelvin, 1 / unit.picosecond, 0.002 * unit.picoseconds)
    platform = Platform.getPlatformByName("CPU")
    simulation = Simulation(pdb.topology, system, integrator, platform)
    simulation.context.setPositions(pdb.positions)
    initial = energy_kj(simulation.context)
    simulation.minimizeEnergy(
        tolerance=10 * unit.kilojoule_per_mole / unit.nanometer,
        maxIterations=max_iterations,
    )
    state = simulation.context.getState(getEnergy=True, getPositions=True)
    final = float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
    final_positions = state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    initial_positions = np.asarray(pdb.positions.value_in_unit(unit.nanometer))
    displacement = np.linalg.norm(final_positions - initial_positions, axis=1)
    with destination.open("w") as stream:
        PDBFile.writeFile(pdb.topology, state.getPositions(), stream, keepIds=True)
    geometry = audit_construct(destination, system_id, expected, names)
    return {
        "system_id": system_id,
        "source": str(source.relative_to(ROOT)),
        "source_sha256": sha256(source),
        "output": str(destination.relative_to(ROOT)),
        "output_sha256": sha256(destination),
        "force_field_files": FORCE_FIELD,
        "solvent_model": "OBC2 implicit solvent for pre-membrane clash relaxation only",
        "restraint_k_kj_mol_nm2": 1000.0,
        "maximum_minimizer_iterations": max_iterations,
        "restrained_backbone_heavy_atom_count": restrained,
        "initial_potential_energy_kj_mol": initial,
        "final_potential_energy_kj_mol": final,
        "energy_decreased": final < initial,
        "maximum_atom_displacement_angstrom": float(displacement.max() * 10.0),
        "median_atom_displacement_angstrom": float(np.median(displacement) * 10.0),
        "geometry_reaudit": geometry,
        "status": "minimized_construct_gate_passed" if final < initial and geometry["geometry_gate_passed"] else "minimized_construct_gate_blocked",
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    jobs = [
        (
            INPUT / "5NM4_ADORA2A_complete_candidate.pdb",
            OUTPUT / "5NM4_ADORA2A_minimized_candidate.pdb",
            "5NM4_ZMA_native",
            {"A": set(range(2, 305))},
            {
                ("A", 54): "ALA", ("A", 88): "THR", ("A", 107): "ARG", ("A", 122): "LYS",
                ("A", 154): "ASN", ("A", 202): "LEU", ("A", 235): "LEU", ("A", 239): "VAL", ("A", 277): "SER",
            },
            1000,
        ),
        (
            INPUT / "5G53_ADORA2A_miniGs_nucleotide_free_complete_candidate.pdb",
            OUTPUT / "5G53_ADORA2A_miniGs_nucleotide_free_minimized_candidate.pdb",
            "5G53_NECA_miniGs_native_nucleotide_free",
            {"B": set(range(6, 306)), "D": set(range(39, 62)) | set(range(193, 255)) | set(range(265, 394))},
            {("B", 154): "ASN"},
            30,
        ),
    ]
    systems = [minimize(*job) for job in jobs]
    passed = sum(system["status"] == "minimized_construct_gate_passed" for system in systems)
    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-md-tier-a-construct-minimization-v1.6",
        "purpose": "pre-membrane computational relaxation; not production dynamics",
        "candidate_labels_loaded": False,
        "trajectory_production_started": False,
        "systems": systems,
        "passed_count": passed,
        "status": "minimized_construct_gate_passed" if passed == len(systems) else "minimized_construct_gate_blocked",
        "next_gate": "Map native ligands, build explicit membrane systems, and rerun energy/geometry audits in the final periodic environment.",
        "runner_sha256": sha256(Path(__file__)),
    }
    report_path = OUTPUT / "minimization_audit.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
