#!/usr/bin/env python3

"""Run v1.1.1 after the explicit-hydrogen-independent box correction."""

import json
from pathlib import Path

from run_redocking_gate import run_case


ROOT = Path(__file__).resolve().parent
BASE_CONFIG = ROOT / "config" / "protocol.v1.1.json"
OUTPUTS = ROOT / "outputs" / "v1.1.1"


def main():
    config = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    config["protocol_id"] = "a2a-dual-state-v1.1.1"
    status_path = OUTPUTS / "preparation_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status["shared_box"].get("atom_selection") != "heavy_atoms_only":
        raise SystemExit("v1.1.1 heavy-atom box correction is missing")
    box = status["shared_box"]
    cases = [
        run_case(
            "v1.1.1-5NM4",
            ROOT / status["assets"]["inactive_receptor"],
            ROOT / status["assets"]["inactive_reference_ligand"],
            box,
            config,
        ),
        run_case(
            "v1.1.1-2YDO",
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
        "preserved_results": ["outputs/redocking_report.json", "outputs/v1.1/redocking_report.json"],
        "implementation_correction": "docking box calculated from heavy atoms only",
        "acceptance_rule": config["redocking_gate"],
        "cases": cases,
        "next_gate": "functional-label dataset curation and scaffold audit" if gate_passed else "review primary receptor and pose-selection design",
    }
    (OUTPUTS / "redocking_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    status["stage"] = "redocking_gate_passed" if gate_passed else "redocking_gate_failed"
    status["redocking_gate_passed"] = gate_passed
    status["model_training_unlocked"] = gate_passed
    status["production_screening_unlocked"] = False
    status["next_gate"] = report["next_gate"]
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

