#!/usr/bin/env python3

"""Audit the pinned OpenMM and bundled CHARMM36m/lipid runtime for v1.5."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy
import openmm
from openmm import Context, HarmonicBondForce, Platform, System, VerletIntegrator, Vec3, unit
from openmm.app import ForceField
import openmm.app


ROOT = Path(__file__).resolve().parent
REQUIREMENTS = ROOT / "requirements-md.txt"
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.5" / "md" / "environment_audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_platform(name: str) -> dict:
    try:
        system = System()
        system.addParticle(12.0)
        system.addParticle(12.0)
        force = HarmonicBondForce()
        force.addBond(0, 1, 0.1, 100.0)
        system.addForce(force)
        integrator = VerletIntegrator(0.001)
        context = Context(system, integrator, Platform.getPlatformByName(name))
        context.setPositions([Vec3(0, 0, 0), Vec3(0.11, 0, 0)] * unit.nanometer)
        state = context.getState(getEnergy=True, getForces=True)
        energy = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        del context, integrator
        return {"status": "usable", "test_energy_kj_mol": round(float(energy), 8)}
    except Exception as exc:  # platform availability is host-specific
        return {"status": "unavailable", "reason": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    data_dir = Path(openmm.app.__file__).resolve().parent / "data"
    forcefield_path = data_dir / "charmm36_2024.xml"
    water_path = data_dir / "charmm36_2024" / "water.xml"
    forcefield = ForceField(str(forcefield_path), str(water_path))
    required_templates = ["POPC", "CHL1", "GDP", "TIP3"]
    template_status = {name: name in forcefield._templates for name in required_templates}

    root = ET.parse(forcefield_path).getroot()
    sources = []
    for element in root.findall("./Info/Source"):
        source = element.attrib.get("Source", "")
        if any(token in source for token in ("top_all36_prot.rtf", "par_all36m_prot.prm", "top_all36_lipid.rtf", "par_all36_lipid.prm", "top_all36_cgenff.rtf", "par_all36_cgenff.prm", "lipid_cholesterol.str")):
            sources.append({"path": source, **element.attrib})

    platform_results = {
        Platform.getPlatform(index).getName(): test_platform(Platform.getPlatform(index).getName())
        for index in range(Platform.getNumPlatforms())
    }
    accelerated = [name for name in ("CUDA", "HIP", "OpenCL") if platform_results.get(name, {}).get("status") == "usable"]
    core_ready = (
        openmm.__version__ == "8.6"
        and all(template_status.values())
        and platform_results.get("CPU", {}).get("status") == "usable"
        and platform_results.get("Reference", {}).get("status") == "usable"
    )
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-md-environment-v1.5",
        "status": "openmm_and_core_force_fields_audited" if core_ready else "environment_audit_failed",
        "runtime": {
            "python": platform.python_version(),
            "python_executable": sys.executable,
            "operating_system": platform.platform(),
            "machine": platform.machine(),
            "numpy": numpy.__version__,
            "openmm": openmm.__version__,
            "openmm_git_revision": getattr(openmm.version, "git_revision", None),
            "openbabel": importlib.metadata.version("openbabel"),
            "pdbfixer": importlib.metadata.version("pdbfixer"),
        },
        "platforms": platform_results,
        "accelerated_platforms": accelerated,
        "production_compute_status": "accelerator_available" if accelerated else "cpu_only_not_suitable_for_full_3_microsecond_campaign",
        "force_field": {
            "primary_xml": str(forcefield_path),
            "primary_xml_sha256": sha256(forcefield_path),
            "water_xml": str(water_path),
            "water_xml_sha256": sha256(water_path),
            "required_template_status": template_status,
            "selected_source_package": "toppar_c36_jul24.tgz",
            "selected_protein_parameter_set": "CHARMM36m",
            "selected_lipid_parameter_set": "CHARMM36 July 2024",
            "selected_water_model": "CHARMM-modified TIP3P",
            "selected_sources": sources,
        },
        "requirements": {
            "path": str(REQUIREMENTS.relative_to(ROOT)),
            "sha256": sha256(REQUIREMENTS),
        },
        "custom_ligand_parameter_status": "not_generated_or_audited",
        "remaining_gates": [
            "generate and independently inspect CGenFF parameters and penalty scores for NEC, ZMA, and all four candidates",
            "obtain an accelerated OpenMM execution host before the full 3 microsecond campaign",
            "build and validate the prepared protein, membrane, solvent, and ion systems",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not core_ready:
        raise SystemExit("OpenMM environment audit failed")


if __name__ == "__main__":
    main()
