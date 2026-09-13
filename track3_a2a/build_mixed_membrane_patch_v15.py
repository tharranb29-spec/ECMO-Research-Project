#!/usr/bin/env python3

"""Build and computationally audit a deterministic 70:30 POPC/CHL1 patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openmm import Vec3, unit
from openmm.app import ForceField, Modeller, NoCutoff, PDBFile, PDBxFile, Topology
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
SOURCE_CHOLESTEROL = ROOT / "data" / "raw" / "5NM4.pdb"
OUTPUT = ROOT / "outputs" / "v1.5" / "md" / "membrane_patch"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rotation_between(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    source = source / np.linalg.norm(source)
    target = target / np.linalg.norm(target)
    cross = np.cross(source, target)
    dot = float(np.clip(np.dot(source, target), -1.0, 1.0))
    if np.linalg.norm(cross) < 1e-10:
        if dot > 0:
            return np.eye(3)
        axis = np.array([1.0, 0.0, 0.0])
        if abs(source[0]) > 0.9:
            axis = np.array([0.0, 1.0, 0.0])
        cross = np.cross(source, axis)
        cross /= np.linalg.norm(cross)
        return -np.eye(3) + 2 * np.outer(cross, cross)
    skew = np.array([[0, -cross[2], cross[1]], [cross[2], 0, -cross[0]], [-cross[1], cross[0], 0]])
    return np.eye(3) + skew + skew @ skew * ((1 - dot) / np.dot(cross, cross))


def deposited_cholesterol() -> dict[str, np.ndarray]:
    coordinates = {}
    for line in SOURCE_CHOLESTEROL.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        if line[17:20].strip() != "CLR" or line[21:22] != "A" or int(line[22:26]) != 508:
            continue
        name = line[12:16].strip()
        mapped = {"O1": "O3", "H1": "H3'"}.get(name, name)
        if name.startswith("H") and len(name) >= 3 and name[1:].isdigit() and name[-1] in "123":
            mapped = f"H{name[1:-1]}{'ABC'[int(name[-1]) - 1]}"
        coordinates[mapped] = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]) / 10.0
    return coordinates


def choose_replacements(residues: list, count: int, positions, box_xy: tuple[float, float]) -> list:
    ordered = sorted(
        residues,
        key=lambda residue: hashlib.sha256(f"a2a-membrane-v1.5|{residue.id}".encode()).hexdigest(),
    )
    coordinates = {}
    for residue in residues:
        phosphorus = next(atom for atom in residue.atoms() if atom.name == "P")
        xyz = positions[phosphorus.index].value_in_unit(unit.nanometer)
        coordinates[residue] = np.array([xyz.x, xyz.y])
    for threshold in np.linspace(1.2, 0.5, 15):
        selected = []
        for residue in ordered:
            xy = coordinates[residue]
            separated = True
            for existing in selected:
                delta = np.abs(xy - coordinates[existing])
                delta = np.minimum(delta, np.array(box_xy) - delta)
                if np.linalg.norm(delta) < threshold:
                    separated = False
                    break
            if separated:
                selected.append(residue)
                if len(selected) == count:
                    return selected
    raise RuntimeError("Could not select a spatially distributed cholesterol replacement set")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    forcefield = ForceField("charmm36_2024.xml", "charmm36_2024/water.xml")
    import openmm.app as app
    popc_path = Path(app.__file__).resolve().parent / "data" / "POPC.pdb"
    patch = PDBFile(str(popc_path))
    modeller = Modeller(patch.topology, patch.positions)
    lipid_residues = [residue for residue in modeller.topology.residues() if residue.name == "POP"]
    phosphorus_z = {
        residue: next(modeller.positions[atom.index].z for atom in residue.atoms() if atom.name == "P")
        for residue in lipid_residues
    }
    center_z = float(np.median(list(phosphorus_z.values())))
    upper = [residue for residue in lipid_residues if phosphorus_z[residue] > center_z]
    lower = [residue for residue in lipid_residues if phosphorus_z[residue] <= center_z]
    box = modeller.topology.getPeriodicBoxVectors()
    box_nm = box.value_in_unit(unit.nanometer)
    box_xy = (float(box_nm[0][0]), float(box_nm[1][1]))
    selected = (
        choose_replacements(upper, round(0.30 * len(upper)), modeller.positions, box_xy)
        + choose_replacements(lower, round(0.30 * len(lower)), modeller.positions, box_xy)
    )
    anchors = []
    for residue in selected:
        phosphorus = next(atom for atom in residue.atoms() if atom.name == "P")
        xyz = modeller.positions[phosphorus.index].value_in_unit(unit.nanometer)
        anchors.append((np.array([xyz.x, xyz.y, xyz.z]), 1 if phosphorus_z[residue] > center_z else -1))
    modeller.delete(selected)

    template = forcefield._templates["CHL1"]
    source = deposited_cholesterol()
    expected_names = {atom.name for atom in template.atoms}
    if set(source) != expected_names:
        raise RuntimeError("Deposited cholesterol atoms do not exactly map to the CHARMM CHL1 template")
    source_origin = source["O3"]
    long_axis = source["C25"] - source_origin
    retained_lipid_atoms = np.array([
        modeller.positions[atom.index].value_in_unit(unit.nanometer)
        for atom in modeller.topology.atoms()
        if atom.residue.name == "POP"
    ])
    cholesterol_topology = Topology()
    chain = cholesterol_topology.addChain("C")
    cholesterol_positions = []
    placed_atoms = []
    placement_clearances = []
    for index, (anchor, leaflet) in enumerate(anchors, 1):
        residue = cholesterol_topology.addResidue("CHL1", chain, str(index))
        atoms = []
        target = np.array([0.0, 0.0, -float(leaflet)])
        rotation = rotation_between(long_axis, target)
        occupied = retained_lipid_atoms if not placed_atoms else np.vstack([retained_lipid_atoms, *placed_atoms])
        occupied_tree = cKDTree(occupied)
        best = None
        for step in range(36):
            angle = 2 * math.pi * ((step / 36) + (index * 0.6180339887498949 % 1.0))
            around_z = np.array([[math.cos(angle), -math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1]])
            transform = around_z @ rotation
            for inward_nm in np.linspace(0.0, 1.0, 11):
                for dx in (-0.15, 0.0, 0.15):
                    for dy in (-0.15, 0.0, 0.15):
                        candidate_anchor = anchor + target * inward_nm + np.array([dx, dy, 0.0])
                        candidate = np.array([
                            candidate_anchor + transform @ (source[atom.name] - source_origin)
                            for atom in template.atoms
                        ])
                        clearance = float(np.min(occupied_tree.query(candidate, k=1)[0]))
                        if best is None or clearance > best[0]:
                            best = (clearance, candidate_anchor, transform, candidate)
        assert best is not None
        clearance, selected_anchor, transform, candidate = best
        placement_clearances.append(clearance)
        placed_atoms.append(candidate)
        for atom in template.atoms:
            atoms.append(cholesterol_topology.addAtom(atom.name, atom.element, residue))
            xyz = selected_anchor + transform @ (source[atom.name] - source_origin)
            cholesterol_positions.append(Vec3(*xyz) * unit.nanometer)
        for left, right in template.bonds:
            cholesterol_topology.addBond(atoms[left], atoms[right])
    modeller.add(cholesterol_topology, cholesterol_positions)

    cholesterol_heavy = np.array([
        modeller.positions[atom.index].value_in_unit(unit.nanometer)
        for atom in modeller.topology.atoms()
        if atom.residue.name == "CHL1" and atom.element.symbol != "H"
    ])
    clashing_waters = []
    for residue in modeller.topology.residues():
        if residue.name != "HOH":
            continue
        oxygen = next(residue.atoms())
        xyz = modeller.positions[oxygen.index].value_in_unit(unit.nanometer)
        if float(np.min(np.linalg.norm(cholesterol_heavy - xyz, axis=1))) < 0.24:
            clashing_waters.append(residue)
    modeller.delete(clashing_waters)

    output_pdb = args.output / "POPC_CHL1_70_30_patch.pdb"
    with output_pdb.open("w", encoding="utf-8") as stream:
        PDBFile.writeFile(modeller.topology, modeller.positions, stream, keepIds=True)
    output_cif = args.output / "POPC_CHL1_70_30_patch.cif"
    with output_cif.open("w", encoding="utf-8") as stream:
        PDBxFile.writeFile(modeller.topology, modeller.positions, stream, keepIds=True)
    # A successful System construction is the strongest available template-completeness audit.
    system = forcefield.createSystem(modeller.topology, nonbondedMethod=NoCutoff, constraints=None)
    counts = {}
    for residue in modeller.topology.residues():
        counts[residue.name] = counts.get(residue.name, 0) + 1
    popc_count = counts.get("POP", 0)
    cholesterol_count = counts.get("CHL1", 0)
    fraction = cholesterol_count / (popc_count + cholesterol_count)
    accepted = abs(fraction - 0.30) <= 0.01 and min(placement_clearances) >= 0.10
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": (
            "mixed_membrane_patch_computationally_accepted"
            if accepted else "mixed_membrane_patch_rejected_by_geometry_audit"
        ),
        "source_popc_patch": str(popc_path),
        "source_popc_patch_sha256": sha256(popc_path),
        "source_cholesterol_structure": "5NM4 CLR A 508",
        "source_cholesterol_sha256": sha256(SOURCE_CHOLESTEROL),
        "force_field": "OpenMM 8.6 charmm36_2024.xml and charmm36_2024/water.xml",
        "leaflet_initial_popc": {"upper": len(upper), "lower": len(lower)},
        "leaflet_cholesterol": {
            "upper": sum(leaflet == 1 for _, leaflet in anchors),
            "lower": sum(leaflet == -1 for _, leaflet in anchors),
        },
        "residue_counts": counts,
        "cholesterol_mole_fraction": fraction,
        "target_cholesterol_mole_fraction": 0.30,
        "ratio_absolute_error": abs(fraction - 0.30),
        "removed_clashing_water_count": len(clashing_waters),
        "minimum_placement_clearance_angstrom": min(placement_clearances) * 10.0,
        "atom_count": system.getNumParticles(),
        "all_force_field_templates_resolved": True,
        "visualization_pdb": str(output_pdb.relative_to(ROOT)),
        "visualization_pdb_sha256": sha256(output_pdb),
        "output_cif": str(output_cif.relative_to(ROOT)),
        "output_cif_sha256": sha256(output_cif),
        "accepted_as_custom_addmembrane_patch": accepted,
        "trajectory_production_started": False,
    }
    audit_path = args.output / "patch_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
