#!/usr/bin/env python3

"""Align and validate the mandatory 4EIY inactive-structure sensitivity."""

import json
import subprocess
from pathlib import Path

import numpy as np

from track3_a2a.prepare_a2a_gate import (
    atom_record,
    fit_transform,
    sha256,
    sdf_coordinates,
    transform_pdb_lines,
    transform_sdf,
    write_pdb,
)
from track3_a2a.run_redocking_gate import run_case


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs" / "v1.2" / "4eiy_sensitivity"
RECEPTORS = ROOT / "docking_inputs" / "v1.2" / "4eiy_sensitivity" / "receptors"
LIGANDS = ROOT / "docking_inputs" / "v1.2" / "4eiy_sensitivity" / "ligands"


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


def main():
    protocol = json.loads((ROOT / "config" / "protocol.v1.1.json").read_text())
    original = json.loads((ROOT / "config" / "protocol.json").read_text())
    preparation = json.loads((ROOT / "outputs" / "v1.1.1" / "preparation_status.json").read_text())
    expected = original["structures"]["inactive"]
    source_receptor = RAW / "4EIY.pdb"
    source_ligand = RAW / "4EIY_ZMA_A2401.sdf"
    if sha256(source_receptor) != expected["source_sha256"] or sha256(source_ligand) != expected["ligand_sha256"]:
        raise ValueError("4EIY source checksum mismatch")

    ranges = protocol["alignment"]["tm_ranges_uniprot"]
    reference_spec = protocol["structures"]["inactive_primary"]
    reference_lines, reference_ca = mapped_receptor(
        RAW / "5NM4.pdb", reference_spec["uniprot_mapping"], ranges
    )
    sensitivity_mapping = [
        {"pdb_start": 2, "pdb_end": 208, "uniprot_start": 2},
        {"pdb_start": 219, "pdb_end": 316, "uniprot_start": 219},
    ]
    mobile_lines, mobile_ca = mapped_receptor(source_receptor, sensitivity_mapping, ranges)
    common = sorted(set(reference_ca) & set(mobile_ca))
    reference = np.asarray([reference_ca[key] for key in common])
    mobile = np.asarray([mobile_ca[key] for key in common])
    rotation, translation = fit_transform(mobile, reference)
    fitted = mobile @ rotation + translation
    alignment_rmsd = float(np.sqrt(np.mean(np.sum((fitted - reference) ** 2, axis=1))))
    if len(common) < protocol["alignment"]["minimum_common_tm_ca_atoms"]:
        raise ValueError(f"Insufficient common TM atoms: {len(common)}")
    if alignment_rmsd > protocol["alignment"]["maximum_alignment_rmsd_angstrom"]:
        raise ValueError(f"4EIY alignment RMSD {alignment_rmsd:.4f} A exceeds limit")

    RECEPTORS.mkdir(parents=True, exist_ok=True)
    LIGANDS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    aligned_receptor = RECEPTORS / "4EIY_inactive_aligned_to_5NM4.pdb"
    aligned_ligand = LIGANDS / "4EIY_ZMA_aligned_to_5NM4.sdf"
    write_pdb(aligned_receptor, transform_pdb_lines(mobile_lines, rotation, translation))
    ligand_coordinates = transform_sdf(source_ligand, aligned_ligand, rotation, translation)
    box = preparation["shared_box"]
    center = np.asarray(box["center"])
    size = np.asarray(box["size"])
    ligand_inside = bool(np.all(np.abs(ligand_coordinates - center) <= size / 2.0 + 1e-6))
    if not ligand_inside:
        raise ValueError("Aligned 4EIY cognate ligand falls outside the frozen 5NM4 box")

    prepared_receptor = RECEPTORS / "4EIY_inactive_aligned_to_5NM4_ph7.4.pdb"
    prepared_pqr = RECEPTORS / "4EIY_inactive_aligned_to_5NM4_ph7.4.pqr"
    command = [
        str(PROJECT_ROOT / ".venv-pdb2pqr" / "bin" / "pdb2pqr"),
        "--ff=AMBER", "--ffout=AMBER", "--keep-chain", "--drop-water",
        "--titration-state-method=propka", "--with-ph=7.4",
        f"--pdb-output={prepared_receptor}", str(aligned_receptor), str(prepared_pqr),
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    (OUT / "pdb2pqr.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError("4EIY PDB2PQR preparation failed")

    case = run_case("4EIY-v1.2-aligned-sensitivity", prepared_receptor, aligned_ligand, box, protocol)
    report = {
        "schema_version": 1,
        "protocol_id": "a2a-4eiy-aligned-sensitivity-v1.2",
        "role": "mandatory inactive-structure sensitivity; never substitutes for 5NM4 primary",
        "original_4eiy_gate_failure_preserved": True,
        "source_hashes": {"receptor": sha256(source_receptor), "ligand": sha256(source_ligand)},
        "alignment": {
            "reference": "5NM4",
            "mobile": "4EIY",
            "common_tm_ca_count": len(common),
            "rmsd_angstrom": round(alignment_rmsd, 4),
            "cognate_ligand_inside_frozen_box": ligand_inside,
        },
        "redocking": case,
        "production_sensitivity_authorized": case["status"] == "pass",
        "interpretation": "A failed gate remains a structure-sensitivity limitation; it must not be tuned after seeing downstream labels.",
    }
    (OUT / "preparation_and_redocking_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
