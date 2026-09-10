#!/usr/bin/env python3

"""Prepare the frozen 5NM4/2YDO v1.1 receptor pair and shared box."""

import json
import subprocess
from pathlib import Path

import numpy as np

from prepare_a2a_gate import (
    atom_record,
    box_from_coordinates,
    fit_transform,
    receptor_lines,
    rounded,
    sdf_coordinates,
    sha256,
    transform_pdb_lines,
    transform_sdf,
    write_pdb,
)


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "config" / "protocol.v1.1.json"
RAW = ROOT / "data" / "raw"
RECEPTORS = ROOT / "docking_inputs" / "v1.1" / "receptors"
LIGANDS = ROOT / "docking_inputs" / "v1.1" / "ligands"
OUTPUTS = ROOT / "outputs" / "v1.1"


def mapped_receptor(path, segments, tm_ranges):
    lines = []
    ca = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        atom = atom_record(line)
        if not atom or atom["record"] != "ATOM" or atom["chain"] != "A" or atom["altloc"] not in {" ", "A"}:
            continue
        uniprot_position = None
        for segment in segments:
            if segment["pdb_start"] <= atom["resseq"] <= segment["pdb_end"]:
                uniprot_position = segment["uniprot_start"] + atom["resseq"] - segment["pdb_start"]
                break
        if uniprot_position is None:
            continue
        lines.append(line)
        if atom["atom"] == "CA" and any(start <= uniprot_position <= end for start, end in tm_ranges):
            ca[(uniprot_position, atom["resname"])] = atom["xyz"]
    if not lines:
        raise ValueError(f"No mapped receptor atoms found in {path}")
    return lines, ca


def prepare_pdb2pqr(source, prefix):
    pdb_output = RECEPTORS / f"{prefix}_ph7.4.pdb"
    pqr_output = RECEPTORS / f"{prefix}_ph7.4.pqr"
    log_output = OUTPUTS / f"{prefix}_pdb2pqr.log"
    command = [
        str(PROJECT_ROOT / ".venv-pdb2pqr" / "bin" / "pdb2pqr"),
        "--ff=AMBER", "--ffout=AMBER", "--keep-chain", "--drop-water",
        "--titration-state-method=propka", "--with-ph=7.4",
        f"--pdb-output={pdb_output}", str(source), str(pqr_output),
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    log_output.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"PDB2PQR failed for {prefix}; see {log_output}")
    return pdb_output, pqr_output, log_output


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inactive = config["structures"]["inactive_primary"]
    active = config["structures"]["active_like_primary"]
    source_paths = {
        "inactive_pdb": RAW / "5NM4.pdb",
        "inactive_ligand": RAW / "5NM4_ZMA_A507.sdf",
        "active_pdb": RAW / "2YDO.pdb",
        "active_ligand": RAW / "2YDO_ADN_A400.sdf",
    }
    expected = {
        "inactive_pdb": inactive["source_sha256"],
        "inactive_ligand": inactive["ligand_sha256"],
        "active_pdb": active["source_sha256"],
        "active_ligand": active["ligand_sha256"],
    }
    checksums = {name: sha256(path) for name, path in source_paths.items()}
    mismatches = [name for name, value in checksums.items() if value != expected[name]]
    if mismatches:
        raise ValueError(f"Source checksum mismatch: {', '.join(mismatches)}")

    RECEPTORS.mkdir(parents=True, exist_ok=True)
    LIGANDS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    ranges = config["alignment"]["tm_ranges_uniprot"]
    inactive_lines, inactive_ca = mapped_receptor(source_paths["inactive_pdb"], inactive["uniprot_mapping"], ranges)
    active_lines, active_ca = mapped_receptor(source_paths["active_pdb"], active["uniprot_mapping"], ranges)
    common = sorted(set(inactive_ca) & set(active_ca))
    if len(common) < config["alignment"]["minimum_common_tm_ca_atoms"]:
        raise ValueError(f"Only {len(common)} common mapped TM C-alpha atoms")
    reference = np.array([inactive_ca[key] for key in common])
    mobile = np.array([active_ca[key] for key in common])
    rotation, translation = fit_transform(mobile, reference)
    fitted = mobile @ rotation + translation
    alignment_rmsd = float(np.sqrt(np.mean(np.sum((fitted - reference) ** 2, axis=1))))
    if alignment_rmsd > config["alignment"]["maximum_alignment_rmsd_angstrom"]:
        raise ValueError(f"Alignment RMSD {alignment_rmsd:.4f} A exceeds protocol maximum")

    inactive_aligned = RECEPTORS / "5NM4_inactive_aligned.pdb"
    active_aligned = RECEPTORS / "2YDO_active_like_aligned.pdb"
    write_pdb(inactive_aligned, inactive_lines)
    write_pdb(active_aligned, transform_pdb_lines(active_lines, rotation, translation))
    inactive_ligand = LIGANDS / "5NM4_ZMA_crystal.sdf"
    active_ligand = LIGANDS / "2YDO_ADN_crystal_aligned.sdf"
    inactive_ligand.write_bytes(source_paths["inactive_ligand"].read_bytes())
    _, inactive_coords, _ = sdf_coordinates(inactive_ligand)
    active_coords = transform_sdf(source_paths["active_ligand"], active_ligand, rotation, translation)
    center, size = box_from_coordinates(inactive_coords, config["box"]["padding_angstrom"])
    active_inside = bool(np.all(np.abs(active_coords - center) <= size / 2.0 + 1e-6))
    if not active_inside:
        raise ValueError("Aligned adenosine is outside the shared 5NM4-derived box")

    inactive_prepared, inactive_pqr, inactive_log = prepare_pdb2pqr(inactive_aligned, "5NM4_inactive")
    active_prepared, active_pqr, active_log = prepare_pdb2pqr(active_aligned, "2YDO_active_like")
    status = {
        "protocol_id": config["protocol_id"],
        "stage": "source_locked_aligned_and_protonated",
        "source_checksums_verified": True,
        "redocking_gate_passed": False,
        "model_training_unlocked": False,
        "production_screening_unlocked": False,
        "alignment": {
            "reference": "5NM4",
            "mobile": "2YDO",
            "mapping_basis": "DBREF to UniProt P29274",
            "common_tm_ca_count": len(common),
            "post_alignment_rmsd_angstrom": round(alignment_rmsd, 4),
        },
        "shared_box": {
            "center": rounded(center),
            "size": rounded(size),
            "padding_angstrom": config["box"]["padding_angstrom"],
            "aligned_adenosine_inside": active_inside,
        },
        "assets": {
            "inactive_receptor": str(inactive_prepared.relative_to(ROOT)),
            "active_like_receptor": str(active_prepared.relative_to(ROOT)),
            "inactive_reference_ligand": str(inactive_ligand.relative_to(ROOT)),
            "active_like_reference_ligand": str(active_ligand.relative_to(ROOT)),
            "inactive_pqr": str(inactive_pqr.relative_to(ROOT)),
            "active_like_pqr": str(active_pqr.relative_to(ROOT)),
            "preparation_logs": [str(inactive_log.relative_to(ROOT)), str(active_log.relative_to(ROOT))],
        },
        "next_gate": "five-seed v1.1 cognate redocking",
    }
    (OUTPUTS / "preparation_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()

