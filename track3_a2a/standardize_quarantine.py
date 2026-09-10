#!/usr/bin/env python3

"""Standardize quarantined A2A structures and audit duplicate/scaffold risk."""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, QED, rdMolDescriptors
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data" / "curated" / "chembl251_functional_quarantine.json"
OUTPUT = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
AUDIT = ROOT / "outputs" / "dataset" / "structure_standardization_audit.json"

UNCHARGER = rdMolStandardize.Uncharger()
TAUTOMER_ENUMERATOR = rdMolStandardize.TautomerEnumerator()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def standardize_smiles(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError("RDKit could not parse canonical_smiles")
    cleaned = rdMolStandardize.Cleanup(molecule)
    parent = rdMolStandardize.FragmentParent(cleaned)
    uncharged = UNCHARGER.uncharge(parent)
    # Rebuild ring information that can be cleared by parent/charge transforms.
    Chem.SanitizeMol(uncharged)
    canonical_tautomer = TAUTOMER_ENUMERATOR.Canonicalize(uncharged)
    standardized_smiles = Chem.MolToSmiles(uncharged, canonical=True, isomericSmiles=True)
    tautomer_smiles = Chem.MolToSmiles(canonical_tautomer, canonical=True, isomericSmiles=True)
    inchikey = Chem.MolToInchiKey(uncharged)
    scaffold = MurckoScaffold.GetScaffoldForMol(uncharged)
    scaffold_smiles = Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=True) if scaffold.GetNumAtoms() else ""
    generic_scaffold = MurckoScaffold.MakeScaffoldGeneric(scaffold) if scaffold.GetNumAtoms() else None
    generic_scaffold_smiles = Chem.MolToSmiles(generic_scaffold, canonical=True) if generic_scaffold else ""
    descriptors = {
        "molecular_weight": round(Descriptors.MolWt(uncharged), 4),
        "clogp": round(Crippen.MolLogP(uncharged), 4),
        "h_bond_donors": int(Lipinski.NumHDonors(uncharged)),
        "h_bond_acceptors": int(Lipinski.NumHAcceptors(uncharged)),
        "rotatable_bonds": int(Lipinski.NumRotatableBonds(uncharged)),
        "tpsa": round(rdMolDescriptors.CalcTPSA(uncharged), 4),
        "heavy_atom_count": int(uncharged.GetNumHeavyAtoms()),
        "qed": round(QED.qed(uncharged), 6),
    }
    filters = {
        "mw_200_to_600": 200 <= descriptors["molecular_weight"] <= 600,
        "qed_above_0_3": descriptors["qed"] > 0.3,
    }
    return {
        "standardized_smiles": standardized_smiles,
        "canonical_tautomer_smiles": tautomer_smiles,
        "standardized_inchikey": inchikey,
        "murcko_scaffold_smiles": scaffold_smiles,
        "generic_murcko_scaffold_smiles": generic_scaffold_smiles,
        "descriptors": descriptors,
        "property_filters": filters,
        "passes_declared_property_filters": all(filters.values()),
    }


def main():
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    standardized = []
    errors = []
    by_inchikey = defaultdict(list)
    class_counts = Counter()
    scaffold_counts = Counter()
    for record in payload["records"]:
        try:
            chemistry = standardize_smiles(record["canonical_smiles"])
        except Exception as exc:  # noqa: BLE001
            errors.append({"record_id": record["record_id"], "chembl_id": record.get("chembl_id"), "error": str(exc)})
            continue
        row = {**record, **chemistry}
        row["training_eligible"] = False
        row["training_blocker"] = "functional label and assay provenance require review"
        standardized.append(row)
        by_inchikey[chemistry["standardized_inchikey"]].append(row)
        class_counts[row["functional_class"]] += 1
        scaffold_counts[chemistry["generic_murcko_scaffold_smiles"] or "ACYCLIC"] += 1

    duplicate_groups = []
    contradictory_structure_groups = 0
    for key, rows in by_inchikey.items():
        if len(rows) < 2:
            continue
        classes = sorted({row["functional_class"] for row in rows})
        if len({value for value in classes if value not in {"unknown", "ambiguous"}}) > 1:
            contradictory_structure_groups += 1
        duplicate_groups.append({
            "standardized_inchikey": key,
            "record_count": len(rows),
            "chembl_ids": sorted({row.get("chembl_id") for row in rows if row.get("chembl_id")}),
            "provisional_classes": classes,
        })

    output = {
        "schema_version": 1,
        "created_at": utc_now(),
        "rdkit_version": getattr(__import__("rdkit"), "__version__", "unknown"),
        "dataset_partition": "quarantine",
        "training_eligible_count": 0,
        "records": standardized,
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    audit = {
        "created_at": utc_now(),
        "input_record_count": len(payload["records"]),
        "successfully_standardized_count": len(standardized),
        "invalid_structure_count": len(errors),
        "unique_standardized_structure_count": len(by_inchikey),
        "duplicate_standardized_structure_group_count": len(duplicate_groups),
        "duplicate_groups_with_contradictory_provisional_classes": contradictory_structure_groups,
        "generic_scaffold_count_including_acyclic": len(scaffold_counts),
        "acyclic_record_count": scaffold_counts.get("ACYCLIC", 0),
        "passes_declared_property_filters_count": sum(row["passes_declared_property_filters"] for row in standardized),
        "provisional_class_counts": dict(sorted(class_counts.items())),
        "largest_scaffold_groups": [
            {"generic_scaffold": scaffold, "record_count": count}
            for scaffold, count in scaffold_counts.most_common(20)
        ],
        "errors": errors,
        "duplicate_groups": duplicate_groups,
        "training_eligible_count": 0,
        "next_gate": "evidence review and scaffold-balanced benchmark selection",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key not in {"errors", "duplicate_groups", "largest_scaffold_groups"}}, indent=2))


if __name__ == "__main__":
    main()
