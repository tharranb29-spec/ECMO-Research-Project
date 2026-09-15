#!/usr/bin/env python3
"""Transfer audited GAFF2 control ligands into their deposited Tier A poses."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from generate_gaff2_ligand_bundles_v16 import mol2_atoms, mol2_bond_graph
from prepare_tier_a_constructs_v16 import Atom, atoms as pdb_atoms


ROOT = Path(__file__).resolve().parent
MD = ROOT / "outputs" / "v1.6" / "md"
OUTPUT = MD / "native_control_ligands"
CONTROLS = {
    "ZMA": {
        "reference": MD / "tier_a_constructs" / "5NM4_native_reference.pdb",
        "native_residue": "ZMA",
        "protein": MD / "tier_a_constructs" / "minimized" / "5NM4_ADORA2A_minimized_candidate.pdb",
    },
    "NEC": {
        "reference": MD / "tier_a_constructs" / "5G53_native_reference.pdb",
        "native_residue": "NEC",
        "protein": MD / "tier_a_constructs" / "5G53_ADORA2A_miniGs_nucleotide_free_complete_candidate.pdb",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rigid_transform(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    source_center = source.mean(axis=0)
    target_center = target.mean(axis=0)
    covariance = (source - source_center).T @ (target - target_center)
    left, _, right_t = np.linalg.svd(covariance)
    rotation = right_t.T @ left.T
    if np.linalg.det(rotation) < 0:
        right_t[-1, :] *= -1
        rotation = right_t.T @ left.T
    translation = target_center - rotation @ source_center
    fitted = (rotation @ source.T).T + translation
    rmsd = float(np.sqrt(np.mean(np.sum((fitted - target) ** 2, axis=1))))
    return rotation, translation, rmsd


def rewrite_mol2_coordinates(source: Path, destination: Path, coordinates: np.ndarray) -> None:
    lines = source.read_text().splitlines()
    in_atoms = False
    output = []
    index = 0
    for line in lines:
        if line == "@<TRIPOS>ATOM":
            in_atoms = True
            output.append(line)
            continue
        if line.startswith("@<TRIPOS>") and line != "@<TRIPOS>ATOM":
            in_atoms = False
        if in_atoms and line.strip():
            fields = line.split()
            if len(fields) >= 9:
                xyz = coordinates[index]
                fields[2:5] = [f"{value:.6f}" for value in xyz]
                line = " ".join(fields)
                index += 1
        output.append(line)
    if index != len(coordinates):
        raise RuntimeError("MOL2 atom count changed during coordinate transfer")
    destination.write_text("\n".join(output) + "\n")


def mol2_coordinates(path: Path) -> np.ndarray:
    lines = path.read_text().splitlines()
    start = lines.index("@<TRIPOS>ATOM") + 1
    end = lines.index("@<TRIPOS>BOND")
    return np.array([[float(value) for value in line.split()[2:5]] for line in lines[start:end] if line.strip()])


def mol2_bonds(path: Path) -> list[tuple[int, int]]:
    lines = path.read_text().splitlines()
    start = lines.index("@<TRIPOS>BOND") + 1
    bonds = []
    for line in lines[start:]:
        if line.startswith("@<TRIPOS>"):
            break
        fields = line.split()
        if len(fields) >= 4:
            bonds.append((int(fields[1]) - 1, int(fields[2]) - 1))
    return bonds


def native_atoms(path: Path, residue_name: str) -> list:
    parsed = []
    for raw in path.read_text().splitlines():
        line = raw.ljust(80)
        if line[:6].strip() != "HETATM" or line[17:20].strip() != residue_name:
            continue
        parsed.append(Atom(
            name=line[12:16].strip(), residue=line[17:20].strip(), chain=line[21].strip(),
            residue_id=int(line[22:26]), element=(line[76:78].strip() or line[12:14].strip()).upper(),
            xyz=np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
        ))
    return parsed


def map_control(name: str, config: dict) -> dict:
    bundle = MD / "ligand_bundles" / name
    input_atoms = mol2_atoms(bundle / "input.mol2")
    typed_atoms = mol2_atoms(bundle / "ligand_gaff2.mol2")
    native = native_atoms(config["reference"], config["native_residue"])
    input_heavy = [index for index, atom in enumerate(input_atoms) if atom["element"] != "H"]
    native_heavy = [atom for atom in native if atom.element not in {"H", "D"}]
    if len(input_heavy) != len(native_heavy):
        raise RuntimeError(f"{name}: native and parameterized heavy-atom counts differ")
    input_elements = [input_atoms[index]["element"].upper() for index in input_heavy]
    native_elements = [atom.element.upper() for atom in native_heavy]
    if input_elements != native_elements:
        raise RuntimeError(f"{name}: native and parameterized heavy-atom order is not element-identical")

    if len(input_atoms) != len(typed_atoms):
        raise RuntimeError(f"{name}: input and GAFF2 atom counts differ")
    source_xyz = mol2_coordinates(bundle / "input.mol2")
    native_xyz = np.array([atom.xyz for atom in native_heavy])
    rotation, translation, fitted_rmsd = rigid_transform(source_xyz[input_heavy], native_xyz)
    transferred = (rotation @ source_xyz.T).T + translation
    fitted_heavy = transferred[input_heavy].copy()
    transferred[input_heavy] = native_xyz
    heavy_native_by_index = {atom_index: native_xyz[offset] for offset, atom_index in enumerate(input_heavy)}
    heavy_fitted_by_index = {atom_index: fitted_heavy[offset] for offset, atom_index in enumerate(input_heavy)}
    for left, right in mol2_bonds(bundle / "input.mol2"):
        if input_atoms[left]["element"] == "H" and right in heavy_native_by_index:
            transferred[left] += heavy_native_by_index[right] - heavy_fitted_by_index[right]
        elif input_atoms[right]["element"] == "H" and left in heavy_native_by_index:
            transferred[right] += heavy_native_by_index[left] - heavy_fitted_by_index[left]

    output_dir = OUTPUT / name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_mol2 = output_dir / "ligand_gaff2_native_pose.mol2"
    rewrite_mol2_coordinates(bundle / "ligand_gaff2.mol2", output_mol2, transferred)
    if mol2_bond_graph(output_mol2) != mol2_bond_graph(bundle / "ligand_gaff2.mol2"):
        raise RuntimeError(f"{name}: bond graph changed during coordinate transfer")

    protein_heavy = [atom for atom in pdb_atoms(config["protein"]) if atom.element not in {"H", "D"}]
    protein_xyz = np.array([atom.xyz for atom in protein_heavy])
    distances = np.linalg.norm(native_xyz[:, None, :] - protein_xyz[None, :, :], axis=2)
    minimum = float(distances.min())
    contact_count = int(np.sum(distances <= 4.0))
    accepted = minimum >= 1.0 and contact_count > 0
    return {
        "ligand": name,
        "status": "native_pose_mapping_accepted" if accepted else "native_pose_mapping_blocked",
        "native_reference": str(config["reference"].relative_to(ROOT)),
        "native_reference_sha256": sha256(config["reference"]),
        "gaff2_source": str((bundle / "ligand_gaff2.mol2").relative_to(ROOT)),
        "gaff2_source_sha256": sha256(bundle / "ligand_gaff2.mol2"),
        "output": str(output_mol2.relative_to(ROOT)),
        "output_sha256": sha256(output_mol2),
        "atom_count": len(input_atoms),
        "heavy_atom_count": len(input_heavy),
        "heavy_atom_order_element_identical": True,
        "pre_transfer_rigid_fit_rmsd_angstrom": fitted_rmsd,
        "post_transfer_native_heavy_rmsd_angstrom": 0.0,
        "hydrogen_policy": "rigidly align, then translate each hydrogen with its bonded deposited heavy atom before final-system relaxation",
        "minimum_ligand_protein_heavy_distance_angstrom": minimum,
        "native_contact_pair_count_within_4_angstrom": contact_count,
        "bond_graph_preserved": True,
        "trajectory_production_started": False,
    }


def main() -> None:
    results = [map_control(name, config) for name, config in CONTROLS.items()]
    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-tier-a-native-ligand-pose-mapping-v1.6",
        "candidate_labels_loaded": False,
        "systems": results,
        "accepted_count": sum(row["status"] == "native_pose_mapping_accepted" for row in results),
        "status": "all_native_pose_mappings_accepted" if all(row["status"] == "native_pose_mapping_accepted" for row in results) else "native_pose_mapping_blocked",
        "next_gate": "Combine each pose with its audited construct, embed in the frozen Lipid21 membrane, parameterize with tleap, and run final periodic geometry and energy audits.",
        "runner_sha256": sha256(Path(__file__)),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT / "native_pose_mapping_audit.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
