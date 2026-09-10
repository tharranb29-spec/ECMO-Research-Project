#!/usr/bin/env python3

"""Ingest human A2A functional activities into a non-training quarantine set."""

import argparse
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib import parse, request


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw" / "chembl251_functional"
CURATED = ROOT / "data" / "curated"
OUTPUTS = ROOT / "outputs" / "dataset"
API = "https://www.ebi.ac.uk/chembl/api/data/activity.json"
TARGET = "CHEMBL251"
PAGE_SIZE = 1000


ACTION_MAP = {
    "AGONIST": "agonist",
    "FULL AGONIST": "agonist",
    "PARTIAL AGONIST": "partial_agonist",
    "ANTAGONIST": "antagonist",
    "INVERSE AGONIST": "inverse_agonist",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_action(value):
    return re.sub(r"[_-]+", " ", str(value or "").strip().upper())


def infer_description_class(description):
    text = str(description or "").lower()
    if re.search(r"\binverse[- ]agonist", text):
        return "inverse_agonist"
    if re.search(r"\bpartial[- ]agonist", text):
        return "partial_agonist"
    antagonist = bool(re.search(r"\bantagonist|antagonistic|block(?:ade|ing)?\b", text))
    agonist = bool(re.search(r"\bagonist|agonistic|stimulation of|stimulated cAMP|activation of", text))
    if antagonist and not agonist:
        return "antagonist"
    if agonist and not antagonist:
        return "agonist"
    return None


def activity_class(activity):
    explicit = ACTION_MAP.get(normalize_action(activity.get("action_type")))
    inferred = infer_description_class(activity.get("assay_description"))
    if explicit and inferred and explicit != inferred:
        return None, "action_description_conflict"
    if explicit:
        return explicit, "chembl_action_type"
    if inferred:
        return inferred, "assay_description_rule"
    return None, "unresolved"


def fetch_page(offset, refresh=False):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"activities_offset_{offset}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8")), path
    query = parse.urlencode({
        "target_chembl_id": TARGET,
        "assay_type": "F",
        "limit": PAGE_SIZE,
        "offset": offset,
    })
    req = request.Request(f"{API}?{query}", headers={"User-Agent": "ZJU-ISM-A2A-Track3/1.0"})
    last_error = None
    for attempt in range(3):
        try:
            with request.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            return payload, path
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"ChEMBL request failed after retries: {last_error}")


def source_url(molecule_id):
    return f"https://www.ebi.ac.uk/chembl/explore/compound/{molecule_id}"


def main():
    parser = argparse.ArgumentParser(description="Build the CHEMBL251 functional quarantine snapshot")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached raw pages")
    args = parser.parse_args()
    first, first_path = fetch_page(0, refresh=args.refresh)
    total = int(first["page_meta"]["total_count"])
    pages = [(first, first_path)]
    for offset in range(PAGE_SIZE, total, PAGE_SIZE):
        pages.append(fetch_page(offset, refresh=args.refresh))
    activities = [row for payload, _ in pages for row in payload.get("activities", [])]

    grouped = defaultdict(list)
    for row in activities:
        molecule_key = row.get("parent_molecule_chembl_id") or row.get("molecule_chembl_id")
        if molecule_key and row.get("canonical_smiles"):
            grouped[molecule_key].append(row)

    records = []
    class_counts = Counter()
    reason_counts = Counter()
    conflict_count = 0
    for molecule_id, rows in sorted(grouped.items()):
        assessments = [activity_class(row) for row in rows]
        proposed = {label for label, _ in assessments if label}
        reasons = Counter(reason for _, reason in assessments)
        conflict = len(proposed) > 1 or reasons.get("action_description_conflict", 0) > 0
        if conflict:
            functional_class = "ambiguous"
            conflict_count += 1
        elif proposed:
            functional_class = next(iter(proposed))
        else:
            functional_class = "unknown"
        class_counts[functional_class] += 1
        reason_counts.update(reasons)
        representative = max(
            rows,
            key=lambda row: (
                bool(row.get("action_type")),
                bool(row.get("pchembl_value")),
                bool(row.get("standard_value")),
            ),
        )
        records.append({
            "record_id": f"chembl251-{molecule_id.lower()}",
            "molecule_name": representative.get("molecule_pref_name") or molecule_id,
            "chembl_id": molecule_id,
            "canonical_smiles": representative["canonical_smiles"],
            "standardized_smiles": None,
            "inchikey": None,
            "dataset_partition": "quarantine",
            "functional_class": functional_class,
            "primary_binary_label": None,
            "evidence_status": "ambiguous",
            "assay_type": "ChEMBL functional assay collection",
            "assay_readout": representative.get("standard_type"),
            "activity_relation": representative.get("standard_relation"),
            "activity_value": float(representative["standard_value"]) if representative.get("standard_value") else None,
            "activity_unit": representative.get("standard_units"),
            "source_type": "ChEMBL API functional activity",
            "source_id": representative.get("assay_chembl_id"),
            "source_url": source_url(molecule_id),
            "source_passage": representative.get("assay_description"),
            "label_rationale": (
                f"Automated quarantine proposal from {len(rows)} activity row(s); "
                f"classification signals={sorted(proposed)}; conflicts={conflict}."
            ),
            "reviewed_by": None,
            "reviewed_at": None,
            "parent_record_id": None,
            "ingested_at": utc_now(),
        })

    CURATED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    quarantine = {
        "schema_version": 1,
        "target_chembl_id": TARGET,
        "dataset_partition": "quarantine",
        "training_eligible_count": 0,
        "records": records,
    }
    (CURATED / "chembl251_functional_quarantine.json").write_text(json.dumps(quarantine, indent=2) + "\n", encoding="utf-8")
    snapshot = {
        "created_at": utc_now(),
        "target_chembl_id": TARGET,
        "api_query": {"assay_type": "F", "page_size": PAGE_SIZE},
        "reported_activity_count": total,
        "retrieved_activity_count": len(activities),
        "unique_molecule_count_with_smiles": len(records),
        "training_eligible_count": 0,
        "provisional_functional_class_counts": dict(sorted(class_counts.items())),
        "classification_signal_counts": dict(sorted(reason_counts.items())),
        "molecules_with_conflicting_signals": conflict_count,
        "raw_pages": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "activity_count": len(payload.get("activities", []))}
            for payload, path in pages
        ],
        "next_actions": [
            "Standardize structures and collapse salt, tautomer, and stereochemical duplicates.",
            "Audit assay descriptions and action_type consistency at molecule level.",
            "Verify agonist and antagonist labels against functional assay publications.",
            "Assign benchmark and locked-holdout partitions only after scaffold analysis.",
        ],
    }
    (OUTPUTS / "chembl251_dataset_audit.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()

