#!/usr/bin/env python3

"""Prepare and align source-locked A2A assets without claiming gate success."""

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "protocol.json"
RAW = ROOT / "data" / "raw"
RECEPTORS = ROOT / "docking_inputs" / "receptors"
LIGANDS = ROOT / "docking_inputs" / "ligands"
OUTPUTS = ROOT / "outputs"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atom_record(line):
    if not line.startswith(("ATOM  ", "HETATM")) or len(line) < 54:
        return None
    try:
        return {
            "record": line[:6].strip(),
            "atom": line[12:16].strip(),
            "altloc": line[16:17],
            "resname": line[17:20].strip(),
            "chain": line[21:22],
            "resseq": int(line[22:26]),
            "xyz": np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
        }
    except ValueError:
        return None


def receptor_lines(path, chain="A"):
    selected = []
    for line in path.read_text(encoding="utf-8").splitlines():
        atom = atom_record(line)
        if not atom or atom["record"] != "ATOM" or atom["chain"] != chain:
            continue
        if not 1 <= atom["resseq"] <= 317 or atom["altloc"] not in {" ", "A"}:
            continue
        selected.append(line)
    if not selected:
        raise ValueError(f"No receptor atoms selected from {path}")
    return selected


def ca_index(lines, tm_ranges):
    index = {}
    for line in lines:
        atom = atom_record(line)
        if atom and atom["atom"] == "CA" and any(start <= atom["resseq"] <= end for start, end in tm_ranges):
            index[(atom["resseq"], atom["resname"])] = atom["xyz"]
    return index


def fit_transform(mobile, reference):
    mobile_center = mobile.mean(axis=0)
    reference_center = reference.mean(axis=0)
    centered_mobile = mobile - mobile_center
    centered_reference = reference - reference_center
    left, _, right_t = np.linalg.svd(centered_mobile.T @ centered_reference)
    rotation = left @ right_t
    if np.linalg.det(rotation) < 0:
        left[:, -1] *= -1
        rotation = left @ right_t
    translation = reference_center - mobile_center @ rotation
    return rotation, translation


def transform_xyz(xyz, rotation, translation):
    return xyz @ rotation + translation


def transform_pdb_lines(lines, rotation, translation):
    transformed = []
    for line in lines:
        atom = atom_record(line)
        xyz = transform_xyz(atom["xyz"], rotation, translation)
        transformed.append(f"{line[:30]}{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}{line[54:]}")
    return transformed


def sdf_coordinates(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    count = int(lines[3][:3])
    coords = []
    for line in lines[4 : 4 + count]:
        coords.append(np.array([float(line[0:10]), float(line[10:20]), float(line[20:30])]))
    return lines, np.array(coords), count


def transform_sdf(source, destination, rotation, translation):
    lines, coords, count = sdf_coordinates(source)
    moved = coords @ rotation + translation
    for index in range(count):
        line = lines[4 + index]
        x, y, z = moved[index]
        lines[4 + index] = f"{x:10.4f}{y:10.4f}{z:10.4f}{line[30:]}"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return moved


def write_pdb(path, lines):
    path.write_text("\n".join(lines + ["TER", "END"]) + "\n", encoding="utf-8")


def box_from_coordinates(coords, padding):
    minimum = coords.min(axis=0) - padding
    maximum = coords.max(axis=0) + padding
    return (minimum + maximum) / 2.0, maximum - minimum


def rounded(values):
    return [round(float(value), 4) for value in values]


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inactive = config["structures"]["inactive"]
    active = config["structures"]["active_like"]
    paths = {
        "inactive_pdb": RAW / "4EIY.pdb",
        "active_pdb": RAW / "2YDO.pdb",
        "inactive_ligand": RAW / "4EIY_ZMA_A2401.sdf",
        "active_ligand": RAW / "2YDO_ADN_A400.sdf",
    }
    expected = {
        "inactive_pdb": inactive["source_sha256"],
        "active_pdb": active["source_sha256"],
        "inactive_ligand": inactive["ligand_sha256"],
        "active_ligand": active["ligand_sha256"],
    }
    checksums = {name: sha256(path) for name, path in paths.items()}
    mismatches = [name for name, value in checksums.items() if value != expected[name]]
    if mismatches:
        raise ValueError(f"Source checksum mismatch: {', '.join(mismatches)}")

    RECEPTORS.mkdir(parents=True, exist_ok=True)
    LIGANDS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    inactive_lines = receptor_lines(paths["inactive_pdb"])
    active_lines = receptor_lines(paths["active_pdb"])
    tm_ranges = config["alignment"]["tm_ranges"]
    inactive_ca = ca_index(inactive_lines, tm_ranges)
    active_ca = ca_index(active_lines, tm_ranges)
    common = sorted(set(inactive_ca) & set(active_ca))
    if len(common) < 100:
        raise ValueError(f"Insufficient common TM C-alpha atoms for alignment: {len(common)}")
    reference = np.array([inactive_ca[key] for key in common])
    mobile = np.array([active_ca[key] for key in common])
    rotation, translation = fit_transform(mobile, reference)
    fitted = mobile @ rotation + translation
    alignment_rmsd = float(np.sqrt(np.mean(np.sum((fitted - reference) ** 2, axis=1))))

    inactive_out = RECEPTORS / "4EIY_inactive_aligned.pdb"
    active_out = RECEPTORS / "2YDO_active_like_aligned.pdb"
    write_pdb(inactive_out, inactive_lines)
    write_pdb(active_out, transform_pdb_lines(active_lines, rotation, translation))

    inactive_ligand_out = LIGANDS / "4EIY_ZMA_crystal.sdf"
    active_ligand_out = LIGANDS / "2YDO_ADN_crystal_aligned.sdf"
    shutil.copyfile(paths["inactive_ligand"], inactive_ligand_out)
    _, inactive_coords, _ = sdf_coordinates(inactive_ligand_out)
    active_coords = transform_sdf(paths["active_ligand"], active_ligand_out, rotation, translation)
    center, size = box_from_coordinates(inactive_coords, float(config["box"]["padding_angstrom"]))
    half = size / 2.0
    active_inside = bool(np.all(np.abs(active_coords - center) <= half + 1e-6))

    status = {
        "protocol_id": config["protocol_id"],
        "stage": "source_locked_and_aligned",
        "redocking_gate_passed": False,
        "production_screening_unlocked": False,
        "source_checksums_verified": True,
        "source_checksums": checksums,
        "alignment": {
            "reference": "4EIY",
            "mobile": "2YDO",
            "common_tm_ca_count": len(common),
            "post_alignment_rmsd_angstrom": round(alignment_rmsd, 4),
            "rotation_matrix": [[round(float(value), 8) for value in row] for row in rotation],
            "translation": rounded(translation),
        },
        "shared_box": {
            "center": rounded(center),
            "size": rounded(size),
            "padding_angstrom": config["box"]["padding_angstrom"],
            "aligned_adenosine_inside": active_inside,
        },
        "prepared_assets": {
            "inactive_receptor_pdb": str(inactive_out.relative_to(ROOT)),
            "active_like_receptor_pdb": str(active_out.relative_to(ROOT)),
            "inactive_reference_ligand_sdf": str(inactive_ligand_out.relative_to(ROOT)),
            "active_like_reference_ligand_sdf": str(active_ligand_out.relative_to(ROOT)),
        },
        "next_gate": "prepare receptor PDBQT files and run five-seed cognate redocking",
    }
    if not active_inside:
        status["stage"] = "alignment_or_box_review_required"
        status["next_gate"] = "review box transfer because aligned adenosine is outside the shared box"
    (OUTPUTS / "preparation_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()

