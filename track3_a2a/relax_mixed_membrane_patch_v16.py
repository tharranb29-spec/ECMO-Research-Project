#!/usr/bin/env python3
"""Restrained relaxation of the accepted Lipid21 mixed-membrane patch."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import Platform, unit
from openmm.app import CutoffPeriodic, ForceField, HBonds, PDBFile, PDBxFile, Simulation
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "outputs" / "v1.6" / "md" / "membrane_patch" / "POPC_CHL1_70_30_Lipid21_patch.cif"
OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "membrane_patch"
FORCE_FIELD_FILES = ["amber19/lipid21.xml", "amber14/tip3p.xml"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def energy(context) -> float:
    return float(context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))


def cross_residue_minimum(topology, positions, heavy_only: bool) -> tuple[float, int]:
    atoms = [
        atom for atom in topology.atoms()
        if atom.residue.name != "HOH" and (not heavy_only or atom.element.symbol != "H")
    ]
    xyz = np.array([
        positions[atom.index].value_in_unit(unit.nanometer) for atom in atoms
    ])
    tree = cKDTree(xyz)
    closest = math.inf
    below_one = 0
    for left, right in tree.query_pairs(0.10):
        if atoms[left].residue is atoms[right].residue:
            continue
        distance = float(np.linalg.norm(xyz[left] - xyz[right]))
        closest = min(closest, distance)
        below_one += 1
    if math.isinf(closest):
        # Query a wider shell only to report the nearest pair when no sub-1 A pair exists.
        for left, right in tree.query_pairs(0.30):
            if atoms[left].residue is atoms[right].residue:
                continue
            closest = min(closest, float(np.linalg.norm(xyz[left] - xyz[right])))
    return closest * 10.0, below_one


def main() -> None:
    pdb = PDBxFile(str(INPUT))
    forcefield = ForceField(*FORCE_FIELD_FILES)
    system = forcefield.createSystem(
        pdb.topology, nonbondedMethod=CutoffPeriodic, nonbondedCutoff=1.0 * unit.nanometer,
        constraints=HBonds, rigidWater=True,
    )
    restraint = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    restraint.addGlobalParameter("k", 1000.0 * unit.kilojoule_per_mole / unit.nanometer**2)
    for name in ("x0", "y0", "z0"):
        restraint.addPerParticleParameter(name)
    restrained = 0
    for atom, position in zip(pdb.topology.atoms(), pdb.positions):
        if atom.residue.name != "HOH" and atom.element.symbol != "H":
            restraint.addParticle(atom.index, position.value_in_unit(unit.nanometer))
            restrained += 1
    system.addForce(restraint)
    integrator = mm.LangevinMiddleIntegrator(310 * unit.kelvin, 1 / unit.picosecond, 0.001 * unit.picoseconds)
    simulation = Simulation(pdb.topology, system, integrator, Platform.getPlatformByName("CPU"))
    simulation.context.setPositions(pdb.positions)
    initial_energy = energy(simulation.context)
    print(f"Initial patch energy: {initial_energy:.3f} kJ/mol", flush=True)
    simulation.minimizeEnergy(tolerance=50 * unit.kilojoule_per_mole / unit.nanometer, maxIterations=200)
    state = simulation.context.getState(getEnergy=True, getPositions=True)
    final_energy = float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
    final_positions = state.getPositions()
    output_cif = OUTPUT / "POPC_CHL1_70_30_Lipid21_patch_relaxed.cif"
    output_pdb = OUTPUT / "POPC_CHL1_70_30_Lipid21_patch_relaxed.pdb"
    with output_cif.open("w") as stream:
        PDBxFile.writeFile(pdb.topology, final_positions, stream, keepIds=True)
    with output_pdb.open("w") as stream:
        PDBFile.writeFile(pdb.topology, final_positions, stream, keepIds=True)
    all_minimum, all_below = cross_residue_minimum(pdb.topology, final_positions, False)
    heavy_minimum, heavy_below = cross_residue_minimum(pdb.topology, final_positions, True)
    accepted = final_energy < initial_energy and math.isfinite(final_energy) and heavy_below == 0 and all_minimum >= 0.60
    audit = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-amber-lipid21-patch-relaxation-v1.6",
        "status": "relaxed_membrane_patch_accepted" if accepted else "relaxed_membrane_patch_blocked",
        "force_field_files": FORCE_FIELD_FILES,
        "restraint_k_kj_mol_nm2": 1000.0,
        "restrained_lipid_heavy_atom_count": restrained,
        "maximum_minimizer_iterations": 200,
        "initial_potential_energy_kj_mol": initial_energy,
        "final_potential_energy_kj_mol": final_energy,
        "energy_decreased": final_energy < initial_energy,
        "minimum_cross_residue_nonwater_all_atom_distance_angstrom": all_minimum,
        "cross_residue_nonwater_all_atom_pair_count_below_1_angstrom": all_below,
        "minimum_cross_residue_nonwater_heavy_distance_angstrom": heavy_minimum,
        "cross_residue_nonwater_heavy_pair_count_below_1_angstrom": heavy_below,
        "trajectory_production_started": False,
        "files": {
            "source": {"path": str(INPUT.relative_to(ROOT)), "sha256": sha256(INPUT)},
            "cif": {"path": str(output_cif.relative_to(ROOT)), "sha256": sha256(output_cif)},
            "pdb": {"path": str(output_pdb.relative_to(ROOT)), "sha256": sha256(output_pdb)},
        },
    }
    audit_path = OUTPUT / "patch_relaxation_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    if not accepted:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
