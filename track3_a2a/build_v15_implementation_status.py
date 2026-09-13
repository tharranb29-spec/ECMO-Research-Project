#!/usr/bin/env python3

"""Build a concise machine-readable status for the v1.5 implementation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CURATION = ROOT / "outputs" / "v1.5" / "continuous_activity_curation_audit.json"
MODELS = ROOT / "outputs" / "v1.5" / "continuous_activity" / "development_results.json"
DOCKING = ROOT / "outputs" / "v1.4" / "docking" / "literature_pilot_2025_report.json"
MD = ROOT / "outputs" / "v1.5" / "md" / "preflight_status.json"
EXTERNAL_PBIND = ROOT / "outputs" / "v1.5" / "external_pbind_intake" / "intake_audit.json"
OUTPUT = ROOT / "outputs" / "v1.5" / "implementation_status.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric_summary(models: dict) -> dict:
    result = {}
    for endpoint, payload in models["results"].items():
        if payload["status"] != "complete_exploratory":
            result[endpoint] = payload
            continue
        primary = payload["primary"]
        delta = primary["uncertainty"]["paired_docking_increment"]
        result[endpoint] = {
            "status": payload["status"],
            "n": primary["n"],
            "scaffold_count": primary["scaffold_count"],
            "small_sample_warning": primary["small_sample_warning"],
            "AB_Ridge": primary["metrics"]["AB_Ridge"],
            "AB_RF": primary["metrics"]["AB_RF"],
            "E_RF": primary["metrics"]["E_RF"],
            "paired_docking_increment": delta,
        }
    return result


def main() -> None:
    inputs = {name: path for name, path in {
        "curation": CURATION, "models": MODELS, "external_docking": DOCKING,
        "external_pbind_intake": EXTERNAL_PBIND, "md_preflight": MD,
    }.items()}
    missing = [str(path) for path in inputs.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing v1.5 status inputs: {missing}")
    curation = json.loads(CURATION.read_text(encoding="utf-8"))
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    docking = json.loads(DOCKING.read_text(encoding="utf-8"))
    md = json.loads(MD.read_text(encoding="utf-8"))
    external_pbind = json.loads(EXTERNAL_PBIND.read_text(encoding="utf-8"))
    output = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-continuous-activity-v1.5",
        "stage": "external_pbind_intake_ready_primary_review_pending_md_preflight_blocked",
        "claim_status": "exploratory_only",
        "activity": {
            "activity_rows_seen": curation["activity_rows_seen"],
            "admitted_measurements": curation["admitted_measurements"],
            "quarantined_measurements": curation["quarantined_measurements"],
            "summary_molecules_by_endpoint": curation["summary_molecules_by_endpoint"],
            "eligible_development_counts": models["eligible_development_counts"],
            "historical_locked_holdout_rows_used": models["historical_locked_holdout_rows_used"],
            "development_results": metric_summary(models),
        },
        "external_candidate_docking": {
            "candidate_labels_loaded": docking["candidate_labels_loaded"],
            "candidate_count": docking["candidate_count"],
            "valid_candidate_count": docking["valid_candidate_count"],
            "failed_candidate_count": docking["failed_candidate_count"],
            "retained_pose_count": sum(
                "retained_pose" in receptor
                for candidate in docking["results"]
                for receptor in candidate["receptors"].values()
            ),
        },
        "md": {
            "status": md["status"],
            "trajectory_production_started": md["trajectory_production_started"],
            "candidate_labels_loaded": md["candidate_labels_loaded"],
            "blockers": md["blockers"],
        },
        "external_pbind_intake": {
            "outcomes_unmasked": external_pbind["outcomes_unmasked"],
            "membership_frozen": external_pbind["membership_frozen"],
            "eligible_for_primary_evidence_review_count": external_pbind[
                "eligible_for_primary_evidence_review_count"
            ],
            "eligible_generic_scaffold_count": external_pbind["eligible_generic_scaffold_count"],
            "floor_status_before_primary_review": external_pbind["floor_status_before_primary_review"],
            "next_gate": external_pbind["next_gate"],
        },
        "external_confirmation_performed": False,
        "model_promotion_allowed": False,
        "source_hashes": {name: sha256(path) for name, path in inputs.items()},
        "next_actions": [
            "Complete independent primary-evidence review and freeze an adequately powered external pBind_Ki cohort before outcomes are unmasked.",
            "Resolve the transferred-GDP/Ala366 clash, complete both Tier A construct models, and audit CGenFF ligand parameters.",
            "Build and audit the standardized POPC/cholesterol membrane systems and freeze native-contact definitions.",
            "Build and run Tier A native controls; interpret Tier B trajectories only if both control gates pass.",
        ],
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
