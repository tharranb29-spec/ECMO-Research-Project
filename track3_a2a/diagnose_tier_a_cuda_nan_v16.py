#!/usr/bin/env python3
"""Isolate immediate CUDA NaNs without launching an equilibration trajectory."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import Platform, XmlSerializer, unit
from openmm.app import PDBFile, Simulation

import run_tier_a_equilibration_v16 as equil


def run_case(source: Path, system_id: str, precision: str, extras: str, steps: int) -> dict:
    pdb = PDBFile(str(source / "positions.pdb"))
    system = XmlSerializer.deserialize((source / "system.xml").read_text())
    state, _ = equil.read_smoke_state(source, system_id)
    restraint = None
    reference_positions = None
    if extras in {"restraints", "restraints_and_disabled_barostat"}:
        restraint, _ = equil.add_restraints(system, pdb)
        reference_positions = pdb.positions
    elif extras == "smoke_referenced_restraints_and_disabled_barostat":
        reference_positions = state.getPositions()
        restraint, _ = equil.add_restraints(system, pdb, reference_positions)
    if restraint is not None:
        restraint.setForceGroup(31)
    if extras in {"restraints_and_disabled_barostat", "smoke_referenced_restraints_and_disabled_barostat"}:
        system.addForce(mm.MonteCarloMembraneBarostat(
            1.0 * unit.bar, 0.0 * unit.bar * unit.nanometer, 310 * unit.kelvin,
            mm.MonteCarloMembraneBarostat.XYIsotropic,
            mm.MonteCarloMembraneBarostat.ZFree,
            0,
        ))
    duplicate_constraints = 0
    pairs = set()
    for index in range(system.getNumConstraints()):
        left, right, _ = system.getConstraintParameters(index)
        pair = tuple(sorted((int(left), int(right))))
        duplicate_constraints += pair in pairs
        pairs.add(pair)
    integrator = mm.LangevinMiddleIntegrator(100 * unit.kelvin, 1 / unit.picosecond, 0.25 * unit.femtoseconds)
    integrator.setConstraintTolerance(1e-6)
    integrator.setRandomNumberSeed(20260914)
    result = {"precision": precision, "extras": extras, "duplicate_constraint_pairs": duplicate_constraints}
    try:
        simulation = Simulation(
            pdb.topology, system, integrator, Platform.getPlatformByName("CUDA"),
            {"Precision": precision},
        )
        simulation.context.setPeriodicBoxVectors(*state.getPeriodicBoxVectors())
        simulation.context.setPositions(state.getPositions())
        before_constraints = simulation.context.getState(getEnergy=True, getPositions=True, groups=1 << 31)
        before_xyz = before_constraints.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
        reference_xyz = reference_positions.value_in_unit(unit.nanometer) if reference_positions is not None else before_xyz
        result["maximum_reference_displacement_before_constraints_nm"] = float(np.max(np.linalg.norm(before_xyz - reference_xyz, axis=1)))
        result["restraint_energy_before_constraints_kj_mol"] = float(
            before_constraints.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        ) if restraint is not None else 0.0
        simulation.context.applyConstraints(1e-6)
        after_constraints = simulation.context.getState(getEnergy=True, getPositions=True, groups=1 << 31)
        after_xyz = after_constraints.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
        result["maximum_constraint_projection_displacement_nm"] = float(np.max(np.linalg.norm(after_xyz - before_xyz, axis=1)))
        result["restraint_energy_after_constraints_kj_mol"] = float(
            after_constraints.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        ) if restraint is not None else 0.0
        simulation.context.setVelocitiesToTemperature(100 * unit.kelvin, 20260914)
        simulation.context.applyVelocityConstraints(1e-6)
        initial = simulation.context.getState(getEnergy=True, getForces=True, getPositions=True)
        forces = initial.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole / unit.nanometer)
        norms = np.linalg.norm(forces, axis=1)
        top = np.argsort(norms)[-5:][::-1]
        atoms = list(pdb.topology.atoms())
        result.update({
            "initial_potential_energy_kj_mol": float(initial.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)),
            "maximum_force_kj_mol_nm": float(norms[top[0]]),
            "top_force_atoms": [
                {"index": int(i), "force_kj_mol_nm": float(norms[i]), "atom": atoms[i].name,
                 "residue": atoms[i].residue.name, "residue_id": atoms[i].residue.id}
                for i in top
            ],
        })
        for step in range(1, steps + 1):
            simulation.step(1)
            check = simulation.context.getState(getEnergy=True, getPositions=True)
            coordinates = check.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
            energy = float(check.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
            if not np.all(np.isfinite(coordinates)) or not math.isfinite(energy):
                raise RuntimeError(f"non-finite state at diagnostic step {step}")
        result.update({"status": "cuda_probe_passed", "completed_steps": steps})
    except Exception as exc:
        result.update({"status": "cuda_probe_failed", "error_type": type(exc).__name__, "error": str(exc)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", default="5NM4_ZMA_native", choices=json.loads(equil.CONFIG_PATH.read_text())["systems"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--corrected-only", action="store_true")
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    source = equil.materialize_bundle(args.system, args.output / "_inputs")
    if args.corrected_only:
        cases = [run_case(source, args.system, "mixed", "smoke_referenced_restraints_and_disabled_barostat", args.steps)]
    else:
        cases = [
            run_case(source, args.system, precision, extras, args.steps)
            for precision in ("mixed", "double")
            for extras in ("base", "restraints", "restraints_and_disabled_barostat")
        ]
    report = {
        "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-tier-a-cuda-nan-isolation-v1.6.4",
        "system_id": args.system, "purpose": "diagnostic only; no equilibration or production trajectory",
        "cases": cases,
    }
    destination = args.output / args.system / "cuda_nan_diagnostic.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
