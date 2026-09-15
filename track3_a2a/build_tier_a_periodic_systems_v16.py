#!/usr/bin/env python3
"""Assemble, parameterize, and audit the two periodic Tier A systems."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import Platform, XmlSerializer, unit
from openmm.app import (
    AmberPrmtopFile, ForceField, HBonds,
    Modeller, NoCutoff, PDBFile, PDBxFile, PME, Simulation,
)
from scipy.spatial import cKDTree

from build_mixed_membrane_patch_v15 import rotation_between
from map_native_control_ligands_v16 import mol2_coordinates, rigid_transform


ROOT = Path(__file__).resolve().parent
MD = ROOT / "outputs" / "v1.6" / "md"
OUTPUT = MD / "tier_a_periodic_systems"
PATCH = MD / "membrane_patch" / "POPC_CHL1_70_30_Lipid21_patch_relaxed.cif"
FORCE_FIELD_FILES = ["amber19/protein.ff19SB.xml", "amber19/lipid21.xml", "amber14/tip3p.xml"]
TM_RANGES = [(7, 35), (45, 73), (79, 109), (119, 146), (170, 199), (229, 258), (267, 292)]
CONTROLS = {
    "5NM4_ZMA_native": {"ligand": "ZMA", "protein_chain": "A"},
    "5G53_NECA_miniGs_native_nucleotide_free": {"ligand": "NEC", "protein_chain": "B"},
}
PROTEIN_RESIDUES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "CYX", "GLN", "GLU", "GLY", "HIS", "HID", "HIE", "HIP",
    "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vec_array(positions, target_unit=unit.nanometer) -> np.ndarray:
    values = positions.value_in_unit(target_unit)
    return np.array([[value.x, value.y, value.z] for value in values])


def quantity_positions(values: np.ndarray):
    return [mm.Vec3(*row) for row in values] * unit.nanometer


def ca_coordinates(pdb: PDBFile, chain_id: str, allowed: set[int] | None = None) -> dict[int, np.ndarray]:
    xyz = vec_array(pdb.positions)
    result = {}
    for atom in pdb.topology.atoms():
        if atom.name != "CA" or atom.residue.chain.id != chain_id:
            continue
        residue_id = int(atom.residue.id)
        if allowed is None or residue_id in allowed:
            result[residue_id] = xyz[atom.index]
    return result


def tm_ids() -> set[int]:
    return {value for start, end in TM_RANGES for value in range(start, end + 1)}


def inactive_orientation(reference: PDBFile) -> tuple[np.ndarray, np.ndarray, dict]:
    ca = ca_coordinates(reference, "A", tm_ids())
    ids = sorted(ca)
    coordinates = np.array([ca[value] for value in ids])
    center = coordinates.mean(axis=0)
    covariance = np.cov((coordinates - center).T)
    _, vectors = np.linalg.eigh(covariance)
    axis = vectors[:, -1]
    all_ca = ca_coordinates(reference, "A")
    n_mean = np.mean([all_ca[value] for value in all_ca if value <= 10], axis=0)
    c_mean = np.mean([all_ca[value] for value in all_ca if value >= 293], axis=0)
    if np.dot(axis, n_mean - c_mean) < 0:
        axis *= -1
    rotation = rotation_between(axis, np.array([0.0, 0.0, 1.0]))
    return rotation, center, {
        "method": "largest principal axis of declared seven-TM CA coordinates",
        "tm_ca_count": len(ids),
        "extracellular_sign_rule": "N-terminal CA centroid mapped toward positive z",
        "source_axis": axis.tolist(),
    }


def transforms() -> dict[str, dict]:
    inactive_path = MD / "tier_a_complex_preflight" / "5NM4_ZMA_native" / "protein.pdb"
    active_path = MD / "tier_a_complex_preflight" / "5G53_NECA_miniGs_native_nucleotide_free" / "protein.pdb"
    inactive = PDBFile(str(inactive_path))
    active = PDBFile(str(active_path))
    orient_rotation, orient_center, orientation_audit = inactive_orientation(inactive)
    inactive_tm = ca_coordinates(inactive, "A", tm_ids())
    active_tm = ca_coordinates(active, "B", tm_ids())
    common = sorted(set(inactive_tm) & set(active_tm))
    active_rotation, active_translation, active_rmsd = rigid_transform(
        np.array([active_tm[value] for value in common]),
        np.array([inactive_tm[value] for value in common]),
    )
    return {
        "5NM4_ZMA_native": {
            "align_rotation": np.eye(3), "align_translation": np.zeros(3),
            "orient_rotation": orient_rotation, "orient_center": orient_center,
            "audit": orientation_audit | {"state_alignment_rmsd_nm": 0.0},
        },
        "5G53_NECA_miniGs_native_nucleotide_free": {
            "align_rotation": active_rotation, "align_translation": active_translation,
            "orient_rotation": orient_rotation, "orient_center": orient_center,
            "audit": orientation_audit | {"state_alignment_ca_count": len(common), "state_alignment_rmsd_nm": active_rmsd},
        },
    }


def apply_transform(values: np.ndarray, transform: dict) -> np.ndarray:
    aligned = (transform["align_rotation"] @ values.T).T + transform["align_translation"]
    return (transform["orient_rotation"] @ (aligned - transform["orient_center"]).T).T


def ligand_topology_and_positions(ligand: str, transform: dict):
    ligand_bundle = MD / "ligand_bundles" / ligand
    topology_pdb = PDBFile(str(ligand_bundle / "ligand_parameterized.pdb"))
    native = mol2_coordinates(MD / "native_control_ligands" / ligand / "ligand_gaff2_native_pose.mol2") / 10.0
    if topology_pdb.topology.getNumAtoms() != len(native):
        raise RuntimeError(f"{ligand}: ligand topology and coordinate counts differ")
    return topology_pdb.topology, quantity_positions(apply_transform(native, transform))


def remove_ligand_overlaps(modeller: Modeller, ligand_xyz_nm: np.ndarray) -> dict:
    ligand_tree = cKDTree(ligand_xyz_nm)
    delete = []
    counts = Counter()
    for residue in modeller.topology.residues():
        if residue.name in PROTEIN_RESIDUES:
            continue
        atoms = list(residue.atoms())
        xyz = np.array([
            modeller.positions[atom.index].value_in_unit(unit.nanometer)
            for atom in atoms if atom.element.symbol != "H"
        ])
        cutoff = 0.22 if residue.name == "HOH" else 0.12
        if len(xyz) and float(ligand_tree.query(xyz, k=1)[0].min()) < cutoff:
            delete.append(residue)
            counts[residue.name] += 1
    modeller.delete(delete)
    return dict(sorted(counts.items()))


def append_ligand_system(base: mm.System, ligand: mm.System) -> int:
    offset = base.getNumParticles()
    for index in range(ligand.getNumParticles()):
        base.addParticle(ligand.getParticleMass(index))
    for index in range(ligand.getNumConstraints()):
        left, right, distance = ligand.getConstraintParameters(index)
        base.addConstraint(left + offset, right + offset, distance)

    base_by_type = {type(force): force for force in base.getForces()}
    for source in ligand.getForces():
        if isinstance(source, mm.CMMotionRemover):
            continue
        target = base_by_type.get(type(source))
        if target is None:
            raise RuntimeError(f"base system has no force compatible with {type(source).__name__}")
        if isinstance(source, mm.HarmonicBondForce):
            for index in range(source.getNumBonds()):
                left, right, length, k = source.getBondParameters(index)
                target.addBond(left + offset, right + offset, length, k)
        elif isinstance(source, mm.HarmonicAngleForce):
            for index in range(source.getNumAngles()):
                a, b, c, angle, k = source.getAngleParameters(index)
                target.addAngle(a + offset, b + offset, c + offset, angle, k)
        elif isinstance(source, mm.PeriodicTorsionForce):
            for index in range(source.getNumTorsions()):
                a, b, c, d, periodicity, phase, k = source.getTorsionParameters(index)
                target.addTorsion(a + offset, b + offset, c + offset, d + offset, periodicity, phase, k)
        elif isinstance(source, mm.NonbondedForce):
            for index in range(source.getNumParticles()):
                target.addParticle(*source.getParticleParameters(index))
            for index in range(source.getNumExceptions()):
                left, right, charge, sigma, epsilon = source.getExceptionParameters(index)
                target.addException(left + offset, right + offset, charge, sigma, epsilon)
        else:
            raise RuntimeError(f"unsupported ligand force {type(source).__name__}")
    return offset


def geometry_and_contacts(topology, positions, ligand_resname: str) -> dict:
    xyz = vec_array(positions, unit.angstrom)
    atoms = list(topology.atoms())
    ligand = [atom for atom in atoms if atom.residue.name == ligand_resname and atom.element.symbol != "H"]
    receptor = [atom for atom in atoms if atom.residue.name in PROTEIN_RESIDUES and atom.element.symbol != "H"]
    ligand_xyz = xyz[[atom.index for atom in ligand]]
    receptor_xyz = xyz[[atom.index for atom in receptor]]
    distances = np.linalg.norm(ligand_xyz[:, None, :] - receptor_xyz[None, :, :], axis=2)
    contacts = []
    for left, right in zip(*np.where(distances <= 4.0)):
        contacts.append({
            "ligand_atom_index": ligand[left].index,
            "receptor_atom_index": receptor[right].index,
            "starting_distance_angstrom": float(distances[left, right]),
        })
    nonwater_heavy = [atom for atom in atoms if atom.element.symbol != "H" and atom.residue.name != "HOH"]
    heavy_xyz = xyz[[atom.index for atom in nonwater_heavy]]
    bonded = {frozenset((left.index, right.index)) for left, right in topology.bonds()}
    clashes = []
    for left, right in cKDTree(heavy_xyz).query_pairs(1.0):
        atom_left, atom_right = nonwater_heavy[left], nonwater_heavy[right]
        if atom_left.residue is atom_right.residue or frozenset((atom_left.index, atom_right.index)) in bonded:
            continue
        clashes.append({"left": str(atom_left), "right": str(atom_right), "distance_angstrom": float(np.linalg.norm(heavy_xyz[left] - heavy_xyz[right]))})
    return {"native_contacts": contacts, "severe_nonwater_heavy_clashes_below_1_angstrom": clashes}


def build(system_id: str, config: dict, transform: dict) -> dict:
    bundle = OUTPUT / system_id
    bundle.mkdir(parents=True, exist_ok=True)
    normalized_complex_path = MD / "tier_a_complex_preflight" / system_id / "complex.pdb"
    normalized_complex = PDBFile(str(normalized_complex_path))
    protein_only = Modeller(normalized_complex.topology, normalized_complex.positions)
    protein_only.delete([
        residue for residue in protein_only.topology.residues() if residue.name == config["ligand"]
    ])
    protein_positions = quantity_positions(apply_transform(vec_array(protein_only.positions), transform))
    modeller = Modeller(protein_only.topology, protein_positions)
    forcefield = ForceField(*FORCE_FIELD_FILES)
    patch = PDBxFile(str(PATCH))
    modeller.addMembrane(
        forcefield, lipidType=patch, minimumPadding=1.0 * unit.nanometer,
        ionicStrength=0.15 * unit.molar, neutralize=True,
        positiveIon="Na+", negativeIon="Cl-", platform=Platform.getPlatformByName("CPU"),
    )

    ligand_topology, ligand_positions = ligand_topology_and_positions(config["ligand"], transform)
    removed = remove_ligand_overlaps(modeller, vec_array(ligand_positions))
    modeller.add(ligand_topology, ligand_positions)
    ligand_prmtop = AmberPrmtopFile(str(MD / "ligand_bundles" / config["ligand"] / "ligand.prmtop"))
    ligand_system = ligand_prmtop.createSystem(nonbondedMethod=NoCutoff, constraints=HBonds)
    base_atom_count = modeller.topology.getNumAtoms() - ligand_topology.getNumAtoms()
    base_topology = Modeller(modeller.topology, modeller.positions)
    base_topology.delete([list(base_topology.topology.residues())[-1]])
    base_system = forcefield.createSystem(
        base_topology.topology, nonbondedMethod=PME, nonbondedCutoff=1.0 * unit.nanometer,
        constraints=HBonds, rigidWater=True,
    )
    offset = append_ligand_system(base_system, ligand_system)
    if offset != base_atom_count or base_system.getNumParticles() != modeller.topology.getNumAtoms():
        raise RuntimeError("particle order/count mismatch after ligand-system merge")

    geometry = geometry_and_contacts(modeller.topology, modeller.positions, config["ligand"])
    counts = Counter(residue.name for residue in modeller.topology.residues())
    lipid_total = counts.get("POP", 0) + counts.get("CHL1", 0)
    cholesterol_fraction = counts.get("CHL1", 0) / lipid_total
    integrator = mm.VerletIntegrator(0.001 * unit.picoseconds)
    simulation = Simulation(modeller.topology, base_system, integrator, Platform.getPlatformByName("CPU"))
    simulation.context.setPositions(modeller.positions)
    initial_energy = float(simulation.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))

    system_path = bundle / "system.xml"
    topology_path = bundle / "topology.cif"
    positions_path = bundle / "positions.pdb"
    contacts_path = bundle / "native_contacts.json"
    system_path.write_text(XmlSerializer.serialize(base_system))
    with topology_path.open("w") as stream:
        PDBxFile.writeFile(modeller.topology, modeller.positions, stream, keepIds=False)
    with positions_path.open("w") as stream:
        PDBFile.writeFile(modeller.topology, modeller.positions, stream, keepIds=False)
    contacts_path.write_text(json.dumps({
        "schema_version": 1, "system_id": system_id, "distance_cutoff_angstrom": 4.0,
        "native_contacts": geometry["native_contacts"], "source_topology_sha256": sha256(topology_path),
    }, indent=2) + "\n")
    accepted = (
        math.isfinite(initial_energy) and not geometry["severe_nonwater_heavy_clashes_below_1_angstrom"]
        and len(geometry["native_contacts"]) > 0 and abs(cholesterol_fraction - 0.30) <= 0.02
    )
    return {
        "system_id": system_id,
        "status": "periodic_assembly_gate_passed" if accepted else "periodic_assembly_gate_blocked",
        "orientation": transform["audit"],
        "force_field_files": FORCE_FIELD_FILES,
        "particle_count": base_system.getNumParticles(),
        "residue_counts": dict(sorted(counts.items())),
        "cholesterol_mole_fraction": cholesterol_fraction,
        "removed_ligand_overlap_residues": removed,
        "initial_potential_energy_kj_mol": initial_energy,
        "finite_initial_energy": math.isfinite(initial_energy),
        "native_contact_count": len(geometry["native_contacts"]),
        "severe_nonwater_heavy_clash_count_below_1_angstrom": len(geometry["severe_nonwater_heavy_clashes_below_1_angstrom"]),
        "severe_nonwater_heavy_clashes_below_1_angstrom": geometry["severe_nonwater_heavy_clashes_below_1_angstrom"],
        "trajectory_production_started": False,
        "files": {path.name: sha256(path) for path in [system_path, topology_path, positions_path, contacts_path]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=["all", *CONTROLS], default="all")
    parser.add_argument("--aggregate-only", action="store_true", help="Aggregate existing per-system audits without rebuilding")
    parser.add_argument("--normalize-exports", action="store_true", help="Rewrite existing coordinate exports with normalized atom IDs")
    args = parser.parse_args()
    selected = CONTROLS if args.system == "all" else {args.system: CONTROLS[args.system]}
    if args.normalize_exports:
        if args.system != "all":
            raise RuntimeError("--normalize-exports requires --system all")
        for system_id in selected:
            bundle = OUTPUT / system_id
            pdb_path = bundle / "positions.pdb"
            cif_path = bundle / "topology.cif"
            parsed = PDBFile(str(pdb_path))
            with cif_path.open("w") as stream:
                PDBxFile.writeFile(parsed.topology, parsed.positions, stream, keepIds=False)
            audit_path = bundle / "assembly_audit.json"
            audit = json.loads(audit_path.read_text())
            audit["coordinate_export_ids_normalized"] = True
            audit["files"]["topology.cif"] = sha256(cif_path)
            audit_path.write_text(json.dumps(audit, indent=2) + "\n")
        args.aggregate_only = True
    if args.aggregate_only:
        if args.system != "all":
            raise RuntimeError("--aggregate-only requires --system all")
        results = [
            json.loads((OUTPUT / system_id / "assembly_audit.json").read_text())
            for system_id in selected
        ]
    else:
        all_transforms = transforms()
        results = []
        for system_id, config in selected.items():
            print(f"Building periodic system {system_id}", flush=True)
            results.append(build(system_id, config, all_transforms[system_id]))
            (OUTPUT / system_id / "assembly_audit.json").write_text(json.dumps(results[-1], indent=2) + "\n")
    if args.system == "all":
        report = {
            "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "specification_id": "a2a-tier-a-periodic-system-assembly-v1.6",
            "candidate_labels_loaded": False, "trajectory_production_started": False,
            "systems": results,
            "passed_count": sum(row["status"] == "periodic_assembly_gate_passed" for row in results),
            "status": "all_periodic_assembly_gates_passed" if all(row["status"] == "periodic_assembly_gate_passed" for row in results) else "periodic_assembly_gate_blocked",
            "next_gate": "Run restrained minimization, staged NVT, and semi-isotropic NPT smoke tests; Tier A production remains locked.",
            "runner_sha256": sha256(Path(__file__)),
        }
        (OUTPUT / "periodic_assembly_audit.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(results[0], indent=2))


if __name__ == "__main__":
    main()
