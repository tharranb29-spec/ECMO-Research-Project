#!/usr/bin/env python3

"""Prepare and audit the direct Siglec-9 GNINA validation inputs.

This utility deliberately stops before docking when source coordinates or
chemical identity have not passed the provenance gate.
"""

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "docking_inputs" / "structure_registry.json"
VALIDATION_PATH = ROOT / "outputs" / "gnina_validation.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_atom(line):
    return {
        "name": line[12:16].strip(),
        "resname": line[17:20].strip(),
        "chain": line[21:22],
        "residue": int(line[22:26]),
        "xyz": tuple(float(line[start : start + 8]) for start in (30, 38, 46)),
    }


def vector(first, second):
    return tuple(second[index] - first[index] for index in range(3))


def cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def dot(first, second):
    return sum(first[index] * second[index] for index in range(3))


def norm(value):
    return math.sqrt(dot(value, value))


def dihedral(a, b, c, d):
    b0 = vector(b, a)
    b1 = vector(b, c)
    b2 = vector(c, d)
    b1_norm = norm(b1)
    if not b1_norm:
        raise ValueError("Cannot calculate a dihedral with a zero-length bond.")
    b1_unit = tuple(value / b1_norm for value in b1)
    v = tuple(b0[index] - dot(b0, b1_unit) * b1_unit[index] for index in range(3))
    w = tuple(b2[index] - dot(b2, b1_unit) * b1_unit[index] for index in range(3))
    return math.degrees(math.atan2(dot(cross(b1_unit, v), w), dot(v, w)))


