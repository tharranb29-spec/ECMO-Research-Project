#!/usr/bin/env python3

"""Build the versioned Step 3 A2A docking feature matrix and audit."""

import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "feature_construction.v1.2.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median_run_value(receptor, field):
    values = [
        run[field]
        for run in receptor["runs"]
        if run["status"] == "valid" and run.get(field) is not None
    ]
    return round(statistics.median(values), 4) if values else None


def index_unique(records, key, consistency_fields=()):
    grouped = defaultdict(list)
    for record in records:
        grouped[record[key]].append(record)
    indexed = {}
    for value, matches in grouped.items():
        for field in consistency_fields:
            representations = {json.dumps(row.get(field), sort_keys=True) for row in matches}
            if len(representations) != 1:
                raise ValueError(f"Conflicting {field} values for {value}")
        indexed[value] = matches[0]
    return indexed


def build_feature_row(molecule, partition, evidence, chemistry, config):
    inactive = molecule["receptors"]["inactive_5NM4"]
    active = molecule["receptors"]["active_like_2YDO"]
    x_inactive = inactive["median_affinity_kcal_mol"]
    x_active = active["median_affinity_kcal_mol"]
    m_affinity = (x_active + x_inactive) / 2
    d_affinity = x_active - x_inactive
    descriptors = chemistry["descriptors"]
    heavy_atoms = descriptors["heavy_atom_count"]
    if not heavy_atoms:
        raise ValueError(f"Missing heavy atoms for {molecule['chembl_id']}")

    inactive_cnn = inactive["median_cnn_score"]
    active_cnn = active["median_cnn_score"]
    inactive_cnnaffinity = median_run_value(inactive, "cnn_affinity_pk")
    active_cnnaffinity = median_run_value(active, "cnn_affinity_pk")
    if None in {inactive_cnn, active_cnn, inactive_cnnaffinity, active_cnnaffinity}:
        raise ValueError(f"Missing CNN aggregate for {molecule['chembl_id']}")

    threshold = config["pose_quality"]["cnnscore_flag_threshold"]
    inactive_flags = sum(
        run["cnn_score"] is None or run["cnn_score"] <= threshold
        for run in inactive["runs"]
        if run["status"] == "valid"
    )
    active_flags = sum(
        run["cnn_score"] is None or run["cnn_score"] <= threshold
        for run in active["runs"]
        if run["status"] == "valid"
    )

    return {
        "molecule_id": molecule["chembl_id"],
        "molecule_name": partition["molecule_name"],
        "label": partition["functional_class"],
        "binary_label": partition["primary_binary_label"],
        "evidence_tier": evidence["recommended_evidence_tier"],
        "label_status": config["label_status"],
        "human_validation_claimed": False,
        "training_eligible": False,
        "partition": partition["partition"],
        "standardized_smiles": partition["standardized_smiles"],
        "standardized_inchikey": partition["standardized_inchikey"],
        "murcko_scaffold_smiles": chemistry["murcko_scaffold_smiles"],
        "generic_murcko_scaffold_smiles": partition["generic_murcko_scaffold_smiles"],
        "molecular_weight": descriptors["molecular_weight"],
        "clogp": descriptors["clogp"],
        "h_bond_donors": descriptors["h_bond_donors"],
        "h_bond_acceptors": descriptors["h_bond_acceptors"],
        "rotatable_bonds": descriptors["rotatable_bonds"],
        "tpsa": descriptors["tpsa"],
        "heavy_atom_count": heavy_atoms,
        "qed": descriptors["qed"],
        "x_inactive_5NM4_affinity_kcal_mol": x_inactive,
        "x_active_like_2YDO_affinity_kcal_mol": x_active,
        "m_affinity_kcal_mol": round(m_affinity, 4),
        "d_affinity_kcal_mol": round(d_affinity, 4),
        "d_affinity_per_heavy_atom": round(d_affinity / heavy_atoms, 6),
        "inactive_5NM4_affinity_sd": inactive["affinity_sd"],
        "active_like_2YDO_affinity_sd": active["affinity_sd"],
        "inactive_5NM4_valid_seeds": inactive["valid_seed_count"],
        "active_like_2YDO_valid_seeds": active["valid_seed_count"],
        "inactive_5NM4_median_cnnscore": inactive_cnn,
        "active_like_2YDO_median_cnnscore": active_cnn,
        "m_cnnscore": round((active_cnn + inactive_cnn) / 2, 4),
        "d_cnnscore": round(active_cnn - inactive_cnn, 4),
        "inactive_5NM4_median_cnnaffinity_pk": inactive_cnnaffinity,
        "active_like_2YDO_median_cnnaffinity_pk": active_cnnaffinity,
        "m_cnnaffinity_pk": round((active_cnnaffinity + inactive_cnnaffinity) / 2, 4),
        "d_cnnaffinity_pk": round(active_cnnaffinity - inactive_cnnaffinity, 4),
        "inactive_5NM4_cnnscore_flagged_seeds": inactive_flags,
        "active_like_2YDO_cnnscore_flagged_seeds": active_flags,
        "cnnscore_flagged_seeds_total": inactive_flags + active_flags,
        "cnnscore_soft_flag_any": inactive_flags + active_flags > 0,
        "pose_quality_status": "retain_with_soft_flag" if inactive_flags + active_flags else "pass",
    }


