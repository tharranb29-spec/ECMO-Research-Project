#!/usr/bin/env python3
"""Aggregate all six frozen Tier A equilibration audits without replica selection."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "tier_a_equilibration.v1.6.1.json"
DEFAULT_INPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_equilibration"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    records = []
    missing = []
    for system_id in config["systems"]:
        for seed in config["replica_seeds"]:
            path = args.input / system_id / f"seed-{seed}" / "equilibration_audit.json"
            if not path.is_file():
                missing.append(str(path.relative_to(args.input)))
                continue
            audit = json.loads(path.read_text())
            records.append({
                "system_id": system_id, "seed": seed, "path": str(path.relative_to(args.input)),
                "sha256": sha256(path), "status": audit["status"],
                "config_sha256": audit["config_sha256"],
            })
    expected = len(config["systems"]) * len(config["replica_seeds"])
    passed = sum(row["status"] == "equilibration_gate_passed" for row in records)
    accepted = not missing and len(records) == expected and passed == expected and all(
        row["config_sha256"] == sha256(CONFIG) for row in records
    )
    report = {
        "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-tier-a-equilibration-gate-v1.6.1",
        "config_sha256": sha256(CONFIG), "expected_run_count": expected,
        "observed_run_count": len(records), "passed_run_count": passed,
        "missing_audits": missing, "runs": records,
        "status": "tier_a_equilibration_gate_passed" if accepted else "tier_a_equilibration_gate_locked",
        "tier_a_production_unlocked": accepted, "tier_b_unlocked": False,
        "best_replica_selection": "prohibited",
        "claim_limit": "This gate authorizes Tier A pilot production; it does not establish control stability or unlock Tier B.",
    }
    output = args.output or args.input / "equilibration_gate_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
