#!/usr/bin/env python3

"""Resolve the 5G53 chain-C chirality caveat without editing deposited atoms."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PDB = ROOT / "data" / "raw" / "5G53.pdb"
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.5" / "md" / "5g53_chirality_review.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(x - y for x, y in zip(a, b))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def parse_pdb(path: Path) -> tuple[list[str], list[dict]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    atoms = []
    for line in lines:
        if not line.startswith(("ATOM  ", "HETATM")) or line[16] not in {" ", "A"}:
            continue
        atoms.append({
            "record": line[:6].strip(),
            "atom": line[12:16].strip(),
            "resname": line[17:20].strip(),
            "chain": line[21],
            "resseq": int(line[22:26]),
            "icode": line[26].strip(),
            "xyz": (float(line[30:38]), float(line[38:46]), float(line[46:54])),
        })
    return lines, atoms


def chirality_volume(residue_atoms: list[dict]) -> float | None:
    coordinates = {atom["atom"]: atom["xyz"] for atom in residue_atoms}
    if not {"N", "CA", "C", "CB"}.issubset(coordinates):
        return None
    ca = coordinates["CA"]
    return dot(vector(coordinates["N"], ca), cross(vector(coordinates["C"], ca), vector(coordinates["CB"], ca)))


def minimum_distance(left: list[dict], right: list[dict]) -> float | None:
    if not left or not right:
        return None
    return min(distance(a["xyz"], b["xyz"]) for a in left for b in right)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    lines, atoms = parse_pdb(PDB)
    caveats = [line.rstrip() for line in lines if line.startswith("CAVEAT")]
    residues: dict[tuple[str, int, str, str], list[dict]] = defaultdict(list)
    for atom in atoms:
        if atom["record"] == "ATOM":
            residues[(atom["chain"], atom["resseq"], atom["icode"], atom["resname"])].append(atom)

    volumes = {}
    sign_counts: dict[str, Counter] = defaultdict(Counter)
    for key, residue_atoms in residues.items():
        volume = chirality_volume(residue_atoms)
        if volume is None or abs(volume) < 0.1:
            continue
        volumes[key] = volume
        sign_counts[key[0]]["positive" if volume > 0 else "negative"] += 1

    target = {}
    for chain in ("C", "D"):
        key = next(key for key in residues if key[0] == chain and key[1] == 239)
        volume = volumes[key]
        dominant_sign = sign_counts[chain].most_common(1)[0][0]
        observed_sign = "positive" if volume > 0 else "negative"
        target[chain] = {
            "residue": f"{key[3]} {chain}{key[1]}{key[2]}",
            "signed_chiral_volume_a3": round(volume, 6),
            "observed_sign": observed_sign,
            "dominant_chain_sign": dominant_sign,
            "matches_dominant_chain_sign": observed_sign == dominant_sign,
            "chain_sign_counts": dict(sign_counts[chain]),
        }

    chain_atoms = {chain: [atom for atom in atoms if atom["record"] == "ATOM" and atom["chain"] == chain] for chain in "ABCD"}
    neca_atoms = {chain: [atom for atom in atoms if atom["record"] == "HETATM" and atom["resname"] == "NEC" and atom["chain"] == chain] for chain in "AB"}
    gdp_atoms = {chain: [atom for atom in atoms if atom["record"] == "HETATM" and atom["resname"] == "GDP" and atom["chain"] == chain] for chain in "CD"}
    residue_239_atoms = {
        chain: next(value for key, value in residues.items() if key[0] == chain and key[1] == 239)
        for chain in "CD"
    }

    passed = (
        any("ASN C 239 HAS WRONG CHIRALITY" in line for line in caveats)
        and not target["C"]["matches_dominant_chain_sign"]
        and target["D"]["matches_dominant_chain_sign"]
        and len(neca_atoms["B"]) == 22
        and len(chain_atoms["B"]) > 0
        and len(chain_atoms["D"]) > 0
    )
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-md-5g53-structure-review-v1.5",
        "source": {
            "path": str(PDB.relative_to(ROOT)),
            "sha256": sha256(PDB),
            "deposited_resolution_angstrom": 3.4,
            "caveats": caveats,
        },
        "biological_assemblies": {
            "1": {"chains": ["A", "C"]},
            "2": {"chains": ["B", "D"]},
        },
        "chirality_check": target,
        "copy_inventory": {
            "A_C": {
                "receptor_atom_count": len(chain_atoms["A"]),
                "mini_gs_atom_count": len(chain_atoms["C"]),
                "neca_atom_count": len(neca_atoms["A"]),
                "gdp_atom_count": len(gdp_atoms["C"]),
                "asn_239_minimum_distance_to_receptor_angstrom": round(minimum_distance(residue_239_atoms["C"], chain_atoms["A"]), 3),
                "asn_239_minimum_distance_to_neca_angstrom": round(minimum_distance(residue_239_atoms["C"], neca_atoms["A"]), 3),
            },
            "B_D": {
                "receptor_atom_count": len(chain_atoms["B"]),
                "mini_gs_atom_count": len(chain_atoms["D"]),
                "neca_atom_count": len(neca_atoms["B"]),
                "gdp_atom_count": len(gdp_atoms["D"]),
                "asn_239_minimum_distance_to_receptor_angstrom": round(minimum_distance(residue_239_atoms["D"], chain_atoms["B"]), 3),
                "asn_239_minimum_distance_to_neca_angstrom": round(minimum_distance(residue_239_atoms["D"], neca_atoms["B"]), 3),
            },
        },
        "decision": {
            "status": "resolved_by_copy_selection" if passed else "manual_review_failed",
            "selected_biological_assembly": 2 if passed else None,
            "selected_receptor_chain": "B" if passed else None,
            "selected_mini_gs_chain": "D" if passed else None,
            "selected_neca": "NEC B 400" if passed else None,
            "deposited_coordinate_edit_performed": False,
            "rationale": "Use the independently deposited B/D biological assembly, whose D239 alpha-carbon chirality matches the dominant L-amino-acid sign. This avoids the chain-C defect instead of repairing experimental coordinates.",
            "literature_precedent": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6445292/",
        },
        "remaining_structure_preparation_gates": [
            "resolve missing receptor and mini-Gs residues and atoms with a versioned construct policy",
            "decide and document GDP occupancy because GDP is present only in chain C of the deposited asymmetric unit",
            "orient the selected B/D assembly in the membrane and document retained waters and engineered components",
            "validate the complete prepared model before membrane building",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit("5G53 chirality review did not pass")


if __name__ == "__main__":
    main()