def crop_v_set(source_path, output_path, start=18, end=144):
    kept = []
    confidence = []
    atom_index = {}
    residue_names = {}
    for raw_line in source_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.startswith(("ATOM  ", "HETATM")):
            continue
        atom = parse_atom(raw_line)
        if atom["chain"] == "A" and start <= atom["residue"] <= end:
            kept.append(raw_line)
            atom_index[(atom["residue"], atom["name"])] = atom["xyz"]
            residue_names[atom["residue"]] = atom["resname"]
            try:
                confidence.append(float(raw_line[60:66]))
            except ValueError:
                pass
    if not kept:
        raise ValueError(f"No chain A residues {start}-{end} were found in {source_path}.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(kept + ["TER", "END", ""]) , encoding="utf-8")

    required = [(52, "CA"), (52, "C"), (53, "N"), (53, "CA")]
    missing = [key for key in required if key not in atom_index]
    omega = None if missing else dihedral(*(atom_index[key] for key in required))
    p53_state = "unresolved" if omega is None else "cis" if abs(omega) < 30 else "trans" if abs(abs(omega) - 180) < 30 else "noncanonical"
    return {
        "residue_span": f"{start}-{end}",
        "atom_count": len(kept),
        "mean_plddt": round(sum(confidence) / len(confidence), 2) if confidence else None,
        "minimum_plddt": round(min(confidence), 2) if confidence else None,
        "residue_36": residue_names.get(36),
        "p53_omega_degrees": round(omega, 2) if omega is not None else None,
        "p53_state": p53_state,
        "sha256": sha256(output_path),
    }


def update_registry(source_path, cropped_path, audit):
    registry = read_json(REGISTRY_PATH, {}) or {}
    registry["last_updated"] = utc_now()
    registry.setdefault("schema_version", 1)
    prepared_pdb = cropped_path.with_name("siglec9_vset_18-144_ph7.4.pdb")
    prepared_pqr = cropped_path.with_name("siglec9_vset_18-144_ph7.4.pqr")
    registry["direct_siglec9_gate"] = {
        "status": "reconstructed_ligand_coordinates_pending_independent_review",
        "ranking_unlocked": False,
        "receptor": {
            "target": "human Siglec-9 V-set domain",
            "uniprot_accession": "Q9Y336",
            "source_type": "AlphaFold DB reconstruction candidate",
            "source_model": "AF-Q9Y336-F1-model_v6",
            "source_url": "https://alphafold.ebi.ac.uk/files/AF-Q9Y336-F1-model_v6.pdb",
            "source_model_created": "2025-08-01",
            "paper_domain_span": "18-144",
            "paper_model_note": "The published study used AlphaFold and RoseTTAFold models; these exact author coordinate files were not deposited with the article.",
            "sequence_variant": "canonical wild-type Q9Y336",
            "study_construct_note": "The NMR construct reported in the supporting information carried C36S; this reconstruction retains canonical C36 and therefore is not study-identical.",
            "local_source_path": str(source_path.relative_to(ROOT)),
            "local_cropped_path": str(cropped_path.relative_to(ROOT)),
            "local_prepared_path": str(prepared_pdb.relative_to(ROOT)) if prepared_pdb.exists() else None,
            "local_pqr_path": str(prepared_pqr.relative_to(ROOT)) if prepared_pqr.exists() else None,
            "prepared_pdb_sha256": sha256(prepared_pdb) if prepared_pdb.exists() else None,
            "prepared_pqr_sha256": sha256(prepared_pqr) if prepared_pqr.exists() else None,
            "preparation_protocol": "PDB2PQR 3.6.2; AMBER naming; PROPKA pH 7.4; hydrogen-bond optimization",
            "source_sha256": sha256(source_path),
            "audit": audit,
            "review_status": "provisional_reconstruction",
        },
        "ligands": [
            {
                "name": "BTCNeu5Ac",
                "chemical_description": "5-N-[(1-benzhydryl-1H-1,2,3-triazol-4-yl)methyl carbamate]-Neu5Ac alpha(2-6)Gal beta(1-4)GlcNAc",
                "published_itc_kd_micromolar": {"value": 19.5, "sd": 1.3},
                "coordinate_status": "literature_reconstructed_3d_coordinates",
                "review_status": "provisional_pending_carbohydrate_chemist_review",
                "local_path": "docking_inputs/siglec9/BTCNeu5Ac.sdf",
                "sha256": "e5503c295aee25b04371b4fc98495bdc7d0689e555ded921efd60f0a969bf475",
                "molecular_formula": "C40H53N5O20",
            },
            {
                "name": "MTTSNeu5Ac",
                "chemical_description": "9N-[5-(2-methylthiazol-4-yl)thiophene sulfonamide]-Neu5Ac alpha(2-6)Gal beta(1-4)GlcNAc",
                "published_itc_kd_micromolar": {"value": 9.6, "sd": 0.8},
                "coordinate_status": "literature_reconstructed_3d_coordinates",
                "review_status": "provisional_pending_carbohydrate_chemist_review",
                "local_path": "docking_inputs/siglec9/MTTSNeu5Ac.sdf",
                "sha256": "ae2a08dee2595552e1e88e0812181242e752dc61580f94f43c42631f8c49a5d3",
                "molecular_formula": "C33H48N4O20S3",
            },
        ],
        "evidence": {
            "primary_article_doi": "10.1021/acschembio.3c00664",
            "primary_article_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10877568/",
            "published_modeling_method": "NMR-guided manual placement followed by five independent 500 ns AMBER MD trajectories",
            "published_template": "PDB 7QUI Siglec-8/NSANeu5Ac",
            "required_contact_checks": ["R120-carboxylate salt bridge", "W128 Neu5Ac stacking", "N129 glycerol-chain hydrogen bonding"],
        },
        "blocking_reasons": [
            "Exact author Siglec-9 model coordinates are not deposited with the article.",
            "The available AlphaFold reconstruction is canonical WT, while the reported NMR construct carried C36S.",
            "BTCNeu5Ac and MTTSNeu5Ac are literature-reconstructed rather than author-deposited coordinates and still require independent carbohydrate-chemistry review.",
            "NMR/MD interaction constraints have not yet been reproduced on this reconstruction.",
        ],
    }
    write_json(REGISTRY_PATH, registry)
    return registry


def update_validation(registry):
    validation = read_json(VALIDATION_PATH, {}) or {}
    validation["last_updated"] = utc_now()
    gate = registry["direct_siglec9_gate"]
    validation["direct_target_assets"] = {
        "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
        "status": gate["status"],
        "ranking_unlocked": gate["ranking_unlocked"],
        "receptor_review_status": gate["receptor"]["review_status"],
        "receptor_p53_state": gate["receptor"]["audit"]["p53_state"],
        "verified_ligand_count": sum(item["review_status"] == "verified" for item in gate["ligands"]),
        "reconstructed_ligand_count": sum("reconstructed" in item.get("coordinate_status", "") for item in gate["ligands"]),
        "required_ligand_count": len(gate["ligands"]),
        "blocking_reasons": gate["blocking_reasons"],
    }
    next_gate = validation.setdefault("next_gate", {})
    next_gate["status"] = "in_progress_pending_independent_chemistry_and_interaction_review"
    next_gate["requirements"] = [
        "Independent carbohydrate-chemistry review of reconstructed BTCNeu5Ac and MTTSNeu5Ac structures",
        "Reproduction of the published Siglec-9 interaction constraints",
        "Matched multi-seed docking after chemistry sign-off",
        "Comparison with published affinity and interaction evidence",
    ]
    write_json(VALIDATION_PATH, validation)


def main():
    parser = argparse.ArgumentParser(description="Audit direct Siglec-9 validation assets.")
    parser.add_argument("--source", default="docking_inputs/siglec9/AF-Q9Y336-F1-model_v6.pdb")
    parser.add_argument("--output", default="docking_inputs/siglec9/siglec9_vset_18-144_raw.pdb")
    args = parser.parse_args()
    source_path = (ROOT / args.source).resolve()
    output_path = (ROOT / args.output).resolve()
    if not source_path.exists():
        raise SystemExit(f"Missing source model: {source_path}")
    audit = crop_v_set(source_path, output_path)
    registry = update_registry(source_path, output_path, audit)
    update_validation(registry)
    print(json.dumps({"receptor_audit": audit, "ranking_unlocked": False}, indent=2))


if __name__ == "__main__":
    main()
