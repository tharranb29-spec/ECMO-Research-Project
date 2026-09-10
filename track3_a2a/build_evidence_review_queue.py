#!/usr/bin/env python3

"""Build a human-review queue from A2A records with genuine functional readouts."""

import csv
import glob
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from track3_a2a.ingest_chembl_functional import activity_class


ROOT = Path(__file__).resolve().parent
STANDARDIZED = ROOT / "data" / "curated" / "chembl251_standardized_quarantine.json"
RAW_GLOB = str(ROOT / "data" / "raw" / "chembl251_functional" / "activities_offset_*.json")
QUEUE = ROOT / "data" / "curated" / "chembl251_functional_review_queue.csv"
PACKET = ROOT / "data" / "curated" / "chembl251_functional_review_packet.json"
AUDIT = ROOT / "outputs" / "dataset" / "functional_evidence_gate_audit.json"

FUNCTIONAL_READOUT = re.compile(
    r"cAMP|cyclic AMP|adenyl(?:yl|ate) cyclase|calcium mobilization|intracellular calcium|"
    r"GTP(?:gamma|\u03b3|\[35S\])|G-protein|luciferase|reporter gene|CRE[- ]|"
    r"ERK|MAPK|inositol phosphate|IP1|impedance|receptor internalization",
    re.IGNORECASE,
)
BINDING_READOUT = re.compile(
    r"radioligand|binding affinity|binding assay|binding inhibition|"
    r"displacement|competition binding|\[(?:3H|125I)\]",
    re.IGNORECASE,
)


def classify_readout(description):
    text = str(description or "")
    functional = bool(FUNCTIONAL_READOUT.search(text))
    binding = bool(BINDING_READOUT.search(text))
    if functional:
        return "functional"
    if binding:
        return "binding_only"
    return "unresolved"


def molecule_key(row):
    return row.get("parent_molecule_chembl_id") or row.get("molecule_chembl_id")


def load_raw_rows():
    rows = []
    for path in sorted(glob.glob(RAW_GLOB)):
        rows.extend(json.loads(Path(path).read_text(encoding="utf-8")).get("activities", []))
    return rows


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def main():
    standardized = json.loads(STANDARDIZED.read_text(encoding="utf-8"))["records"]
    raw_rows = load_raw_rows()
    by_molecule = defaultdict(list)
    readout_counts = Counter()
    for row in raw_rows:
        key = molecule_key(row)
        if not key:
            continue
        row = dict(row)
        row["evidence_readout_class"] = classify_readout(row.get("assay_description"))
        row["proposed_functional_class"], row["classification_rule"] = activity_class(row)
        readout_counts[row["evidence_readout_class"]] += 1
        by_molecule[key].append(row)

    queue_rows = []
    packet_rows = []
    exclusion_counts = Counter()
    for record in standardized:
        activities = by_molecule.get(record["chembl_id"], [])
        functional_rows = [
            row for row in activities
            if row["evidence_readout_class"] == "functional"
            and row["proposed_functional_class"] in {"agonist", "antagonist"}
        ]
        labels = sorted({row["proposed_functional_class"] for row in functional_rows})
        if not functional_rows:
            exclusion_counts["no_classifiable_functional_readout"] += 1
            continue
        if len(labels) != 1:
            exclusion_counts["conflicting_functional_labels"] += 1
            continue

        assays = sorted({row.get("assay_chembl_id") for row in functional_rows if row.get("assay_chembl_id")})
        documents = sorted({row.get("document_chembl_id") for row in functional_rows if row.get("document_chembl_id")})
        evidence_strength = "high" if len(assays) >= 2 and len(documents) >= 2 else "medium" if len(assays) >= 2 else "initial"
        representative = max(
            functional_rows,
            key=lambda row: (bool(row.get("action_type")), bool(row.get("pchembl_value")), bool(row.get("standard_value"))),
        )
        queue_rows.append({
            "chembl_id": record["chembl_id"],
            "molecule_name": record["molecule_name"],
            "proposed_class": labels[0],
            "evidence_strength": evidence_strength,
            "functional_activity_rows": len(functional_rows),
            "unique_assays": len(assays),
            "unique_documents": len(documents),
            "representative_assay": representative.get("assay_chembl_id") or "",
            "representative_document": representative.get("document_chembl_id") or "",
            "representative_readout": representative.get("standard_type") or "",
            "representative_description": representative.get("assay_description") or "",
            "standardized_smiles": record["standardized_smiles"],
            "standardized_inchikey": record["standardized_inchikey"],
            "generic_scaffold": record["generic_murcko_scaffold_smiles"],
            "passes_prospective_property_filters": record["passes_declared_property_filters"],
            "review_decision": "",
            "reviewer": "",
            "review_notes": "",
        })
        packet_rows.append({
            "chembl_id": record["chembl_id"],
            "proposed_class": labels[0],
            "evidence_strength": evidence_strength,
            "training_eligible": False,
            "functional_evidence": [
                {
                    "activity_id": row.get("activity_id"),
                    "assay_chembl_id": row.get("assay_chembl_id"),
                    "document_chembl_id": row.get("document_chembl_id"),
                    "document_journal": row.get("document_journal"),
                    "document_year": row.get("document_year"),
                    "description": row.get("assay_description"),
                    "standard_type": row.get("standard_type"),
                    "standard_relation": row.get("standard_relation"),
                    "standard_value": row.get("standard_value"),
                    "standard_units": row.get("standard_units"),
                    "pchembl_value": row.get("pchembl_value"),
                    "proposed_functional_class": row["proposed_functional_class"],
                    "classification_rule": row["classification_rule"],
                }
                for row in functional_rows
            ],
        })

    strength_order = {"high": 0, "medium": 1, "initial": 2}
    queue_rows.sort(key=lambda row: (strength_order[row["evidence_strength"]], row["proposed_class"], row["chembl_id"]))
    packet_rows.sort(key=lambda row: (strength_order[row["evidence_strength"]], row["proposed_class"], row["chembl_id"]))
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(queue_rows[0]))
        writer.writeheader()
        writer.writerows(queue_rows)
    PACKET.write_text(json.dumps({
        "schema_version": 1,
        "created_at": utc_now(),
        "dataset_partition": "quarantine",
        "training_eligible_count": 0,
        "records": packet_rows,
    }, indent=2) + "\n", encoding="utf-8")

    audit = {
        "created_at": utc_now(),
        "raw_activity_rows": len(raw_rows),
        "readout_class_counts": dict(sorted(readout_counts.items())),
        "standardized_molecule_count": len(standardized),
        "molecules_queued_for_human_review": len(queue_rows),
        "queue_class_counts": dict(sorted(Counter(row["proposed_class"] for row in queue_rows).items())),
        "queue_evidence_strength_counts": dict(sorted(Counter(row["evidence_strength"] for row in queue_rows).items())),
        "excluded_molecule_counts": dict(sorted(exclusion_counts.items())),
        "training_eligible_count": 0,
        "important_note": "Property filters are prospective-screening descriptors and do not determine retrospective benchmark eligibility.",
        "admission_rule": "A reviewer must confirm a functional readout, agonist/antagonist direction, source document, and absence of context conflict.",
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
