#!/usr/bin/env python3
"""Build and audit protein-only Tier A construct candidates for protocol v1.6."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openmm.app import PDBFile
from pdbfixer import PDBFixer


ROOT = Path(__file__).resolve().parent
INPUT_ROOT = ROOT / "outputs" / "v1.5" / "md" / "builder_inputs"
OUTPUT_ROOT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_constructs"
PROTOCOL = ROOT / "config" / "protocol.v1.6.json"


MUTATIONS_5NM4 = [
    "LEU-63-ALA", "ALA-97-THR", "ALA-116-ARG", "ALA-131-LYS", "ALA-163-ASN",
    "ALA-211-LEU", "ALA-340-LEU", "ALA-344-VAL", "ALA-382-SER",
]
MUTATIONS_5G53 = ["ALA-154-ASN"]
LOOP_5NM4 = ["LYS", "GLN", "MET", "GLU", "SER", "GLN", "PRO", "LEU", "PRO", "GLY"]
LOOPS_MINIGS = {
    23: ["ILE", "TYR", "HIS", "GLY", "GLY", "SER", "GLY", "GLY", "SER", "GLY", "GLY", "THR", "SER", "GLY", "ILE"],
    40: ["GLY", "GLY", "GLN", "ARG", "ASP", "GLU", "ARG", "ARG", "LYS", "TRP", "ILE", "GLN", "CYS", "PHE"],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protein_only(source: Path, destination: Path, chain_ids: set[str]) -> None:
    lines = []
    for raw in source.read_text(errors="replace").splitlines():
        line = raw.ljust(80)
        if line[:6].strip() == "ATOM" and line[21].strip() in chain_ids:
            if line[76:78].strip().upper() not in {"H", "D"}:
                lines.append(raw)
    lines.extend(["TER", "END"])
    destination.write_text("\n".join(lines) + "\n")


def extract_references(source: Path, destination: Path, allowed: set[tuple[str, str]]) -> None:
    lines = ["REMARK 950 NATIVE COORDINATE REFERENCE ONLY; NOT A PARAMETERIZED SYSTEM."]
    serial = 1
    for raw in source.read_text(errors="replace").splitlines():
        line = raw.ljust(80)
        if line[:6].strip() != "HETATM":
            continue
        key = (line[21].strip(), line[17:20].strip())
        if key in allowed:
            lines.append(f"{line[:6]}{serial:5d}{line[11:]}".rstrip())
            serial += 1
    lines.extend(["TER", "END"])
    destination.write_text("\n".join(lines) + "\n")


def write_fixer(fixer: PDBFixer, path: Path) -> None:
    with path.open("w") as stream:
        PDBFile.writeFile(fixer.topology, fixer.positions, stream, keepIds=True)


def renumber_5nm4(path: Path) -> None:
    remapped = []
    residue_map = {}
    next_residue = 2
    for raw in path.read_text().splitlines():
        line = raw.ljust(80)
        if line[:6].strip() not in {"ATOM", "HETATM"}:
            remapped.append(raw)
            continue
        old = int(line[22:26])
        key = (line[21], old)
        if key not in residue_map:
            residue_map[key] = next_residue
            next_residue += 1
        new = residue_map[key]
        remapped.append(f"{line[:22]}{new:4d}{line[26:]}".rstrip())
    if next_residue != 305:
        raise RuntimeError(f"5NM4 sequence-order renumbering ended at {next_residue - 1}, expected 304")
    path.write_text("\n".join(remapped) + "\n")


@dataclass
class Atom:
    name: str
    residue: str
    chain: str
    residue_id: int
    element: str
    xyz: np.ndarray


def atoms(path: Path) -> list[Atom]:
    parsed = []
    for raw in path.read_text().splitlines():
        line = raw.ljust(80)
        if line[:6].strip() != "ATOM":
            continue
        parsed.append(Atom(
            name=line[12:16].strip(), residue=line[17:20].strip(), chain=line[21].strip(),
            residue_id=int(line[22:26]), element=(line[76:78].strip() or line[12:14].strip()).upper(),
            xyz=np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]),
        ))
    return parsed


def audit_construct(path: Path, system: str, expected_residues: dict[str, set[int]], expected_names: dict[tuple[str, int], str]) -> dict:
    parsed = atoms(path)
    pdb = PDBFile(str(path))
    topology_atoms = list(pdb.topology.atoms())
    if len(topology_atoms) != len(parsed):
        raise RuntimeError("PDB topology and fixed-column atom inventories differ")
    bonded_pairs = {frozenset((left.index, right.index)) for left, right in pdb.topology.bonds()}
    by_residue = defaultdict(list)
    for atom in parsed:
        by_residue[(atom.chain, atom.residue_id)].append(atom)
    observed = defaultdict(set)
    for chain, residue_id in by_residue:
        observed[chain].add(residue_id)
    residue_sets_pass = all(observed[chain] == ids for chain, ids in expected_residues.items())
    names_pass = all(by_residue[(chain, residue_id)][0].residue == name for (chain, residue_id), name in expected_names.items())

    peptide_distances = []
    continuity_failures = []
    for chain, ids in expected_residues.items():
        for left in sorted(ids):
            right = left + 1
            if right not in ids:
                continue
            c_atoms = [a for a in by_residue[(chain, left)] if a.name == "C"]
            n_atoms = [a for a in by_residue[(chain, right)] if a.name == "N"]
            if len(c_atoms) != 1 or len(n_atoms) != 1:
                continuity_failures.append({"chain": chain, "left": left, "right": right, "reason": "missing_backbone_atom"})
                continue
            distance = float(np.linalg.norm(c_atoms[0].xyz - n_atoms[0].xyz))
            peptide_distances.append(distance)
            if not 1.15 <= distance <= 1.55:
                continuity_failures.append({"chain": chain, "left": left, "right": right, "distance_angstrom": distance})

    heavy = [(index, atom) for index, atom in enumerate(parsed) if atom.element not in {"H", "D"}]
    minimum = (math.inf, None)
    severe = []
    for offset, (left_index, left) in enumerate(heavy):
        for right_index, right in heavy[offset + 1:]:
            if frozenset((left_index, right_index)) in bonded_pairs:
                continue
            if (left.chain, left.residue_id) == (right.chain, right.residue_id):
                continue
            if left.chain == right.chain and abs(left.residue_id - right.residue_id) == 1:
                continue
            distance = float(np.linalg.norm(left.xyz - right.xyz))
            if distance < minimum[0]:
                minimum = (distance, (left, right))
            if distance < 1.5:
                severe.append({
                    "left": f"{left.chain}:{left.residue}{left.residue_id}:{left.name}",
                    "right": f"{right.chain}:{right.residue}{right.residue_id}:{right.name}",
                    "distance_angstrom": round(distance, 6),
                })
    closest = None if minimum[1] is None else {
        "left": f"{minimum[1][0].chain}:{minimum[1][0].residue}{minimum[1][0].residue_id}:{minimum[1][0].name}",
        "right": f"{minimum[1][1].chain}:{minimum[1][1].residue}{minimum[1][1].residue_id}:{minimum[1][1].name}",
        "distance_angstrom": round(minimum[0], 6),
    }
    passed = residue_sets_pass and names_pass and not continuity_failures and not severe
    return {
        "system_id": system,
        "protein_atom_count": len(parsed),
        "protein_residue_count": len(by_residue),
        "observed_residue_ranges": {chain: [min(ids), max(ids)] for chain, ids in observed.items()},
        "expected_residue_sets_passed": residue_sets_pass,
        "back_mutation_names_passed": names_pass,
        "peptide_bond_count_audited": len(peptide_distances),
        "peptide_distance_range_angstrom": [min(peptide_distances), max(peptide_distances)] if peptide_distances else None,
        "continuity_failures": continuity_failures,
        "closest_nonlocal_heavy_atom_pair": closest,
        "severe_nonlocal_clashes_below_1_5_angstrom": severe,
        "geometry_gate_passed": passed,
        "status": "construct_candidate_geometry_passed" if passed else "construct_candidate_blocked_by_geometry_audit",
    }


def build_5nm4(temp: Path) -> tuple[Path, Path, dict]:
    source = INPUT_ROOT / "5NM4_A_ZMA_sodium_builder_input.pdb"
    protein = temp / "5nm4_protein.pdb"
    reference = OUTPUT_ROOT / "5NM4_native_reference.pdb"
    extract_references(source, reference, {("L", "ZMA"), ("I", "NA"), ("W", "HOH")})
    protein_only(source, protein, {"A"})
    fixer = PDBFixer(filename=str(protein))
    fixer.applyMutations(MUTATIONS_5NM4, "A")
    fixer.missingResidues = {(0, 207): LOOP_5NM4}
    fixer.findMissingAtoms()
    fixer.addMissingAtoms(seed=20260915)
    fixer.addMissingHydrogens(7.4)
    output = OUTPUT_ROOT / "5NM4_ADORA2A_complete_candidate.pdb"
    failed_archive = OUTPUT_ROOT / "5NM4_ADORA2A_complete_candidate.numbering_blocked_attempt.pdb"
    if output.exists() and not failed_archive.exists():
        shutil.copy2(output, failed_archive)
    write_fixer(fixer, output)
    renumber_5nm4(output)
    expected = {"A": set(range(2, 305))}
    names = {
        ("A", 54): "ALA", ("A", 88): "THR", ("A", 107): "ARG", ("A", 122): "LYS",
        ("A", 154): "ASN", ("A", 202): "LEU", ("A", 235): "LEU", ("A", 239): "VAL", ("A", 277): "SER",
    }
    return output, reference, audit_construct(output, "5NM4_ZMA_native", expected, names)


def build_5g53(temp: Path) -> tuple[Path, Path, dict]:
    source = INPUT_ROOT / "5G53_BD_NECA_GDP_builder_input.pdb"
    protein = temp / "5g53_protein.pdb"
    reference = OUTPUT_ROOT / "5G53_native_reference.pdb"
    extract_references(source, reference, {("L", "NEC")})
    protein_only(source, protein, {"B", "D"})
    fixer = PDBFixer(filename=str(protein))
    fixer.applyMutations(MUTATIONS_5G53, "B")
    fixer.missingResidues = {
        (0, 202): ["LEU", "LYS", "GLN", "MET", "GLU", "SER", "GLN", "PRO", "LEU", "PRO", "GLY", "GLU", "ARG", "ALA", "ARG", "SER"],
        **{(1, index): sequence for index, sequence in LOOPS_MINIGS.items()},
    }
    fixer.findMissingAtoms()
    fixer.addMissingAtoms(seed=20260915)
    fixer.addMissingHydrogens(7.4)
    output = OUTPUT_ROOT / "5G53_ADORA2A_miniGs_nucleotide_free_complete_candidate.pdb"
    write_fixer(fixer, output)
    expected = {
        "B": set(range(6, 306)),
        "D": set(range(39, 62)) | set(range(193, 255)) | set(range(265, 394)),
    }
    names = {("B", 154): "ASN"}
    result = audit_construct(output, "5G53_NECA_miniGs_native_nucleotide_free", expected, names)
    result["gdp_atom_count"] = 0
    result["nucleotide_policy_passed"] = True
    return output, reference, result


def main() -> None:
    protocol = json.loads(PROTOCOL.read_text())
    if protocol["md_v1_6"]["gdp_policy"]["decision"] != "omit_GDP_from_selected_BD_control":
        raise RuntimeError("protocol GDP policy drift")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a2a-v16-construct-") as directory:
        temp = Path(directory)
        built = [build_5nm4(temp), build_5g53(temp)]
    systems = []
    for output, reference, audit in built:
        audit["construct_path"] = str(output.relative_to(ROOT))
        audit["construct_sha256"] = sha256(output)
        audit["native_reference_path"] = str(reference.relative_to(ROOT))
        audit["native_reference_sha256"] = sha256(reference)
        systems.append(audit)
    accepted = sum(system["geometry_gate_passed"] for system in systems)
    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-md-tier-a-constructs-v1.6",
        "method": "PDBFixer 1.12 deterministic missing-atom and declared-loop candidate generation followed by independent geometry audit",
        "pdbfixer_seed": 20260915,
        "protonation_ph": 7.4,
        "gdp_policy": "nucleotide-free selected 5G53 B/D assembly; no cross-copy GDP transfer",
        "candidate_labels_loaded": False,
        "trajectory_production_started": False,
        "systems": systems,
        "geometry_pass_count": accepted,
        "status": "construct_geometry_gate_passed" if accepted == 2 else "construct_geometry_gate_blocked",
        "next_gate": "Map parameterized native ligand coordinates, build Amber protein-ligand topology, then require energy and membrane-system audits before dynamics.",
        "source_hashes": {
            "protocol": sha256(PROTOCOL),
            "inactive_builder_input": sha256(INPUT_ROOT / "5NM4_A_ZMA_sodium_builder_input.pdb"),
            "active_builder_input": sha256(INPUT_ROOT / "5G53_BD_NECA_GDP_builder_input.pdb"),
            "runner": sha256(Path(__file__)),
        },
    }
    report_path = OUTPUT_ROOT / "construct_audit.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
