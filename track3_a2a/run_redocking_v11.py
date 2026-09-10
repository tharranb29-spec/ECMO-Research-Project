#!/usr/bin/env python3

"""Run the frozen v1.1 five-seed 5NM4/2YDO redocking gate."""

import json
from pathlib import Path

from run_redocking_gate import run_case


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "protocol.v1.1.json"
OUTPUTS = ROOT / "outputs" / "v1.1"
STATUS_PATH = OUTPUTS / "preparation_status.json"


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    if not status.get("source_checksums_verified") or not status["shared_box"].get("aligned_adenosine_inside"):
        raise SystemExit("v1.1 source/alignment gate is not ready")
    box = status["shared_box"]
    cases = [
        run_case(
            "v1.1-5NM4",
            ROOT / status["assets"]["inactive_receptor"],
            ROOT / status["assets"]["inactive_reference_ligand"],
            box,
            config,
        ),
        run_case(
            "v1.1-2YDO",
            ROOT / status["assets"]["active_like_receptor"],
            ROOT / status["assets"]["active_like_reference_ligand"],
            box,
            config,
        ),
    ]
    gate_passed = all(case["status"] == "pass" for case in cases)
    report = {
        "protocol_id": config["protocol_id"],
        "gate": "primary_pair_cognate_redocking",
        "status": "pass" if gate_passed else "fail",
        "model_training_unlocked": gate_passed,
        "production_screening_unlocked": False,
        "preserved_v1_0_failure": config["change_control"]["preserved_negative_result"],
        "mandatory_sensitivity_structure": "4EIY",
        "interpretation": "Pose-recovery validation only; no efficacy or experimental-affinity claim.",
        "acceptance_rule": config["redocking_gate"],
        "cases": cases,
        "next_gate": "functional-label dataset curation and scaffold audit" if gate_passed else "review v1.1 receptor preparation",
    }
    (OUTPUTS / "redocking_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    status["stage"] = "redocking_gate_passed" if gate_passed else "redocking_gate_failed"
    status["redocking_gate_passed"] = gate_passed
    status["model_training_unlocked"] = gate_passed
    status["production_screening_unlocked"] = False
    status["next_gate"] = report["next_gate"]
    STATUS_PATH.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

