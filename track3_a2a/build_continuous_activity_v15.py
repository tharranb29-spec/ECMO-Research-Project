#!/usr/bin/env python3

"""Apply the frozen v1.5 activity gate and build separate molecule targets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rdkit import Chem


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "continuous_activity.v1.5.json"
RAW = ROOT / "data" / "raw" / "chembl251_activity_v15"
FEATURES = ROOT / "outputs" / "v1.3" / "docking_clean_computational.csv"
CURATED = ROOT / "data" / "curated"
OUTPUTS = ROOT / "outputs" / "v1.5"
LEDGER_FIELDS = [
    "measurement_id", "molecule_id", "standardized_inchikey", "endpoint_name",
    "functional_mode", "functional_mode_source", "standard_type", "standard_relation",
    "standard_value", "standard_units", "pactivity_value", "pactivity_recalculated",
    "pactivity_absolute_difference", "assay_chembl_id", "target_chembl_id", "target_gene",
    "target_organism", "target_type", "target_confidence", "assay_type", "bao_format",
    "cell_chembl_id", "document_chembl_id", "doi", "pmid", "document_type",
    "source_retrieved_at", "data_validity_comment", "activity_comment", "review_status",
    "admission_reasons", "development_partition",
]
SUMMARY_FIELDS = [
    "molecule_id", "standardized_inchikey", "endpoint_name", "functional_mode",
    "aggregated_pactivity", "measurement_count", "assay_count", "primary_document_count",
    "interassay_sd", "interassay_mad", "minimum_pactivity", "maximum_pactivity",
    "high_disagreement_flag", "development_partition", "external_eligibility", "review_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalize(value: object) -> str:
    return re.sub(r"[_-]+", " ", str(value or "").strip().lower())


def functional_mode(activity: dict, assay: dict) -> tuple[str | None, str]:
    action = normalize(activity.get("action_type"))
    text = " ".join([
        action,
        normalize(activity.get("assay_description")),
        normalize(assay.get("description")),
        normalize(activity.get("activity_comment")),
    ])
    if "inverse agonist" in text:
        return "inverse_agonist", "explicit_text"
    if "partial agonist" in text:
        return "partial_agonist", "explicit_text"
    if action in {"agonist", "full agonist"}:
        return "full_agonist" if action == "full agonist" else "agonist", "action_type"
    if action == "antagonist":
        return "antagonist", "action_type"
    antagonist = bool(re.search(r"\bantagonist|\binhibit(?:s|ed|ion)?\b|\bblock(?:s|ed|ade)?\b", text))
    agonist = bool(re.search(r"\bagonist|\bactivat(?:e|es|ed|ion)\b|\bstimulat(?:e|es|ed|ion)\b", text))
    if antagonist:
        return "antagonist", "assay_text_rule"
    if agonist:
        return "agonist", "assay_text_rule"
    return None, "unresolved"


def endpoint_for(activity: dict, mode: str | None) -> str | None:
    assay_type = activity.get("assay_type")
    standard_type = activity.get("standard_type")
    if assay_type == "B" and standard_type == "Ki":
        return "pBind_Ki"
    if assay_type == "F" and standard_type in {"EC50", "Potency"} and mode in {"agonist", "full_agonist"}:
        return "pFunc_agonism"
    if assay_type == "F" and standard_type in {"IC50", "Potency"} and mode == "antagonist":
        return "pFunc_inhibition"
    if assay_type == "F" and standard_type in {"IC50", "Potency"} and mode == "inverse_agonist":
        return "pFunc_inverse_agonism"
    return None


def has_unassigned_stereocenter(smiles: str) -> bool:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        return True
    return any(label == "?" for _, label in Chem.FindMolChiralCenters(
        molecule, includeUnassigned=True, useLegacyImplementation=False
    ))


def numeric(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def admission_reasons(
    activity: dict,
    assay: dict,
    document: dict,
    target: dict,
    molecule: dict,
    endpoint: str | None,
    pcalc: float | None,
) -> list[str]:
    reasons = []
    if endpoint is None:
        reasons.append("endpoint_or_functional_mode_not_admitted")
    if activity.get("target_chembl_id") != "CHEMBL251" or assay.get("target_chembl_id") != "CHEMBL251":
        reasons.append("wrong_target")
    if activity.get("target_organism") != "Homo sapiens" or assay.get("assay_organism") not in {None, "Homo sapiens"}:
        reasons.append("non_human_context")
    if target.get("target_type") != "SINGLE PROTEIN":
        reasons.append("target_not_single_protein")
    if int(assay.get("confidence_score") or 0) < 8:
        reasons.append("target_confidence_below_8")
    if activity.get("standard_relation") != "=":
        reasons.append("non_exact_relation")
    if activity.get("standard_units") != "nM":
        reasons.append("non_nm_units")
    value = numeric(activity.get("standard_value"))
    if value is None or value <= 0:
        reasons.append("non_positive_or_missing_value")
    validity = activity.get("data_validity_comment")
    if validity not in {None, "", "Manually validated"}:
        reasons.append("disallowed_validity_comment")
    if activity.get("assay_variant_mutation") or assay.get("variant_sequence"):
        reasons.append("mutant_or_variant_assay")
    pchembl = numeric(activity.get("pchembl_value"))
    if pchembl is None or pcalc is None or abs(pchembl - pcalc) > 0.05:
        reasons.append("pchembl_missing_or_inconsistent")
    doc_type = str(document.get("doc_type") or "").upper()
    if doc_type != "PUBLICATION":
        reasons.append("not_primary_publication")
    if not document.get("doi") and not document.get("pubmed_id"):
        reasons.append("doi_or_pmid_missing")
    if not molecule.get("standardized_inchikey") or not molecule.get("standardized_smiles"):
        reasons.append("standardized_structure_missing")
    elif has_unassigned_stereocenter(molecule["standardized_smiles"]):
        reasons.append("unassigned_stereocenter")
    return reasons


def median_absolute_deviation(values: list[float]) -> float:
    center = statistics.median(values)
    return statistics.median(abs(value - center) for value in values)


def aggregate(ledger: list[dict]) -> list[dict]:
    admitted = [row for row in ledger if row["review_status"] == "admitted_exploratory"]
    assay_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in admitted:
        key = (row["molecule_id"], row["standardized_inchikey"], row["endpoint_name"],
               row["functional_mode"], row["assay_chembl_id"])
        assay_groups[key].append(row)
    molecule_groups: dict[tuple, list[tuple[float, list[dict]]]] = defaultdict(list)
    for key, rows in assay_groups.items():
        molecule_groups[key[:4]].append((statistics.median(float(row["pactivity_value"]) for row in rows), rows))

    summaries = []
    for key, assay_values in sorted(molecule_groups.items()):
        molecule_id, inchikey, endpoint, mode = key
        values = [value for value, _ in assay_values]
        all_rows = [row for _, rows in assay_values for row in rows]
        sd = statistics.stdev(values) if len(values) > 1 else None
        summaries.append({
            "molecule_id": molecule_id,
            "standardized_inchikey": inchikey,
            "endpoint_name": endpoint,
            "functional_mode": mode,
            "aggregated_pactivity": f"{statistics.median(values):.6f}",
            "measurement_count": len(all_rows),
            "assay_count": len(values),
            "primary_document_count": len({row["document_chembl_id"] for row in all_rows}),
            "interassay_sd": "" if sd is None else f"{sd:.6f}",
            "interassay_mad": f"{median_absolute_deviation(values):.6f}",
            "minimum_pactivity": f"{min(values):.6f}",
            "maximum_pactivity": f"{max(values):.6f}",
            "high_disagreement_flag": bool(sd is not None and sd > 0.75),
            "development_partition": all_rows[0]["development_partition"],
            "external_eligibility": False,
            "review_status": "admitted_exploratory",
        })
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--features", type=Path, default=FEATURES)
    parser.add_argument("--output-dir", type=Path, default=OUTPUTS)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    activities = json.loads((args.raw / "activities.json").read_text(encoding="utf-8"))
    assays = {row["assay_chembl_id"]: row for row in json.loads((args.raw / "assays.json").read_text(encoding="utf-8"))}
    documents = {row["document_chembl_id"]: row for row in json.loads((args.raw / "documents.json").read_text(encoding="utf-8"))}
    target = json.loads((args.raw / "target.json").read_text(encoding="utf-8"))
    molecules = {row["molecule_id"]: row for row in read_csv(args.features)}
    retrieved_at = json.loads((args.raw / "acquisition_manifest.json").read_text(encoding="utf-8"))["created_at"]

    ledger = []
    for activity in activities:
        molecule_id = activity.get("parent_molecule_chembl_id") or activity.get("molecule_chembl_id")
        if molecule_id not in molecules:
            continue
        assay = assays.get(activity.get("assay_chembl_id"), {})
        document = documents.get(activity.get("document_chembl_id"), {})
        mode, mode_source = functional_mode(activity, assay)
        endpoint = endpoint_for(activity, mode)
        value = numeric(activity.get("standard_value"))
        pcalc = 9.0 - math.log10(value) if value is not None and value > 0 and activity.get("standard_units") == "nM" else None
        reasons = admission_reasons(activity, assay, document, target, molecules[molecule_id], endpoint, pcalc)
        ledger.append({
            "measurement_id": activity.get("activity_id"),
            "molecule_id": molecule_id,
            "standardized_inchikey": molecules[molecule_id].get("standardized_inchikey"),
            "endpoint_name": endpoint or "",
            "functional_mode": mode or "",
            "functional_mode_source": mode_source,
            "standard_type": activity.get("standard_type"),
            "standard_relation": activity.get("standard_relation"),
            "standard_value": activity.get("standard_value"),
            "standard_units": activity.get("standard_units"),
            "pactivity_value": activity.get("pchembl_value"),
            "pactivity_recalculated": "" if pcalc is None else f"{pcalc:.6f}",
            "pactivity_absolute_difference": "" if pcalc is None or numeric(activity.get("pchembl_value")) is None else f"{abs(numeric(activity['pchembl_value']) - pcalc):.6f}",
            "assay_chembl_id": activity.get("assay_chembl_id"),
            "target_chembl_id": activity.get("target_chembl_id"),
            "target_gene": "ADORA2A",
            "target_organism": activity.get("target_organism"),
            "target_type": target.get("target_type"),
            "target_confidence": assay.get("confidence_score"),
            "assay_type": activity.get("assay_type"),
            "bao_format": activity.get("bao_format"),
            "cell_chembl_id": assay.get("cell_chembl_id"),
            "document_chembl_id": activity.get("document_chembl_id"),
            "doi": document.get("doi"),
            "pmid": document.get("pubmed_id"),
            "document_type": document.get("doc_type"),
            "source_retrieved_at": retrieved_at,
            "data_validity_comment": activity.get("data_validity_comment"),
            "activity_comment": activity.get("activity_comment"),
            "review_status": "admitted_exploratory" if not reasons else "quarantine",
            "admission_reasons": "|".join(reasons),
            "development_partition": molecules[molecule_id].get("partition"),
        })
    ledger.sort(key=lambda row: (str(row["molecule_id"]), str(row["measurement_id"])))
    summaries = aggregate(ledger)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = CURATED / "activity_measurements_v15_exploratory.csv"
    summary_path = CURATED / "activity_molecule_summary_v15_exploratory.csv"
    write_csv(ledger_path, LEDGER_FIELDS, ledger)
    write_csv(summary_path, SUMMARY_FIELDS, summaries)

    admitted = [row for row in ledger if row["review_status"] == "admitted_exploratory"]
    audit = {
        "schema_version": 1,
        "created_at": utc_now(),
        "specification_id": config["specification_id"],
        "claim_status": "exploratory_only",
        "source_hashes": {
            "config": sha256(CONFIG),
            "features": sha256(args.features),
            "acquisition_manifest": sha256(args.raw / "acquisition_manifest.json"),
        },
        "activity_rows_seen": len(ledger),
        "admitted_measurements": len(admitted),
        "quarantined_measurements": len(ledger) - len(admitted),
        "admitted_by_endpoint": dict(sorted(Counter(row["endpoint_name"] for row in admitted).items())),
        "summary_molecules_by_endpoint": dict(sorted(Counter(row["endpoint_name"] for row in summaries).items())),
        "quarantine_reasons": dict(sorted(Counter(reason for row in ledger for reason in row["admission_reasons"].split("|") if reason).items())),
        "high_disagreement_molecules": [
            {"molecule_id": row["molecule_id"], "endpoint_name": row["endpoint_name"]}
            for row in summaries if row["high_disagreement_flag"]
        ],
        "historical_locked_holdout_measurements_admitted_but_model_ineligible": sum(
            row["development_partition"] == "locked_holdout" for row in admitted
        ),
        "outputs": {
            "ledger": {"path": str(ledger_path.relative_to(ROOT)), "sha256": sha256(ledger_path)},
            "summary": {"path": str(summary_path.relative_to(ROOT)), "sha256": sha256(summary_path)},
        },
    }
    audit_path = args.output_dir / "continuous_activity_curation_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
