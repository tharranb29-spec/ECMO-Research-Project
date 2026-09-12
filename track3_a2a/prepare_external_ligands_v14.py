#!/usr/bin/env python3

"""Prepare label-blind pH 7.4 ligand states for the four v1.4 candidates."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from track3_a2a.prepare_provisional_ligands_v12 import canonical_variants, embed_variant
except ModuleNotFoundError:  # direct script execution
    from prepare_provisional_ligands_v12 import canonical_variants, embed_variant


ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "outputs" / "v1.4" / "external_cohort" / "literature_pilot_2025" / "eligible_candidates.csv"
CONFIG = ROOT / "config" / "ligand_prep.v1.2.json"
OUTPUT_DIR = ROOT / "docking_inputs" / "v1.4" / "literature_pilot_2025" / "ligands"
MANIFEST = ROOT / "outputs" / "v1.4" / "docking" / "literature_pilot_2025_ligand_manifest.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_for(record_id: str, variant_index: int) -> int:
    digest = hashlib.sha256(f"v1.4|{record_id}|{variant_index}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % (2**31 - 1) or 1


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    with CANDIDATES.open(newline="", encoding="utf-8") as stream:
        candidates = list(csv.DictReader(stream))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for candidate in sorted(candidates, key=lambda row: row["record_id"]):
        variants = canonical_variants(candidate["standardized_smiles"], config)
        for index, smiles in enumerate(variants, start=1):
            seed = seed_for(candidate["record_id"], index)
            molecule, optimization, optimization_status = embed_variant(smiles, seed)
            molecule.SetProp("_Name", f"{candidate['record_id']}_protomer_{index}")
            molecule.SetProp("CANDIDATE_ID", candidate["record_id"])
            molecule.SetProp("PRIMARY_PROTOMER", "true" if index == 1 else "false")
            molecule.SetProp("PH", "7.4")
            path = OUTPUT_DIR / f"{candidate['record_id']}_p{index}.sdf"
            from rdkit import Chem
            writer = Chem.SDWriter(str(path))
            writer.write(molecule)
            writer.close()
            entries.append({
                "candidate_id": candidate["record_id"],
                "functional_label_blinded": True,
                "protomer_index": index,
                "primary_protomer": index == 1,
                "protonated_smiles": smiles,
                "embedding_seed": seed,
                "optimization": optimization,
                "optimization_converged": optimization_status == 0,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            })
    payload = {
        "schema_version": 1,
        "created_at": utc_now(),
        "protocol_id": "a2a-external-validation-v1.4",
        "candidate_labels_loaded": False,
        "candidate_manifest_sha256": sha256(CANDIDATES),
        "ligand_prep_config_sha256": sha256(CONFIG),
        "candidate_count": len(candidates),
        "prepared_structure_count": len(entries),
        "primary_structure_count": sum(row["primary_protomer"] for row in entries),
        "entries": entries,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "entries"}, indent=2))


if __name__ == "__main__":
    main()
