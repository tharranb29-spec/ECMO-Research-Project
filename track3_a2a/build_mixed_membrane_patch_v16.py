#!/usr/bin/env python3
"""Build and audit the frozen Amber Lipid21 70:30 POPC/cholesterol patch."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm.app as app
from openmm import Vec3, unit
from openmm.app import ForceField, Modeller, NoCutoff, PDBFile, PDBxFile, Topology
from scipy.spatial import cKDTree

from build_mixed_membrane_patch_v15 import choose_replacements, deposited_cholesterol, rotation_between


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "membrane_patch"
FORCE_FIELD_FILES = ["amber19/lipid21.xml", "amber14/tip3p.xml"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    forcefield = ForceField(*FORCE_FIELD_FILES)
    popc_path = Path(app.__file__).resolve().parent / "data" / "POPC.pdb"
    patch = PDBFile(str(popc_path))
    modeller = Modeller(patch.topology, patch.positions)
    lipids = [residue for residue in modeller.topology.residues() if residue.name == "POP"]
    phosphorus_z = {
        residue: next(modeller.positions[atom.index].z for atom in residue.atoms() if atom.name == "P")
        for residue in lipids
    }
    center_z = float(np.median(list(phosphorus_z.values())))
    upper = [residue for residue in lipids if phosphorus_z[residue] > center_z]
    lower = [residue for residue in lipids if phosphorus_z[residue] <= center_z]
    box_nm = modeller.topology.getPeriodicBoxVectors().value_in_unit(unit.nanometer)
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
    if set(source) != {atom.name for atom in template.atoms}:
        raise RuntimeError("Deposited cholesterol does not exactly map to the Lipid21 CHL1 template")
    source_origin = source["O3"]
    long_axis = source["C25"] - source_origin
    retained_lipid_atoms = np.array([
        modeller.positions[atom.index].value_in_unit(unit.nanometer)
        for atom in modeller.topology.atoms() if atom.residue.name == "POP"
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
            around_z = np.array([
                [math.cos(angle), -math.sin(angle), 0],
                [math.sin(angle), math.cos(angle), 0],
                [0, 0, 1],
            ])
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

    # The source POPC patch is tightly packed.  Remove any POPC with a true
    # sub-1 A heavy-atom overlap with inserted cholesterol, then remove the same
    # number from the opposite leaflet to preserve a symmetric composition.
    cholesterol_heavy = np.array([
        modeller.positions[atom.index].value_in_unit(unit.nanometer)
        for atom in modeller.topology.atoms()
        if atom.residue.name == "CHL1" and atom.element.symbol != "H"
    ])
    clashing_popc = []
    popc_by_leaflet = {1: [], -1: []}
    for residue in modeller.topology.residues():
        if residue.name != "POP":
            continue
        phosphorus = next(atom for atom in residue.atoms() if atom.name == "P")
        leaflet = 1 if modeller.positions[phosphorus.index].z > center_z else -1
        popc_by_leaflet[leaflet].append(residue)
        heavy_xyz = np.array([
            modeller.positions[atom.index].value_in_unit(unit.nanometer)
            for atom in residue.atoms() if atom.element.symbol != "H"
        ])
        if float(np.min(cKDTree(cholesterol_heavy).query(heavy_xyz, k=1)[0])) < 0.10:
            clashing_popc.append(residue)
    removed_by_leaflet = {
        leaflet: sum(residue in clashing_popc for residue in residues)
        for leaflet, residues in popc_by_leaflet.items()
    }
    balanced_target = max(removed_by_leaflet.values())
    balance_popc = []
    for leaflet, residues in popc_by_leaflet.items():
        needed = balanced_target - removed_by_leaflet[leaflet]
        eligible = [residue for residue in residues if residue not in clashing_popc]
        eligible.sort(key=lambda residue: hashlib.sha256(f"a2a-lipid21-balance-v1.6|{residue.id}".encode()).hexdigest())
        balance_popc.extend(eligible[:needed])
    deleted_popc = clashing_popc + balance_popc
    modeller.delete(deleted_popc)

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

    final_cholesterol_heavy = np.array([
        modeller.positions[atom.index].value_in_unit(unit.nanometer)
        for atom in modeller.topology.atoms()
        if atom.residue.name == "CHL1" and atom.element.symbol != "H"
    ])
    final_popc_heavy = np.array([
        modeller.positions[atom.index].value_in_unit(unit.nanometer)
        for atom in modeller.topology.atoms()
        if atom.residue.name == "POP" and atom.element.symbol != "H"
    ])
    final_heavy_clearance = float(cKDTree(final_popc_heavy).query(final_cholesterol_heavy, k=1)[0].min())
    nonwater_heavy_atoms = [
        atom for atom in modeller.topology.atoms()
        if atom.element.symbol != "H" and atom.residue.name != "HOH"
    ]
    nonwater_heavy_xyz = np.array([
        modeller.positions[atom.index].value_in_unit(unit.nanometer)
        for atom in nonwater_heavy_atoms
    ])
    cross_residue_clashes = [
        (left, right) for left, right in cKDTree(nonwater_heavy_xyz).query_pairs(0.10)
        if nonwater_heavy_atoms[left].residue is not nonwater_heavy_atoms[right].residue
    ]

    output_pdb = OUTPUT / "POPC_CHL1_70_30_Lipid21_patch.pdb"
    output_cif = OUTPUT / "POPC_CHL1_70_30_Lipid21_patch.cif"
    with output_pdb.open("w", encoding="utf-8") as stream:
        PDBFile.writeFile(modeller.topology, modeller.positions, stream, keepIds=True)
    with output_cif.open("w", encoding="utf-8") as stream:
        PDBxFile.writeFile(modeller.topology, modeller.positions, stream, keepIds=True)
    system = forcefield.createSystem(modeller.topology, nonbondedMethod=NoCutoff, constraints=None)
    counts = Counter(residue.name for residue in modeller.topology.residues())
    popc_count = counts.get("POP", 0)
    cholesterol_count = counts.get("CHL1", 0)
    fraction = cholesterol_count / (popc_count + cholesterol_count)
    accepted = (
        abs(fraction - 0.30) <= 0.01
        and final_heavy_clearance >= 0.10
        and not cross_residue_clashes
    )
    audit = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-amber-lipid21-mixed-membrane-v1.6",
        "status": "mixed_membrane_patch_computationally_accepted" if accepted else "mixed_membrane_patch_rejected",
        "force_field_files": FORCE_FIELD_FILES,
        "source_popc_patch": str(popc_path),
        "source_popc_patch_sha256": sha256(popc_path),
        "source_cholesterol_structure": "5NM4 CLR A 508",
        "leaflet_initial_popc": {"upper": len(upper), "lower": len(lower)},
        "leaflet_cholesterol": {
            "upper": sum(leaflet == 1 for _, leaflet in anchors),
            "lower": sum(leaflet == -1 for _, leaflet in anchors),
        },
        "residue_counts": dict(sorted(counts.items())),
        "cholesterol_mole_fraction": fraction,
        "target_cholesterol_mole_fraction": 0.30,
        "ratio_absolute_error": abs(fraction - 0.30),
        "removed_clashing_water_count": len(clashing_waters),
        "initial_minimum_all_atom_placement_clearance_angstrom": min(placement_clearances) * 10.0,
        "removed_clashing_popc_count": len(clashing_popc),
        "removed_balance_popc_count": len(balance_popc),
        "removed_popc_by_leaflet_before_balance": removed_by_leaflet,
        "minimum_final_cholesterol_popc_heavy_clearance_angstrom": final_heavy_clearance * 10.0,
        "cross_residue_nonwater_heavy_clash_count_below_1_angstrom": len(cross_residue_clashes),
        "particle_count": system.getNumParticles(),
        "all_lipid21_templates_resolved": True,
        "accepted_as_custom_addmembrane_patch": accepted,
        "trajectory_production_started": False,
        "files": {
            "pdb": {"path": str(output_pdb.relative_to(ROOT)), "sha256": sha256(output_pdb)},
            "cif": {"path": str(output_cif.relative_to(ROOT)), "sha256": sha256(output_cif)},
        },
    }
    audit_path = OUTPUT / "patch_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
