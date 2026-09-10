#!/usr/bin/env python3

"""Prepare pH-aware 3D ligand inputs for provisional A2A docking."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dimorphite_dl import protonate_smiles
from rdkit import Chem
from rdkit.Chem import AllChem


ROOT = Path(__file__).resolve().parent
PARTITIONS = ROOT / "data" / "curated" / "chembl251_provisional_partitions_v1.2.json"
CONFIG = ROOT / "config" / "ligand_prep.v1.2.json"
OUTPUT_DIR = ROOT / "docking_inputs" / "v1.2" / "ligands"
MANIFEST = ROOT / "outputs" / "v1.2" / "ligand_preparation_manifest.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def seed_for(chembl_id, variant_index):
    digest = hashlib.sha256(f"{chembl_id}|{variant_index}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % (2**31 - 1) or 1


def canonical_variants(smiles, config):
    values = protonate_smiles(
        smiles,
        ph_min=config["protonation"]["ph_min"],
        ph_max=config["protonation"]["ph_max"],
        precision=config["protonation"]["precision"],
        max_variants=config["protonation"]["max_variants"],
    )
    canonical = set()
    for value in values:
        molecule = Chem.MolFromSmiles(value)
        if molecule is None:
            continue
        canonical.add(Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True))
    if not canonical:
        raise ValueError("No valid pH-adjusted protomer generated")
    return sorted(canonical)


def embed_variant(smiles, seed):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError("RDKit could not parse protonated SMILES")
    molecule = Chem.AddHs(molecule)
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    params.useRandomCoords = False
    status = AllChem.EmbedMolecule(molecule, params)
    if status != 0:
        params.useRandomCoords = True
        status = AllChem.EmbedMolecule(molecule, params)
    if status != 0:
        raise ValueError("ETKDGv3 embedding failed")
    if AllChem.MMFFHasAllMoleculeParams(molecule):
        optimization = "MMFF94"
        optimization_status = AllChem.MMFFOptimizeMolecule(molecule, maxIters=500)
    else:
        optimization = "UFF"
        optimization_status = AllChem.UFFOptimizeMolecule(molecule, maxIters=500)
    return molecule, optimization, int(optimization_status)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    partition_payload = json.loads(PARTITIONS.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    failures = []
    molecule_variant_counts = Counter()
    optimization_counts = Counter()
    for record in partition_payload["records"]:
        try:
            variants = canonical_variants(record["standardized_smiles"], config)
        except Exception as exc:  # noqa: BLE001
            failures.append({"chembl_id": record["chembl_id"], "stage": "protonation", "error": str(exc)})
            continue
        molecule_variant_counts[len(variants)] += 1
        for index, smiles in enumerate(variants, start=1):
            seed = seed_for(record["chembl_id"], index)
            try:
                molecule, optimization, optimization_status = embed_variant(smiles, seed)
            except Exception as exc:  # noqa: BLE001
                failures.append({"chembl_id": record["chembl_id"], "variant_index": index, "stage": "embedding", "error": str(exc)})
                continue
            molecule.SetProp("_Name", f"{record['chembl_id']}_protomer_{index}")
            molecule.SetProp("CHEMBL_ID", record["chembl_id"])
            molecule.SetProp("PROTOMER_INDEX", str(index))
            molecule.SetProp("PRIMARY_PROTOMER", "true" if index == 1 else "false")
            molecule.SetProp("PH", "7.4")
            molecule.SetProp("PARTITION", record["partition"])
            path = OUTPUT_DIR / f"{record['chembl_id']}_p{index}.sdf"
            writer = Chem.SDWriter(str(path))
            writer.write(molecule)
            writer.close()
            optimization_counts[optimization] += 1
            entries.append({
                "chembl_id": record["chembl_id"],
                "partition": record["partition"],
                "functional_class_blinded_for_docking": True,
                "protomer_index": index,
                "primary_protomer": index == 1,
                "protonated_smiles": smiles,
                "formal_charge": Chem.GetFormalCharge(Chem.RemoveHs(molecule)),
                "embedding_seed": seed,
                "optimization": optimization,
                "optimization_converged": optimization_status == 0,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path)
            })
    manifest = {
        "schema_version": 1,
        "created_at": utc_now(),
        "protocol_id": config["protocol_id"],
        "partition_status": "provisional_computational_only",
        "human_validation_claimed": False,
        "input_partition_sha256": sha256(PARTITIONS),
        "config_sha256": sha256(CONFIG),
        "molecule_count": len(partition_payload["records"]),
        "prepared_structure_count": len(entries),
        "primary_structure_count": sum(item["primary_protomer"] for item in entries),
        "alternate_structure_count": sum(not item["primary_protomer"] for item in entries),
        "molecule_variant_counts": {str(key): value for key, value in sorted(molecule_variant_counts.items())},
        "optimization_counts": dict(sorted(optimization_counts.items())),
        "failure_count": len(failures),
        "failures": failures,
        "entries": entries,
        "next_gate": "provisional dual-state GNINA production protocol and smoke batch"
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key not in {"entries", "failures"}}, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
