#!/usr/bin/env python3

"""Computationally audit a completed MD bundle and freeze its analysis definition."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import app, unit
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "md_validation.v1.5.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--system-id", required=True)
    parser.add_argument("--tier", choices=["A", "B"], required=True)
    parser.add_argument("--ligand-resname", required=True)
    parser.add_argument("--receptor-chain", required=True)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    tier_a = {row["system_id"] for row in config["tiers"]["tier_a_controls"]}
    tier_b_config = config["tiers"]["tier_b_blinded_candidates"]
    tier_b = {f"{candidate}_{pdb}" for candidate in tier_b_config["candidate_ids"] for pdb in tier_b_config["receptor_structures"]}
    if args.system_id not in (tier_a if args.tier == "A" else tier_b):
        raise RuntimeError("System ID is not in the frozen tier declaration")
    paths = {
        "system_xml": args.bundle / "system.xml",
        "topology_pdb": args.bundle / "topology.pdb",
        "equilibrated_state_xml": args.bundle / "equilibrated_state.xml",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError(f"Completed bundle files are missing: {missing}")
    pdb = app.PDBFile(str(paths["topology_pdb"]))
    system = mm.XmlSerializer.deserialize(paths["system_xml"].read_text(encoding="utf-8"))
    state = mm.XmlSerializer.deserialize(paths["equilibrated_state_xml"].read_text(encoding="utf-8"))
    positions = state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    atoms = list(pdb.topology.atoms())
    blockers = []
    if len(atoms) != system.getNumParticles() or len(atoms) != len(positions):
        blockers.append({"reason": "particle_topology_position_count_mismatch"})
    if not np.all(np.isfinite(positions)):
        blockers.append({"reason": "nonfinite_coordinates"})
    ligand = [atom for atom in atoms if atom.residue.name == args.ligand_resname and atom.element.symbol != "H"]
    receptor = [
        atom for atom in atoms
        if atom.residue.chain.id == args.receptor_chain and atom.element.symbol != "H"
        and atom.residue.name not in {"HOH", "POP", "POPC", "CHL", "CHL1"}
    ]
    alignment = [atom.index for atom in receptor if atom.name == "CA"]
    if not ligand:
        blockers.append({"reason": "ligand_heavy_atoms_not_found"})
    if len(alignment) < 100:
        blockers.append({"reason": "insufficient_receptor_ca_alignment_atoms", "count": len(alignment)})
    bonded = {tuple(sorted((left.index, right.index))) for left, right in pdb.topology.bonds()}
    heavy = [atom for atom in atoms if atom.element.symbol != "H" and atom.residue.name != "HOH"]
    heavy_coordinates = np.asarray([positions[atom.index] for atom in heavy])
    close_pairs = cKDTree(heavy_coordinates).query_pairs(r=0.10)
    closest = (math.inf, None)
    for left_local, right_local in close_pairs:
        left, right = heavy[left_local], heavy[right_local]
        if left.residue is right.residue or tuple(sorted((left.index, right.index))) in bonded:
            continue
        distance = float(np.linalg.norm(positions[left.index] - positions[right.index]))
        if distance < closest[0]:
            closest = (distance, (left, right))
    if closest[0] < 0.10:
        blockers.append({
            "reason": "severe_cross_residue_heavy_atom_clash",
            "distance_angstrom": closest[0] * 10,
            "atoms": [str(closest[1][0]), str(closest[1][1])],
        })
    native_contacts = []
    for ligand_atom in ligand:
        for receptor_atom in receptor:
            distance = float(np.linalg.norm(positions[ligand_atom.index] - positions[receptor_atom.index]))
            if distance <= 0.40:
                native_contacts.append({
                    "ligand_atom_index": ligand_atom.index,
                    "receptor_atom_index": receptor_atom.index,
                    "starting_distance_angstrom": distance * 10,
                })
    if not native_contacts:
        blockers.append({"reason": "no_starting_orthosteric_contacts_within_4_angstrom"})
    energy = None
    try:
        integrator = mm.VerletIntegrator(0.001 * unit.picoseconds)
        context = mm.Context(system, integrator, mm.Platform.getPlatformByName("CPU"))
        context.setState(state)
        energy = context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        if not math.isfinite(energy):
            blockers.append({"reason": "nonfinite_potential_energy"})
        del context, integrator
    except Exception as exc:  # noqa: BLE001
        blockers.append({"reason": "openmm_context_or_energy_failure", "details": str(exc)})
    definition_path = args.bundle / "native_contacts.json"
    definition = {
        "schema_version": 1, "system_id": args.system_id,
        "ligand_heavy_atom_indices": [atom.index for atom in ligand],
        "alignment_atom_indices": alignment, "native_contacts": native_contacts,
        "distance_cutoff_angstrom": 4.0, "source_state_sha256": sha256(paths["equilibrated_state_xml"]),
    }
    definition_path.write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
    accepted = not blockers
    manifest = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"], "system_id": args.system_id,
        "tier": args.tier, "status": f"accepted_for_tier_{args.tier.lower()}_production" if accepted else "blocked_by_computational_audit",
        "candidate_labels_loaded": False, "computational_audit_passed": accepted,
        "minimum_cross_residue_heavy_atom_distance_angstrom": (
            closest[0] * 10 if math.isfinite(closest[0]) else ">=1.0"
        ),
        "starting_native_contact_count": len(native_contacts), "potential_energy_kj_mol": energy,
        "blockers": blockers,
        "files": {
            name: {"path": path.name, "sha256": sha256(path)} for name, path in paths.items()
        } | {"native_contacts": {"path": definition_path.name, "sha256": sha256(definition_path)}},
    }
    manifest_path = args.bundle / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    if not accepted:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
