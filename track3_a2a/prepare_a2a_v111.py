#!/usr/bin/env python3

"""Apply the v1.1.1 heavy-atom box correction after v1.1 preparation."""

import contextlib
import io
import json
from pathlib import Path

import numpy as np

from prepare_a2a_gate import rounded
from prepare_a2a_v11 import main as prepare_v11


ROOT = Path(__file__).resolve().parent
SOURCE_LIGAND = ROOT / "data" / "raw" / "5NM4_ZMA_A507.sdf"
V11_STATUS = ROOT / "outputs" / "v1.1" / "preparation_status.json"
OUTPUTS = ROOT / "outputs" / "v1.1.1"


def heavy_atom_coordinates(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    atom_count = int(lines[3][:3])
    coordinates = []
    for line in lines[4 : 4 + atom_count]:
        if line[31:34].strip().upper() == "H":
            continue
        coordinates.append([float(line[0:10]), float(line[10:20]), float(line[20:30])])
    return np.array(coordinates)


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        prepare_v11()
    status = json.loads(V11_STATUS.read_text(encoding="utf-8"))
    coordinates = heavy_atom_coordinates(SOURCE_LIGAND)
    padding = float(status["shared_box"]["padding_angstrom"])
    minimum = coordinates.min(axis=0) - padding
    maximum = coordinates.max(axis=0) + padding
    status["protocol_id"] = "a2a-dual-state-v1.1.1"
    status["stage"] = "source_locked_aligned_protonated_box_corrected"
    status["shared_box"] = {
        "center": rounded((minimum + maximum) / 2.0),
        "size": rounded(maximum - minimum),
        "padding_angstrom": padding,
        "atom_selection": "heavy_atoms_only",
        "reference_heavy_atom_count": int(len(coordinates)),
        "aligned_adenosine_inside": status["shared_box"]["aligned_adenosine_inside"],
    }
    status["change_control"] = {
        "base_protocol": "a2a-dual-state-v1.1",
        "correction": "SDF explicit-hydrogen-independent heavy-atom box",
        "preserved_failed_run": "outputs/v1.1/redocking_report.json",
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "preparation_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()

