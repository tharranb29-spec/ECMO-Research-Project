#!/usr/bin/env python3
"""Build and audit unsolvated Tier A receptor/GAFF2-ligand compatibility bundles."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openmm import Platform, VerletIntegrator, unit
from openmm.app import AmberInpcrdFile, AmberPrmtopFile, NoCutoff, PDBFile, Simulation
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
MD = ROOT / "outputs" / "v1.6" / "md"
OUTPUT = MD / "tier_a_complex_preflight"
IMAGE = "a2a-ambertools:v1.6"
CONTROLS = {
    "5NM4_ZMA_native": {
        "protein": MD / "tier_a_constructs" / "minimized" / "5NM4_ADORA2A_minimized_candidate.pdb",
        "ligand": "ZMA", "ligand_resname": "ZMA", "receptor_chain": "A",
    },
    "5G53_NECA_miniGs_native_nucleotide_free": {
        "protein": MD / "tier_a_constructs" / "minimized" / "5G53_ADORA2A_miniGs_nucleotide_free_minimized_candidate.pdb",
        "ligand": "NEC", "ligand_resname": "NEC", "receptor_chain": "B",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_container(bundle: Path) -> None:
    relative = bundle.relative_to(REPO)
    command = [
        "docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
        "--volume", f"{REPO}:/work", "--workdir", f"/work/{relative}",
        IMAGE, "tleap", "-f", "tleap.in",
    ]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (bundle / "tleap.log").write_text("COMMAND: tleap -f tleap.in\n\n" + completed.stdout)
    if completed.returncode:
        raise RuntimeError(f"tleap failed for {bundle.name}; inspect tleap.log")


def write_amber_protein(source: Path, destination: Path) -> dict:
    """Translate explicit PDB protonation/disulfides into Amber residue names."""
    lines = source.read_text().splitlines()
    serial_atoms = {}
    residue_atoms = {}
    residue_names = {}
    first_residue_by_chain = {}
    for raw in lines:
        line = raw.ljust(80)
        if line[:6].strip() != "ATOM":
            continue
        serial = int(line[6:11])
        key = (line[21], line[22:26], line[26])
        atom_name = line[12:16].strip()
        serial_atoms[serial] = (key, line[17:20].strip(), atom_name)
        residue_atoms.setdefault(key, set()).add(atom_name)
        residue_names[key] = line[17:20].strip()
        first_residue_by_chain.setdefault(line[21], key)
    disulfide_keys = set()
    disulfide_pairs = set()
    for raw in lines:
        if not raw.startswith("CONECT"):
            continue
        fields = raw.split()
        if len(fields) < 3:
            continue
        left = serial_atoms.get(int(fields[1]))
        for value in fields[2:]:
            right = serial_atoms.get(int(value))
            if left and right and left[1:] == ("CYS", "SG") and right[1:] == ("CYS", "SG"):
                disulfide_keys.update((left[0], right[0]))
                disulfide_pairs.add(tuple(sorted((left[0], right[0]))))
    histidine_names = {}
    for key, atom_names in residue_atoms.items():
        if residue_names[key] != "HIS":
            continue
        has_hd1 = "HD1" in atom_names
        has_he2 = "HE2" in atom_names
        if has_hd1 and has_he2:
            histidine_names[key] = "HIP"
        elif has_hd1:
            histidine_names[key] = "HID"
        else:
            histidine_names[key] = "HIE"
    rewritten = []
    removed_thiol_hydrogens = 0
    removed_terminal_backbone_hydrogens = 0
    for raw in lines:
        line = raw.ljust(80)
        if line[:6].strip() != "ATOM":
            rewritten.append(raw)
            continue
        key = (line[21], line[22:26], line[26])
        residue = line[17:20].strip()
        atom_name = line[12:16].strip()
        if key == first_residue_by_chain[line[21]] and atom_name == "H":
            # tleap generates H1/H2/H3 for an uncapped N-terminus; retaining the
            # generic backbone H creates an untyped duplicate.
            removed_terminal_backbone_hydrogens += 1
            continue
        if key in disulfide_keys and residue == "CYS":
            if atom_name == "HG":
                removed_thiol_hydrogens += 1
                continue
            line = f"{line[:17]}CYX{line[20:]}"
        elif residue == "HIS":
            line = f"{line[:17]}{histidine_names[key]}{line[20:]}"
        rewritten.append(line.rstrip())
    destination.write_text("\n".join(rewritten) + "\n")
    return {
        "histidines_typed": len(histidine_names),
        "disulfide_cysteines_typed": len(disulfide_keys),
        "disulfide_bond_count": len(disulfide_pairs),
        "removed_disulfide_thiol_hydrogens": removed_thiol_hydrogens,
        "removed_terminal_backbone_hydrogens": removed_terminal_backbone_hydrogens,
    }


def geometry_audit(pdb_path: Path, ligand_resname: str, receptor_chain: str) -> dict:
    pdb = PDBFile(str(pdb_path))
    positions = np.array([
        [position.x, position.y, position.z]
        for position in pdb.positions.value_in_unit(unit.angstrom)
    ])
    atoms = list(pdb.topology.atoms())
    ligand = [atom for atom in atoms if atom.residue.name == ligand_resname and atom.element.symbol != "H"]
    protein_residues = {
        "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "HID", "HIE", "HIP",
        "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
    }
    receptor = [
        atom for atom in atoms
        if atom.element.symbol != "H" and atom.residue.name in protein_residues
    ]
    if not ligand or not receptor:
        return {"passed": False, "reason": "ligand_or_receptor_not_found"}
    distances = cKDTree(positions[[atom.index for atom in receptor]]).query(
        positions[[atom.index for atom in ligand]], k=1
    )[0]
    contact_pairs = 0
    receptor_xyz = positions[[atom.index for atom in receptor]]
    for atom in ligand:
        contact_pairs += int(np.sum(np.linalg.norm(receptor_xyz - positions[atom.index], axis=1) <= 4.0))
    return {
        "passed": float(distances.min()) >= 1.0 and contact_pairs > 0,
        "ligand_heavy_atom_count": len(ligand),
        "receptor_heavy_atom_count": len(receptor),
        "minimum_ligand_receptor_heavy_distance_angstrom": float(distances.min()),
        "native_contact_pair_count_within_4_angstrom": contact_pairs,
        "requested_receptor_chain_before_tleap": receptor_chain,
        "note": "tleap may not preserve PDB chain identifiers; geometry uses all protein heavy atoms",
    }


def build(system_id: str, config: dict) -> dict:
    bundle = OUTPUT / system_id
    bundle.mkdir(parents=True, exist_ok=True)
    ligand_bundle = MD / "ligand_bundles" / config["ligand"]
    native_pose = MD / "native_control_ligands" / config["ligand"] / "ligand_gaff2_native_pose.mol2"
    protein_translation = write_amber_protein(config["protein"], bundle / "protein.pdb")
    shutil.copy2(native_pose, bundle / "ligand_native_pose.mol2")
    shutil.copy2(ligand_bundle / "ligand.frcmod", bundle / "ligand.frcmod")
    (bundle / "tleap.in").write_text(
        "source leaprc.protein.ff19SB\n"
        "source leaprc.gaff2\n"
        "loadAmberParams ligand.frcmod\n"
        "LIG = loadMol2 ligand_native_pose.mol2\n"
        "REC = loadPdb protein.pdb\n"
        "COM = combine {REC LIG}\n"
        "check COM\n"
        "saveAmberParm COM complex.prmtop complex.inpcrd\n"
        "savePdb COM complex.pdb\n"
        "quit\n"
    )
    run_container(bundle)
    severe_tokens = [
        token for token in ["FATAL", "Could not find bond parameter", "Could not find angle parameter", "Could not find torsion parameter"]
        if token in (bundle / "tleap.log").read_text()
    ]
    prmtop = AmberPrmtopFile(str(bundle / "complex.prmtop"))
    inpcrd = AmberInpcrdFile(str(bundle / "complex.inpcrd"))
    system = prmtop.createSystem(nonbondedMethod=NoCutoff, constraints=None)
    integrator = VerletIntegrator(0.001 * unit.picoseconds)
    simulation = Simulation(prmtop.topology, system, integrator, Platform.getPlatformByName("CPU"))
    simulation.context.setPositions(inpcrd.positions)
    energy = float(simulation.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
    geometry = geometry_audit(bundle / "complex.pdb", config["ligand_resname"], config["receptor_chain"])
    accepted = not severe_tokens and math.isfinite(energy) and geometry["passed"]
    files = [
        "protein.pdb", "ligand_native_pose.mol2", "ligand.frcmod", "tleap.in",
        "tleap.log", "leap.log", "complex.prmtop", "complex.inpcrd", "complex.pdb",
    ]
    return {
        "system_id": system_id,
        "status": "unsolvated_complex_preflight_accepted" if accepted else "unsolvated_complex_preflight_blocked",
        "particle_count": system.getNumParticles(),
        "initial_potential_energy_kj_mol": energy,
        "finite_initial_energy": math.isfinite(energy),
        "tleap_severe_tokens": severe_tokens,
        "geometry": geometry,
        "amber_protein_translation": protein_translation,
        "files": {name: sha256(bundle / name) for name in files},
        "trajectory_production_started": False,
    }


def main() -> None:
    results = [build(system_id, config) for system_id, config in CONTROLS.items()]
    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-tier-a-unsolvated-complex-preflight-v1.6",
        "candidate_labels_loaded": False,
        "systems": results,
        "accepted_count": sum(row["status"] == "unsolvated_complex_preflight_accepted" for row in results),
        "status": "all_unsolvated_complex_preflights_accepted" if all(row["status"] == "unsolvated_complex_preflight_accepted" for row in results) else "unsolvated_complex_preflight_blocked",
        "next_gate": "Embed the accepted complexes into the audited Lipid21 patch, remove solvent overlaps, rebuild with tleap, and run final periodic-system audits.",
        "runner_sha256": sha256(Path(__file__)),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "complex_preflight_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
