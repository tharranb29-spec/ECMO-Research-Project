#!/usr/bin/env python3

"""Test pose selection on 5NM4 after explicit DBREF-to-UniProt mapping."""

import json
import subprocess
from pathlib import Path

import numpy as np

from prepare_a2a_gate import (
    atom_record,
    ca_index,
    fit_transform,
    receptor_lines,
    sha256,
    transform_pdb_lines,
    transform_sdf,
    write_pdb,
)
from run_redocking_gate import run_case


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
RAW = ROOT / "data" / "raw"
RECEPTORS = ROOT / "docking_inputs" / "receptors"
LIGANDS = ROOT / "docking_inputs" / "ligands"
OUTPUTS = ROOT / "outputs"


def five_nm4_receptor_and_ca(path, tm_ranges):
    """Select ADORA2A atoms and map 5NM4 author numbering to UniProt P29274."""
    lines = []
    ca = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        atom = atom_record(line)
        if not atom or atom["record"] != "ATOM" or atom["chain"] != "A" or atom["altloc"] not in {" ", "A"}:
            continue
        if 11 <= atom["resseq"] <= 217:
            uniprot_position = atom["resseq"] - 9
        elif 324 <= atom["resseq"] <= 422:
            uniprot_position = atom["resseq"] - 105
        else:
            continue
        lines.append(line)
        if atom["atom"] == "CA" and any(start <= uniprot_position <= end for start, end in tm_ranges):
            ca[(uniprot_position, atom["resname"])] = atom["xyz"]
    if not lines:
        raise ValueError("No ADORA2A atoms selected from 5NM4 DBREF segments.")
    return lines, ca


def main():
    config = json.loads((ROOT / "config" / "protocol.json").read_text(encoding="utf-8"))
    status = json.loads((OUTPUTS / "preparation_status.json").read_text(encoding="utf-8"))
    ranges = config["alignment"]["tm_ranges"]
    reference_lines = receptor_lines(RAW / "4EIY.pdb")
    reference_index = ca_index(reference_lines, ranges)
    mobile_lines, mobile_index = five_nm4_receptor_and_ca(RAW / "5NM4.pdb", ranges)
    common = sorted(set(reference_index) & set(mobile_index))
    if len(common) < 150:
        raise SystemExit(f"Invalid sequence mapping: only {len(common)} common TM C-alpha atoms.")
    reference = np.array([reference_index[key] for key in common])
    mobile = np.array([mobile_index[key] for key in common])
    rotation, translation = fit_transform(mobile, reference)
    fitted = mobile @ rotation + translation
    alignment_rmsd = float(np.sqrt(np.mean(np.sum((fitted - reference) ** 2, axis=1))))
    if alignment_rmsd > 3.0:
        raise SystemExit(f"Invalid structural alignment RMSD: {alignment_rmsd:.4f} A.")

    aligned_receptor = RECEPTORS / "5NM4_inactive_diagnostic_aligned.pdb"
    aligned_ligand = LIGANDS / "5NM4_ZMA_diagnostic_aligned.sdf"
    write_pdb(aligned_receptor, transform_pdb_lines(mobile_lines, rotation, translation))
    transform_sdf(RAW / "5NM4_ZMA_A507.sdf", aligned_ligand, rotation, translation)

    prepared_receptor = RECEPTORS / "5NM4_inactive_diagnostic_ph7.4.pdb"
    prepared_pqr = RECEPTORS / "5NM4_inactive_diagnostic_ph7.4.pqr"
    preparation_log = OUTPUTS / "5NM4_pdb2pqr.log"
    command = [
        str(PROJECT_ROOT / ".venv-pdb2pqr" / "bin" / "pdb2pqr"),
        "--ff=AMBER", "--ffout=AMBER", "--keep-chain", "--drop-water",
        "--titration-state-method=propka", "--with-ph=7.4",
        f"--pdb-output={prepared_receptor}", str(aligned_receptor), str(prepared_pqr),
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    preparation_log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise SystemExit(f"5NM4 PDB2PQR failed; see {preparation_log}")

    case = run_case("5NM4-diagnostic", prepared_receptor, aligned_ligand, status["shared_box"], config)
    report = {
        "status": case["status"],
        "validity": "valid_secondary_diagnostic",
        "role": "independent_inactive_structure_diagnostic_not_primary_gate",
        "primary_4EIY_result_preserved": True,
        "source": {
            "pdb_id": "5NM4",
            "resolution_angstrom": 1.70,
            "source_pdb_sha256": sha256(RAW / "5NM4.pdb"),
            "source_ligand_sha256": sha256(RAW / "5NM4_ZMA_A507.sdf"),
        },
        "sequence_mapping": {
            "method": "PDB DBREF segments mapped to UniProt P29274",
            "segments": ["PDB 11-217 -> UniProt 2-208", "PDB 324-422 -> UniProt 219-317"],
        },
        "alignment": {
            "reference": "4EIY",
            "common_tm_ca_count": len(common),
            "post_alignment_rmsd_angstrom": round(alignment_rmsd, 4),
        },
        "redocking": case,
        "interpretation_rule": (
            "Assess transferability of pose selection only. Do not replace the registered 4EIY "
            "endpoint based on favorable performance."
        ),
    }
    (OUTPUTS / "5NM4_diagnostic_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