def quality_summary(rows):
    summary = {}
    for label in ("agonist", "antagonist"):
        selected = [row for row in rows if row["label"] == label]
        inactive_flags = sum(row["inactive_5NM4_cnnscore_flagged_seeds"] for row in selected)
        active_flags = sum(row["active_like_2YDO_cnnscore_flagged_seeds"] for row in selected)
        receptor_runs = len(selected) * 3
        summary[label] = {
            "molecule_count": len(selected),
            "molecules_with_any_soft_flag": sum(row["cnnscore_soft_flag_any"] for row in selected),
            "inactive_5NM4": {
                "flagged_seed_count": inactive_flags,
                "seed_count": receptor_runs,
                "flag_rate": round(inactive_flags / receptor_runs, 6),
            },
            "active_like_2YDO": {
                "flagged_seed_count": active_flags,
                "seed_count": receptor_runs,
                "flag_rate": round(active_flags / receptor_runs, 6),
            },
            "all_receptors": {
                "flagged_seed_count": inactive_flags + active_flags,
                "seed_count": receptor_runs * 2,
                "flag_rate": round((inactive_flags + active_flags) / (receptor_runs * 2), 6),
            },
        }
    return summary


def hard_filter_sensitivity(rows):
    output = {}
    for label in ("agonist", "antagonist"):
        selected = [row for row in rows if row["label"] == label]
        output[label] = {
            "unfiltered": len(selected),
            "all_six_seeds_pass": sum(row["cnnscore_flagged_seeds_total"] == 0 for row in selected),
            "at_least_two_passing_seeds_per_receptor": sum(
                row["inactive_5NM4_cnnscore_flagged_seeds"] <= 1
                and row["active_like_2YDO_cnnscore_flagged_seeds"] <= 1
                for row in selected
            ),
            "at_least_one_passing_seed_per_receptor": sum(
                row["inactive_5NM4_cnnscore_flagged_seeds"] <= 2
                and row["active_like_2YDO_cnnscore_flagged_seeds"] <= 2
                for row in selected
            ),
        }
    return output


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    input_paths = {name: ROOT / value for name, value in config["inputs"].items()}
    inputs = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in input_paths.items()}

    partitions = index_unique(inputs["partitions"]["records"], "chembl_id")
    reviews = index_unique(inputs["evidence_review"]["records"], "chembl_id")
    chemistry = index_unique(
        inputs["standardized_chemistry"]["records"],
        "chembl_id",
        ("standardized_smiles", "descriptors", "murcko_scaffold_smiles"),
    )

    rows = []
    missing_metadata = []
    for molecule in inputs["docking_report"]["molecules"]:
        chembl_id = molecule["chembl_id"]
        if chembl_id not in partitions or chembl_id not in reviews or chembl_id not in chemistry:
            missing_metadata.append(chembl_id)
            continue
        rows.append(build_feature_row(molecule, partitions[chembl_id], reviews[chembl_id], chemistry[chembl_id], config))

    rows.sort(key=lambda row: row["molecule_id"])
    output_path = ROOT / config["outputs"]["feature_matrix"]
    audit_path = ROOT / config["outputs"]["audit"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No feature rows were produced")
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    class_counts = Counter(row["label"] for row in rows)
    partition_counts = Counter(row["partition"] for row in rows)
    class_partition_counts = Counter(f"{row['partition']}:{row['label']}" for row in rows)
    tier_counts = Counter(row["evidence_tier"] for row in rows)
    scaffold_counts = {
        label: Counter(
            row["generic_murcko_scaffold_smiles"] or "ACYCLIC"
            for row in rows
            if row["label"] == label
        )
        for label in ("agonist", "antagonist")
    }
    audit = {
        "schema_version": 1,
        "created_at": utc_now(),
        "protocol_id": config["protocol_id"],
        "human_validation_claimed": False,
        "training_eligible_count": 0,
        "source_hashes": {name: sha256(path) for name, path in input_paths.items()},
        "feature_matrix_sha256": sha256(output_path),
        "input_docked_molecule_count": len(inputs["docking_report"]["molecules"]),
        "output_row_count": len(rows),
        "missing_metadata_ids": missing_metadata,
        "class_counts": dict(sorted(class_counts.items())),
        "partition_counts": dict(sorted(partition_counts.items())),
        "class_partition_counts": dict(sorted(class_partition_counts.items())),
        "evidence_tier_counts": dict(sorted(tier_counts.items())),
        "pose_quality_policy": config["pose_quality"],
        "pose_quality_by_provisional_class": quality_summary(rows),
        "hard_filter_sensitivity_not_primary": hard_filter_sensitivity(rows),
        "scaffold_summary": {
            label: {
                "unique_generic_scaffolds": len(counts),
                "singleton_scaffolds": sum(count == 1 for count in counts.values()),
                "largest_scaffold_group": max(counts.values()),
            }
            for label, counts in scaffold_counts.items()
        },
        "partition_scaffold_overlap": sorted(
            {
                row["generic_murcko_scaffold_smiles"] or "ACYCLIC"
                for row in rows
                if row["partition"] == "provisional_development"
            }
            & {
                row["generic_murcko_scaffold_smiles"] or "ACYCLIC"
                for row in rows
                if row["partition"] == "provisional_locked_holdout"
            }
        ),
        "orthogonal_feature_definitions": {
            "m_affinity_kcal_mol": "(x_active_like_2YDO + x_inactive_5NM4) / 2",
            "d_affinity_kcal_mol": "x_active_like_2YDO - x_inactive_5NM4",
            "d_affinity_per_heavy_atom": "d_affinity_kcal_mol / heavy_atom_count",
            "m_cnnscore": "(active_like_2YDO_median_cnnscore + inactive_5NM4_median_cnnscore) / 2",
            "d_cnnscore": "active_like_2YDO_median_cnnscore - inactive_5NM4_median_cnnscore",
        },
        "primary_matrix_status": "provisional_computational_only",
        "next_gate": "independent label review and scaffold audit before model fitting",
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
