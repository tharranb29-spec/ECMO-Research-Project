#!/usr/bin/env python3

"""Benchmark local OpenMM CPU throughput without starting project trajectories."""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import openmm as mm
from openmm import app, unit


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "v1.5" / "md" / "openmm_cpu_benchmark.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--box-nm", type=float, default=6.0)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    modeller = app.Modeller(app.Topology(), [])
    forcefield = app.ForceField("charmm36_2024/water.xml")
    edge = args.box_nm
    modeller.addSolvent(
        forcefield,
        boxSize=mm.Vec3(edge, edge, edge) * unit.nanometer,
        ionicStrength=0.15 * unit.molar,
        neutralize=True,
        model="tip3p",
    )
    system = forcefield.createSystem(
        modeller.topology,
        nonbondedMethod=app.PME,
        nonbondedCutoff=1.0 * unit.nanometer,
        constraints=app.HBonds,
        rigidWater=True,
    )
    integrator = mm.LangevinMiddleIntegrator(
        310 * unit.kelvin,
        1 / unit.picosecond,
        2 * unit.femtoseconds,
    )
    cpu = mm.Platform.getPlatformByName("CPU")
    simulation = app.Simulation(
        modeller.topology,
        system,
        integrator,
        cpu,
        {"Threads": str(args.threads)},
    )
    simulation.context.setPositions(modeller.positions)
    simulation.minimizeEnergy(maxIterations=20)
    simulation.context.setVelocitiesToTemperature(310 * unit.kelvin, 20260913)
    simulation.step(50)
    start = time.perf_counter()
    simulation.step(args.steps)
    elapsed = time.perf_counter() - start
    simulated_ns = args.steps * 0.000002
    ns_per_day = simulated_ns / elapsed * 86400
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "benchmark_complete_no_project_trajectory_started",
        "platform": "CPU",
        "cpu_threads": args.threads,
        "host_platform": platform.platform(),
        "openmm_version": mm.version.short_version,
        "force_field": "charmm36_2024/water.xml",
        "periodic_box_nm": [edge, edge, edge],
        "atom_count": modeller.topology.getNumAtoms(),
        "steps": args.steps,
        "timestep_fs": 2.0,
        "elapsed_seconds": round(elapsed, 6),
        "throughput_ns_per_day": round(ns_per_day, 6),
        "estimated_days_per_100ns_at_benchmark_size": round(100 / ns_per_day, 3),
        "estimated_serial_days_per_3us_at_benchmark_size": round(3000 / ns_per_day, 3),
        "interpretation": (
            "This water box is much smaller than either planned receptor-membrane control. "
            "Its timing is an optimistic upper bound; production should use accelerated compute."
        ),
        "trajectory_production_started": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
