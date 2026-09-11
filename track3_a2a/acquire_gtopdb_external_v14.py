#!/usr/bin/env python3

"""Create a label-free GtoPdb A2A structure snapshot from a sealed interaction export."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "external" / "gtopdb_2026.2"
STRUCTURE_URL = "https://www.guidetopharmacology.org/services/ligands/{ligand_id}/structure"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_structure(ligand_id: int, attempts: int = 3) -> dict:
    url = STRUCTURE_URL.format(ligand_id=ligand_id)
    error = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ECMO-Track3-v1.4/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            error = exc
            if attempt + 1 < attempts:
                time.sleep(1.0 + attempt)
    raise RuntimeError(f"failed to retrieve ligand {ligand_id}: {error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("interaction_snapshot", type=Path)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    retrieved_at = datetime.fromisoformat(args.retrieved_at.replace("Z", "+00:00"))
    if retrieved_at.tzinfo is None:
        raise ValueError("--retrieved-at must include a UTC offset")
    interactions = json.loads(args.interaction_snapshot.read_text(encoding="utf-8"))
    ligands = {
        int(row["ligandId"]): row["ligandName"]
        for row in interactions
        if row.get("targetId") == 19 and row.get("targetSpecies") == "Human"
    }
    structures, errors = {}, []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_structure, ligand_id): ligand_id for ligand_id in ligands}
        for future in as_completed(futures):
            ligand_id = futures[future]
            try:
                structures[ligand_id] = future.result()
            except Exception as exc:  # noqa: BLE001
                errors.append({"ligand_id": ligand_id, "error": str(exc)})

    args.output_dir.mkdir(parents=True, exist_ok=True)
    structure_path = args.output_dir / "target_19_label_free_structures.json"
    candidate_path = args.output_dir / "external_candidates_gtopdb_2026.2.csv"
    audit_path = args.output_dir / "source_acquisition_audit.json"
    structure_payload = {
        "schema_version": 1,
        "source": "IUPHAR/BPS Guide to PHARMACOLOGY",
        "release": "2026.2",
        "target_id": 19,
        "target_species": "Human",
        "retrieved_at": retrieved_at.astimezone(timezone.utc).isoformat(),
        "labels_included": False,
        "structures": [structures[key] for key in sorted(structures)],
    }
    structure_path.write_text(json.dumps(structure_payload, indent=2) + "\n", encoding="utf-8")
    source_snapshot_id = f"gtopdb-2026.2-target19-{sha256(structure_path)[:16]}"
    fields = [
        "record_id", "molecule_name", "external_identifier", "canonical_smiles",
        "source_cohort", "source_type", "source_id", "source_url", "source_snapshot_id",
        "source_published_at", "source_retrieved_at", "prior_project_visibility",
        "source_independence_basis", "priority_category", "evidence_status", "ingested_at",
    ]
    with candidate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for ligand_id in sorted(structures):
            structure = structures[ligand_id]
            if not structure.get("smiles"):
                continue
            writer.writerow({
                "record_id": f"GTPDB-{ligand_id}",
                "molecule_name": structure.get("ligandName") or ligands[ligand_id],
                "external_identifier": f"GtoPdb:{ligand_id}",
                "canonical_smiles": structure["smiles"],
                "source_cohort": "GtoPdb 2026.2 human A2A",
                "source_type": "independent_curated_database",
                "source_id": str(ligand_id),
                "source_url": f"https://www.guidetopharmacology.org/GRAC/LigandDisplayForward?ligandId={ligand_id}",
                "source_snapshot_id": source_snapshot_id,
                "source_published_at": "2026-06-15",
                "source_retrieved_at": retrieved_at.astimezone(timezone.utc).isoformat(),
                "prior_project_visibility": "false",
                "source_independence_basis": "first project access after v1.3 freeze; automated check against full pre-freeze structure pool still required",
                "priority_category": "",
                "evidence_status": "unreviewed_action_annotation_withheld",
                "ingested_at": retrieved_at.astimezone(timezone.utc).isoformat(),
            })
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_id": source_snapshot_id,
        "sealed_interaction_snapshot_sha256": sha256(args.interaction_snapshot),
        "sealed_interaction_count": len(interactions),
        "unique_human_a2a_ligand_count": len(ligands),
        "retrieved_structure_count": len(structures),
        "candidate_with_smiles_count": sum(bool(row.get("smiles")) for row in structures.values()),
        "retrieval_errors": errors,
        "labels_in_structure_snapshot": False,
        "labels_in_candidate_csv": False,
        "structure_snapshot_sha256": sha256(structure_path),
        "candidate_csv_sha256": sha256(candidate_path),
        "next_gate": "run screen_external_candidates_v14.py before any evidence labels are joined",
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
