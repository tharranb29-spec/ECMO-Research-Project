#!/usr/bin/env python3
"""Build the machine-readable v1.6 workstream status from audited artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "v1.6" / "implementation_status.json"


def load(relative: str) -> tuple[dict, Path]:
    path = ROOT / relative
    return json.loads(path.read_text()), path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    freeze, freeze_path = load("outputs/v1.6/protocol_freeze_manifest.json")
    model, model_path = load("outputs/v1.6/model_reproduction/development_results.json")
    ligands, ligand_path = load("outputs/v1.6/md/ligand_bundles/campaign_manifest.json")
    pubmed, pubmed_path = load("outputs/v1.6/external_evidence/pubmed_retrieval_audit.json")
    pmc, pmc_path = load("outputs/v1.6/external_evidence/pmc_fulltext_retrieval_audit.json")
    metrics = model["result"]["metrics"]
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-track3-protocol-v1.6",
        "deadline": "2026-09-30",
        "external_outcomes_joined": False,
        "md_trajectory_production_started": False,
        "candidate_labels_loaded_for_md": False,
        "workstreams": {
            "A_protocol_and_governance": {
                "status": "exit_gate_passed",
                "freeze_signature": freeze["computational_release_signature_sha256"],
                "primary_endpoint": "pBind_Ki",
                "primary_model": "AB_Ridge",
                "rf_comparator": "500/sqrt/1",
                "development_reproduction": {
                    "n": model["result"]["n"],
                    "generic_murcko_scaffolds": model["result"]["scaffold_count"],
                    "r2": {name: values["r2"] for name, values in metrics.items()},
                },
            },
            "B_external_confirmation": {
                "status": "evidence_retrieval_in_progress_membership_not_frozen",
                "queue_candidates": 240,
                "pubmed_requested": pubmed["requested_pmid_count"],
                "pubmed_retrieved": pubmed["retrieved_article_count"],
                "pmc_requested": pmc["requested_pmcid_count"],
                "pmc_fulltext_retrieved": pmc["retrieved_fulltext_count"],
                "pmc_fulltext_unavailable": pmc["failed_fulltext_count"],
                "next_gate": "deterministic source triage plus independent source-grounded extraction; freeze membership only after agreement",
            },
            "C_open_md": {
                "status": "ligand_gate_passed_construct_gate_pending",
                "ambertools_image": ligands["image"],
                "ambertools_image_id": ligands["image_id"],
                "accepted_ligand_bundles": ligands["accepted_count"],
                "required_ligand_bundles": 6,
                "gdp_policy": "nucleotide-free selected 5G53 B/D mini-Gs control",
                "tier_a_unlocked_for_trajectory": False,
                "tier_b_unlocked": False,
                "next_gate": "complete and audit two Tier A receptor constructs, membranes, native contacts, and local minimization/NVT/NPT smoke tests",
            },
            "D_dashboard": {
                "status": "scheduled_to_start_2026-09-16",
                "current_mode": "legacy_dashboard_preserved",
                "next_gate": "static versioned Track 3 evidence contracts before autonomous shadow-mode integration",
            },
        },
        "artifact_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in [freeze_path, model_path, ligand_path, pubmed_path, pmc_path]
        },
        "timeline_status": "on_track_for_September_14_protocol_and_open_parameterization_milestone",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
