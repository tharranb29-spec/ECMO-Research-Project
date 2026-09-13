#!/usr/bin/env python3

"""Prepare audited, non-production Tier A inputs for external structure building."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
POLICY = ROOT / "config" / "md_construct_policy.v1.5.json"
OUTPUT = ROOT / "outputs" / "v1.5" / "md" / "builder_inputs"


@dataclass(frozen=True)
class Atom:
    line: str
    record: str
    serial: int
    name: str
    altloc: str
    resname: str
    chain: str
    resseq: int
    icode: str
    xyz: np.ndarray
    element: str


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recorded_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_atoms(path: Path) -> list[Atom]:
    atoms = []
    for raw_line in path.read_text(errors="replace").splitlines():
        line = raw_line.ljust(80)
        record = line[:6].strip()
        if record not in {"ATOM", "HETATM"}:
            continue
        atoms.append(Atom(
            line=raw_line,
            record=record,
            serial=int(line[6:11]),
            name=line[12:16].strip(),
            altloc=line[16].strip(),
            resname=line[17:20].strip(),
            chain=line[21].strip(),
            resseq=int(line[22:26]),
            icode=line[26].strip(),
            xyz=np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
            element=line[76:78].strip() or line[12:14].strip(),
        ))
    return atoms


def render_atom(atom: Atom, *, serial: int, chain: str | None = None,
                resseq: int | None = None, xyz: np.ndarray | None = None) -> str:
    line = atom.line.ljust(80)
    chosen_xyz = atom.xyz if xyz is None else xyz
    rendered = (
        f"{line[:6]}{serial:5d}{line[11:21]}{(chain if chain is not None else atom.chain):1s}"
        f"{(resseq if resseq is not None else atom.resseq):4d}{line[26:30]}"
        f"{chosen_xyz[0]:8.3f}{chosen_xyz[1]:8.3f}{chosen_xyz[2]:8.3f}{line[54:80]}"
    )
    return rendered.rstrip()


def heavy(atom: Atom) -> bool:
    return atom.element.upper() not in {"H", "D"}


def minimum_distance(left: list[Atom], left_xyz: np.ndarray,
                     right: list[Atom]) -> tuple[float, dict]:
    best = (float("inf"), {})
    for atom, xyz in zip(left, left_xyz):
        if not heavy(atom):
            continue
        for other in right:
            if not heavy(other):
                continue
            distance = float(np.linalg.norm(xyz - other.xyz))
            if distance < best[0]:
                best = (distance, {
                    "left": f"{atom.resname}:{atom.name}",
                    "right": f"{other.chain}:{other.resname}{other.resseq}:{other.name}",
                })
    return best


def kabsch(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    source_center = source.mean(axis=0)
    target_center = target.mean(axis=0)
    covariance = (source - source_center).T @ (target - target_center)
    u, _, vt = np.linalg.svd(covariance)
    correction = np.eye(3)
    correction[-1, -1] = np.sign(np.linalg.det(vt.T @ u.T))
    rotation = vt.T @ correction @ u.T
    translation = target_center - source_center @ rotation.T
    fitted = source @ rotation.T + translation
    rmsd = float(np.sqrt(np.mean(np.sum((fitted - target) ** 2, axis=1))))
    return rotation, translation, rmsd


def write_pdb(path: Path, remarks: list[str], records: list[tuple[Atom, dict]]) -> None:
    lines = [f"REMARK 950 {remark}" for remark in remarks]
    for serial, (atom, changes) in enumerate(records, 1):
        lines.append(render_atom(atom, serial=serial, **changes))
    lines.extend(["TER", "END"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_5g53(atoms: list[Atom], output: Path) -> dict:
    proteins = [a for a in atoms if a.record == "ATOM" and a.chain in {"B", "D"}]
    neca = [a for a in atoms if a.record == "HETATM" and a.chain == "B" and a.resname == "NEC" and a.resseq == 400]
    gdp = [a for a in atoms if a.record == "HETATM" and a.chain == "C" and a.resname == "GDP" and a.resseq == 400]
    residues_by_chain = {
        chain: {a.resseq for a in atoms if a.record == "ATOM" and a.chain == chain}
        for chain in {"A", "B", "C", "D"}
    }
    if any(residue in residues_by_chain["A"] for residue in range(147, 159)):
        raise RuntimeError("Expected deposited receptor chain A gap 147-158 was not reproduced")
    if not set(range(147, 159)).issubset(residues_by_chain["B"]):
        raise RuntimeError("Selected receptor chain B does not resolve residues 147-158")
    if any(residue in residues_by_chain["C"] for residue in {366, 367, 368}):
        raise RuntimeError("Expected deposited mini-Gs chain C pocket gap 366-368 was not reproduced")
    if not {366, 367, 368}.issubset(residues_by_chain["D"]):
        raise RuntimeError("Selected mini-Gs chain D does not resolve the expected pocket residues 366-368")

    allowed_backbone = {"N", "CA", "C", "O"}
    source_map = {(a.resseq, a.icode, a.resname, a.name): a for a in atoms
                  if a.record == "ATOM" and a.chain == "C" and a.name in allowed_backbone and not a.altloc}
    target_map = {(a.resseq, a.icode, a.resname, a.name): a for a in atoms
                  if a.record == "ATOM" and a.chain == "D" and a.name in allowed_backbone and not a.altloc}
    all_shared = sorted(set(source_map) & set(target_map))
    shared = [key for key in all_shared if min(
        float(np.linalg.norm(source_map[key].xyz - atom.xyz)) for atom in gdp
    ) <= 8.0]
    if len(shared) < 40:
        raise RuntimeError(f"Too few shared mini-Gs backbone atoms for GDP alignment: {len(shared)}")
    source_xyz = np.vstack([source_map[key].xyz for key in shared])
    target_xyz = np.vstack([target_map[key].xyz for key in shared])
    rotation, translation, rmsd = kabsch(source_xyz, target_xyz)
    gdp_xyz = np.vstack([a.xyz for a in gdp]) @ rotation.T + translation
    clash_distance, clash_pair = minimum_distance(gdp, gdp_xyz, proteins + neca)
    alignment_passed = rmsd <= 0.5
    clash_passed = clash_distance >= 1.5

    records = [(a, {}) for a in proteins]
    records += [(a, {"chain": "L"}) for a in neca]
    records += [(a, {"chain": "G", "xyz": xyz}) for a, xyz in zip(gdp, gdp_xyz)]
    path = output / "5G53_BD_NECA_GDP_builder_input.pdb"
    write_pdb(path, [
        "NON-PRODUCTION BUILDER INPUT; MISSING SEGMENTS AND MUTATIONS REMAIN.",
        "CHAINS B/D SELECTED TO AVOID THE DEPOSITED ASN C239 CHIRALITY ERROR.",
        f"GDP C400 TRANSFERRED TO G USING LOCAL C-TO-D BACKBONE ALIGNMENT; RMSD {rmsd:.3f} A.",
        f"GDP TRANSFER CLASH CHECK {'PASSED' if clash_passed else 'FAILED'}; MINIMUM {clash_distance:.3f} A.",
        "NECA B400 REMAPPED TO CHAIN L; DEPOSITED COORDINATES OTHERWISE UNCHANGED.",
    ], records)
    return {
        "system_id": "5G53_NECA_miniGs_native",
        "status": (
            "builder_input_ready_not_simulation_ready"
            if alignment_passed and clash_passed
            else "builder_input_generated_geometric_review_failed"
        ),
        "output": recorded_path(path),
        "output_sha256": sha256(path),
        "selected_protein_atom_count": len(proteins),
        "neca_atom_count": len(neca),
        "gdp_atom_count": len(gdp),
        "gdp_transfer": {
            "alignment_atom_count": len(shared),
            "backbone_alignment_rmsd_angstrom": round(rmsd, 6),
            "minimum_transferred_gdp_heavy_atom_distance_angstrom": round(clash_distance, 6),
            "closest_pair": clash_pair,
            "rmsd_gate_angstrom": 0.5,
            "severe_clash_gate_angstrom": 1.5,
            "alignment_passed": alignment_passed,
            "clash_passed": clash_passed,
            "passed": alignment_passed and clash_passed,
        },
        "copy_selection_rationale": {
            "assembly_1_receptor_A_missing_residues": list(range(147, 159)) + list(range(212, 224)),
            "assembly_2_receptor_B_missing_residues": list(range(208, 224)),
            "gdp_source_miniGs_C_missing_pocket_residues": [366, 367, 368],
            "selected_miniGs_D_resolves_pocket_residues": [366, 367, 368],
            "decision": (
                "Retain B/D. Do not switch automatically to A/C or accept a rigid GDP transfer; "
                "jointly refine GDP with the resolved D-chain pocket."
            ),
        },
        "required_builder_edits": [
            "back-mutate receptor A154N",
            "model receptor residues 208-223 and mini-Gs internal segments 193-207 and 225-238",
            "complete missing sidechains and validate all modeled geometry",
            "assign protonation at pH 7.4 and parameterize NEC and GDP",
            "manually resolve the transferred GDP/Ala366 clash before accepting the nucleotide pose",
        ],
    }


def prepare_5nm4(atoms: list[Atom], output: Path, policy: dict) -> dict:
    protein = [a for a in atoms if a.record == "ATOM" and a.chain == "A" and
               (11 <= a.resseq <= 217 or 324 <= a.resseq <= 422)]
    zma = [a for a in atoms if a.record == "HETATM" and a.chain == "A" and a.resname == "ZMA" and a.resseq == 507]
    sodium = [a for a in atoms if a.record == "HETATM" and a.chain == "A" and a.resname == "NA" and a.resseq == 506]
    waters = [a for a in atoms if a.record == "HETATM" and a.chain == "A" and a.resname == "HOH"]
    references = zma + sodium
    retained_waters = [water for water in waters if references and
                       min(float(np.linalg.norm(water.xyz - ref.xyz)) for ref in references) <= 5.0]

    expected = {}
    for mutation in policy["controls"]["5NM4_ZMA_native"]["back_mutations_to_uniprot"]:
        parts = mutation["pdb_residue"].split()
        expected[int(parts[2])] = parts[0]
    observed = {}
    for atom in atoms:
        if atom.record == "ATOM" and atom.chain == "A" and atom.resseq in expected:
            observed.setdefault(atom.resseq, atom.resname)
    if observed != expected:
        raise RuntimeError(f"5NM4 mutation inventory mismatch: expected {expected}, observed {observed}")

    records = [(a, {}) for a in protein]
    records += [(a, {"chain": "L"}) for a in zma]
    records += [(a, {"chain": "I"}) for a in sodium]
    records += [(a, {"chain": "W"}) for a in retained_waters]
    path = output / "5NM4_A_ZMA_sodium_builder_input.pdb"
    write_pdb(path, [
        "NON-PRODUCTION BUILDER INPUT; MISSING LOOP AND BACK-MUTATIONS REMAIN.",
        "B562RIL FUSION/TAGS, DETERGENTS, AND DEPOSITED MEMBRANE LIPIDS REMOVED.",
        "ZMA A507 REMAPPED TO L; SODIUM A506 TO I; LOCAL WATERS TO W.",
        "NINE DEPOSITED RECEPTOR MUTATIONS MUST BE RESTORED TO HUMAN ADORA2A.",
    ], records)
    return {
        "system_id": "5NM4_ZMA_native",
        "status": "builder_input_ready_not_simulation_ready",
        "output": recorded_path(path),
        "output_sha256": sha256(path),
        "selected_receptor_atom_count": len(protein),
        "zma_atom_count": len(zma),
        "sodium_atom_count": len(sodium),
        "retained_water_atom_count": len(retained_waters),
        "retained_water_residue_ids": sorted({f"A:{a.resseq}{a.icode}" for a in retained_waters}),
        "deposited_mutation_inventory_verified": [
            {"pdb_residue_number": residue, "deposited_residue": expected[residue]}
            for residue in sorted(expected)
        ],
        "required_builder_edits": [
            "restore all nine receptor mutations, including orthosteric S277A",
            "model the ICL3 segment corresponding to UniProt 209-218",
            "complete missing sidechains and validate all modeled geometry",
            "assign protonation at pH 7.4 and parameterize ZMA",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    source_5g53 = RAW / "5G53.pdb"
    source_5nm4 = RAW / "5NM4.pdb"
    systems = [
        prepare_5nm4(parse_atoms(source_5nm4), args.output, policy),
        prepare_5g53(parse_atoms(source_5g53), args.output),
    ]
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": policy["specification_id"],
        "status": "tier_a_builder_inputs_audited_not_simulation_ready",
        "trajectory_production_started": False,
        "source_hashes": {
            "construct_policy": sha256(POLICY),
            "5NM4": sha256(source_5nm4),
            "5G53": sha256(source_5g53),
        },
        "systems": systems,
        "remaining_gate": "Complete and visually audit external loop/mutation rebuilding before membrane construction.",
    }
    audit_path = args.output / "builder_input_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
