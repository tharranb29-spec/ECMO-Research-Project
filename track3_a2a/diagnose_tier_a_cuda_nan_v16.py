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


def run_case(source: Path, system_id: str, precision: str, extras: str) -> dict:
    pdb = PDBFile(str(source / "positions.pdb"))
    system = XmlSerializer.deserialize((source / "system.xml").read_text())
    state, _ = equil.read_smoke_state(source, system_id)
    if extras in {"restraints", "restraints_and_disabled_barostat"}:
        equil.add_restraints(system, pdb)
    if extras == "restraints_and_disabled_barostat":
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
        simulation.context.applyConstraints(1e-6)
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
        for step in range(1, 11):
            simulation.step(1)
            check = simulation.context.getState(getEnergy=True, getPositions=True)
            coordinates = check.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
            energy = float(check.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
            if not np.all(np.isfinite(coordinates)) or not math.isfinite(energy):
                raise RuntimeError(f"non-finite state at diagnostic step {step}")
        result.update({"status": "ten_step_cuda_probe_passed", "completed_steps": 10})
    except Exception as exc:
        result.update({"status": "cuda_probe_failed", "error_type": type(exc).__name__, "error": str(exc)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", default="5NM4_ZMA_native", choices=json.loads(equil.CONFIG_PATH.read_text())["systems"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = equil.materialize_bundle(args.system, args.output / "_inputs")
    cases = [
        run_case(source, args.system, precision, extras)
        for precision in ("mixed", "double")
        for extras in ("base", "restraints", "restraints_and_disabled_barostat")
    ]
    report = {
        "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-tier-a-cuda-nan-isolation-v1.6.1",
        "system_id": args.system, "purpose": "diagnostic only; no equilibration or production trajectory",
        "cases": cases,
    }
    destination = args.output / args.system / "cuda_nan_diagnostic.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
