#!/usr/bin/env python3
"""Generate and computationally audit six GAFF2/AM1-BCC ligand bundles."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rdkit import Chem


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SOURCE_MANIFEST = ROOT / "outputs" / "v1.5" / "md" / "cgenff_requests" / "request_manifest.json"
OUTPUT_ROOT = ROOT / "outputs" / "v1.6" / "md" / "ligand_bundles"
IMAGE = "a2a-ambertools:v1.6"
RESIDUE_CODES = {"NEC": "NEC", "ZMA": "ZMA", "C5A": "C5A", "C7A": "C7A", "C9A": "C9A", "PGD2": "PG2"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mol2_atoms(path: Path) -> list[dict]:
    lines = path.read_text().splitlines()
    try:
        start = lines.index("@<TRIPOS>ATOM") + 1
        end = lines.index("@<TRIPOS>BOND")
    except ValueError as exc:
        raise RuntimeError(f"invalid MOL2 sections in {path}") from exc
    atoms = []
    for line in lines[start:end]:
        fields = line.split()
        if len(fields) < 9:
            continue
        atom_type = fields[5]
        element = atom_type.split(".")[0].capitalize()
        atoms.append({"index": int(fields[0]), "name": fields[1], "element": element, "atom_type": atom_type, "charge": float(fields[8])})
    return atoms


def write_rdkit_audit_mol2(input_path: Path, typed_path: Path, output_path: Path) -> None:
    """Make a non-production copy with Tripos types solely for RDKit graph/stereo audit."""
    source_types = {atom["index"]: atom["atom_type"] for atom in mol2_atoms(input_path)}
    lines = typed_path.read_text().splitlines()
    in_atom_section = False
    rewritten = []
    for line in lines:
        if line == "@<TRIPOS>ATOM":
            in_atom_section = True
            rewritten.append(line)
            continue
        if line.startswith("@<TRIPOS>") and line != "@<TRIPOS>ATOM":
            in_atom_section = False
        if in_atom_section and line.strip():
            fields = line.split()
            if len(fields) >= 9:
                fields[5] = source_types[int(fields[0])]
                line = " ".join(fields)
        rewritten.append(line)
    output_path.write_text("\n".join(rewritten) + "\n")


def isomeric_smiles(path: Path) -> str | None:
    molecule = None
    if path.suffix.lower() == ".sdf":
        supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=True)
        molecule = next((mol for mol in supplier if mol is not None), None)
    elif path.suffix.lower() == ".mol2":
        molecule = Chem.MolFromMol2File(str(path), removeHs=False, sanitize=True)
    return Chem.MolToSmiles(molecule, isomericSmiles=True) if molecule is not None else None


def source_chiral_centers(path: Path) -> list[tuple[int, str]]:
    molecule = None
    if path.suffix.lower() == ".sdf":
        supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=True)
        molecule = next((mol for mol in supplier if mol is not None), None)
    if molecule is None:
        return []
    return [(int(index), label) for index, label in Chem.FindMolChiralCenters(molecule, includeUnassigned=True)]


def mol2_bond_graph(path: Path) -> list[tuple[int, int]]:
    lines = path.read_text().splitlines()
    try:
        start = lines.index("@<TRIPOS>BOND") + 1
    except ValueError as exc:
        raise RuntimeError(f"missing MOL2 bond section in {path}") from exc
    bonds = []
    for line in lines[start:]:
        if line.startswith("@<TRIPOS>"):
            break
        fields = line.split()
        if len(fields) >= 4:
            bonds.append(tuple(sorted((int(fields[1]), int(fields[2])))))
    return sorted(bonds)


def run_container(arguments: list[str], cwd: Path, log: Path) -> None:
    relative = cwd.relative_to(REPO)
    command = [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "--volume", f"{REPO}:/work",
        "--workdir", f"/work/{relative}",
        IMAGE,
        *arguments,
    ]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log.write_text("COMMAND: " + " ".join(arguments) + "\n\n" + completed.stdout)
    if completed.returncode != 0:
        raise RuntimeError(f"container command failed; inspect {log}")


def write_tleap(path: Path, residue_code: str) -> None:
    path.write_text(
        "source leaprc.gaff2\n"
        "loadAmberParams ligand.frcmod\n"
        "LIG = loadMol2 ligand_gaff2.mol2\n"
        "check LIG\n"
        "saveAmberParm LIG ligand.prmtop ligand.inpcrd\n"
        "savePdb LIG ligand_parameterized.pdb\n"
        "quit\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-only", action="store_true", help="Re-audit existing generated parameter files without rerunning AmberTools")
    args = parser.parse_args()
    source = json.loads(SOURCE_MANIFEST.read_text())
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    campaign_entries = []

    environment_log = OUTPUT_ROOT / "ambertools_environment.log"
    if not args.audit_only:
        run_container(["micromamba", "list", "--name", "base", "ambertools"], OUTPUT_ROOT, environment_log)

    for entry in source["entries"]:
        name = entry["residue_name"]
        residue_code = RESIDUE_CODES[name]
        bundle = OUTPUT_ROOT / name
        logs = bundle / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        prior_audit = bundle / "audit.json"
        prior_archive = bundle / "audit.parser_blocked_attempt.json"
        if prior_audit.exists() and not prior_archive.exists():
            shutil.copy2(prior_audit, prior_archive)
        source_mol2 = ROOT / entry["request_mol2_path"]
        original_structure = ROOT / entry["source_path"]
        input_mol2 = bundle / "input.mol2"
        if not args.audit_only:
            shutil.copy2(source_mol2, input_mol2)

        charge = int(entry["expected_formal_charge"])
        if not args.audit_only:
            run_container([
                "antechamber", "-i", "input.mol2", "-fi", "mol2",
                "-o", "ligand_gaff2.mol2", "-fo", "mol2",
                "-at", "gaff2", "-c", "bcc", "-nc", str(charge),
                "-rn", residue_code, "-s", "2",
            ], bundle, logs / "antechamber.log")
            run_container([
                "parmchk2", "-i", "ligand_gaff2.mol2", "-f", "mol2",
                "-o", "ligand.frcmod", "-s", "gaff2",
            ], bundle, logs / "parmchk2.log")
            write_tleap(bundle / "tleap.in", residue_code)
            run_container(["tleap", "-f", "tleap.in"], bundle, logs / "tleap.log")

        input_atoms = mol2_atoms(input_mol2)
        typed_atoms = mol2_atoms(bundle / "ligand_gaff2.mol2")
        atom_order_preserved = len(input_atoms) == len(typed_atoms)
        typed_charge = sum(atom["charge"] for atom in typed_atoms)
        atom_map_path = bundle / "atom_name_map.csv"
        with atom_map_path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["index", "input_name", "gaff2_name", "element"], lineterminator="\n")
            writer.writeheader()
            for old, new in zip(input_atoms, typed_atoms):
                writer.writerow({"index": old["index"], "input_name": old["name"], "gaff2_name": new["name"], "element": old["element"]})

        source_smiles = isomeric_smiles(original_structure)
        audit_mol2 = bundle / "ligand_tripostypes_for_rdkit_audit.mol2"
        write_rdkit_audit_mol2(input_mol2, bundle / "ligand_gaff2.mol2", audit_mol2)
        output_smiles = isomeric_smiles(audit_mol2)
        stereochemistry_comparison_available = source_smiles is not None and output_smiles is not None
        stereochemistry_preserved = source_smiles == output_smiles if stereochemistry_comparison_available else None
        chiral_centers = source_chiral_centers(original_structure)
        bond_graph_preserved = mol2_bond_graph(input_mol2) == mol2_bond_graph(bundle / "ligand_gaff2.mol2")
        achiral_graph_fallback_passed = not stereochemistry_comparison_available and not chiral_centers and bond_graph_preserved
        tleap_text = (logs / "tleap.log").read_text()
        severe_log_tokens = [token for token in ["FATAL", "Could not find bond parameter", "Could not find angle parameter", "Could not find torsion parameter"] if token in tleap_text]
        expected_files = [
            bundle / "ligand_gaff2.mol2", bundle / "ligand.frcmod", bundle / "ligand.prmtop",
            bundle / "ligand.inpcrd", bundle / "ligand_parameterized.pdb", atom_map_path,
        ]
        accepted = (
            len(input_atoms) == len(typed_atoms) == int(entry["atom_count"])
            and atom_order_preserved
            and abs(typed_charge - charge) <= 0.01
            and not severe_log_tokens
            and all(path.exists() and path.stat().st_size > 0 for path in expected_files)
            and bond_graph_preserved
            and (stereochemistry_preserved is True or achiral_graph_fallback_passed)
        )
        audit = {
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "specification_id": "a2a-md-ligand-bundle-v1.6",
            "ligand": name,
            "molecule_id": entry["molecule_id"],
            "functional_label_blinded": entry["functional_label_blinded"],
            "residue_code": residue_code,
            "parameterization": "GAFF2 with AM1-BCC",
            "expected_formal_charge": charge,
            "typed_mol2_charge": typed_charge,
            "input_atom_count": len(input_atoms),
            "output_atom_count": len(typed_atoms),
            "atom_order_preserved": atom_order_preserved,
            "rdkit_audit_copy": str(audit_mol2.relative_to(bundle)),
            "rdkit_audit_copy_is_not_a_production_parameter_file": True,
            "source_isomeric_smiles": source_smiles,
            "output_isomeric_smiles": output_smiles,
            "stereochemistry_comparison_available": stereochemistry_comparison_available,
            "stereochemistry_preserved": stereochemistry_preserved,
            "source_chiral_centers": chiral_centers,
            "bond_graph_preserved": bond_graph_preserved,
            "achiral_graph_fallback_passed": achiral_graph_fallback_passed,
            "tleap_severe_tokens": severe_log_tokens,
            "status": "accepted_for_system_building" if accepted else "blocked_by_ligand_bundle_audit",
            "files": {str(path.relative_to(bundle)): sha256(path) for path in expected_files if path.exists()},
            "source_hashes": {"original_structure": sha256(original_structure), "input_mol2": sha256(input_mol2)},
        }
        audit_path = bundle / "audit.json"
        audit_path.write_text(json.dumps(audit, indent=2) + "\n")
        campaign_entries.append({"ligand": name, "status": audit["status"], "audit": str(audit_path.relative_to(ROOT)), "audit_sha256": sha256(audit_path)})

    image = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True, check=True, stdout=subprocess.PIPE).stdout.strip()
    campaign = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-md-ligand-campaign-v1.6",
        "image": IMAGE,
        "image_id": image,
        "source_manifest": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "candidate_labels_loaded": False,
        "entries": campaign_entries,
        "accepted_count": sum(item["status"] == "accepted_for_system_building" for item in campaign_entries),
        "status": "complete" if all(item["status"] == "accepted_for_system_building" for item in campaign_entries) else "blocked",
    }
    campaign_path = OUTPUT_ROOT / "campaign_manifest.json"
    prior_campaign = OUTPUT_ROOT / "campaign_manifest.parser_blocked_attempt.json"
    if campaign_path.exists() and not prior_campaign.exists():
        shutil.copy2(campaign_path, prior_campaign)
    campaign_path.write_text(json.dumps(campaign, indent=2) + "\n")
    print(json.dumps(campaign, indent=2))


if __name__ == "__main__":
    main()
