#!/usr/bin/env python3
"""Validate and hash the prospective Track 3 v1.6 protocol freeze."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "protocol.v1.6.json"
AMENDMENT = ROOT / "V16_PROTOCOL_AMENDMENT.md"
OUTPUT = ROOT / "outputs" / "v1.6" / "protocol_freeze_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    spec = json.loads(CONFIG.read_text())
    require(spec["specification_id"] == "a2a-track3-protocol-v1.6", "wrong specification id")
    require("prospectively_frozen" in spec["status"], "protocol is not marked prospectively frozen")
    require(spec["endpoints"]["primary"]["name"] == "pBind_Ki", "primary endpoint drift")
    require(spec["models"]["primary_external_predictor"]["name"] == "AB_Ridge", "primary model drift")
    rf = spec["models"]["chemistry_rf_comparator"]["parameters"]
    require((rf["n_estimators"], rf["max_features"], rf["min_samples_leaf"]) == (500, "sqrt", 1), "RF freeze mismatch")
    require(spec["external_confirmation"]["computational_evidence_gate"]["human_approval_required"] is False, "human approval mismatch")
    require(spec["external_confirmation"]["one_time_outcome_join"] is True, "outcome join is not one-time")
    require(spec["md_v1_6"]["gdp_policy"]["decision"] == "omit_GDP_from_selected_BD_control", "GDP policy drift")
    require(spec["md_v1_6"]["tier_b"]["unlock_rule"] == "Both Tier A controls pass.", "Tier B gate drift")
    require(spec["release"]["automatic_model_replacement"] is False, "automatic promotion is prohibited")

    frozen_inputs = [CONFIG, AMENDMENT]
    manifest = {
        "schema_version": 1,
        "specification_id": spec["specification_id"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "frozen_and_machine_validated",
        "external_outcomes_joined": False,
        "md_trajectory_production_started": False,
        "human_approval_required": False,
        "frozen_decisions": {
            "primary_endpoint": "pBind_Ki",
            "primary_external_predictor": "AB_Ridge(alpha=1.0)",
            "rf_comparators": "500/sqrt/1; seed=20260914",
            "evidence_gate": "two independent computational passes; disagreement quarantined",
            "md_stack": "AmberTools25/OpenMM8.6/ff19SB/Lipid21/GAFF2-AM1-BCC/TIP3P",
            "gdp_policy": "selected 5G53 B/D control is nucleotide-free; cross-copy transfer prohibited",
            "tier_a_pilot": "2 controls x 3 replicas x 50 ns",
            "tier_b_pilot": "8 systems x 3 replicas x 20 ns; locked until Tier A passes"
        },
        "files": {str(path.relative_to(ROOT)): sha256(path) for path in frozen_inputs},
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["computational_release_signature_sha256"] = hashlib.sha256(canonical).hexdigest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
