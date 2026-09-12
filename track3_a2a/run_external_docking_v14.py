#!/usr/bin/env python3

"""Run the frozen label-blind dual-state docking gate for v1.4 candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import statistics
from datetime import datetime, timezone
from pathlib import Path

try:
    from track3_a2a.run_provisional_docking_v12 import aggregate_runs, run_seed
except ModuleNotFoundError:  # direct script execution
    from run_provisional_docking_v12 import aggregate_runs, run_seed


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
EXTERNAL_CONFIG = ROOT / "config" / "external_validation.v1.4.json"
DOCKING_CONFIG = ROOT / "config" / "docking_provisional.v1.2.json"
POSE_CONFIG = ROOT / "config" / "md_pose_selection.v1.5.json"
PREPARATION = ROOT / "outputs" / "v1.1.1" / "preparation_status.json"
LIGANDS = ROOT / "outputs" / "v1.4" / "docking" / "literature_pilot_2025_ligand_manifest.json"
OUTPUT = ROOT / "outputs" / "v1.4" / "docking"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retained_run(runs: list[dict]) -> dict:
    valid = [run for run in runs if run["status"] == "valid"]
    if not valid:
        raise ValueError("No valid seed is available for retained-pose selection")
    median = statistics.median(run["minimized_affinity_kcal_mol"] for run in valid)
    return min(valid, key=lambda run: (abs(run["minimized_affinity_kcal_mol"] - median), run["seed"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-timeout-seconds", type=int, default=2700)
    parser.add_argument("--retry-timeouts", action="store_true")
    args = parser.parse_args()
    external = json.loads(EXTERNAL_CONFIG.read_text(encoding="utf-8"))
    docking = json.loads(DOCKING_CONFIG.read_text(encoding="utf-8"))
    pose_config = json.loads(POSE_CONFIG.read_text(encoding="utf-8"))
    preparation = json.loads(PREPARATION.read_text(encoding="utf-8"))
    ligand_manifest = json.loads(LIGANDS.read_text(encoding="utf-8"))
    primary = sorted(
        [row for row in ligand_manifest["entries"] if row["primary_protomer"]],
        key=lambda row: row["candidate_id"],
    )
    if [42, 43, 44] != external["docking"]["production_seeds"] or [42, 43, 44] != pose_config["production_seeds"]:
        raise RuntimeError("Production seed specifications disagree")
    receptor_paths = {
        "inactive_5NM4": ROOT / docking["receptors"]["inactive_5NM4"],
        "active_like_2YDO": ROOT / docking["receptors"]["active_like_2YDO"],
    }
    for path in receptor_paths.values():
        if not path.exists():
            raise FileNotFoundError(path)

    run_root = OUTPUT / "runs"
    results = []
    for ligand_entry in primary:
        ligand = {"chembl_id": ligand_entry["candidate_id"], "path": ligand_entry["path"]}
        receptors = {}
        for receptor_name, receptor_path in receptor_paths.items():
            runs = [
                run_seed(
                    ligand, receptor_name, receptor_path, preparation["shared_box"], docking,
                    run_root, seed, args.job_timeout_seconds, args.retry_timeouts,
                )
                for seed in external["docking"]["production_seeds"]
            ]
            aggregate = aggregate_runs(runs, external["docking"]["minimum_valid_seeds_per_receptor"])
            receptor_id = "5NM4" if receptor_name == "inactive_5NM4" else "2YDO"
            if aggregate["status"] == "valid":
                selected = retained_run(runs)
                source = ROOT / selected["pose_path"]
                destination = OUTPUT / ligand_entry["candidate_id"] / receptor_id / "retained_pose.sdf"
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                aggregate["retained_pose"] = {
                    "seed": selected["seed"],
                    "selection_rule": pose_config["retained_pose_rule"],
                    "cnnscore_soft_flag": selected["cnnscore_flag"],
                    "path": str(destination.relative_to(ROOT)),
                    "sha256": sha256(destination),
                }
            receptors[receptor_id] = aggregate
        results.append({
            "candidate_id": ligand_entry["candidate_id"],
            "functional_label_blinded": True,
            "status": "valid" if all(row["status"] == "valid" for row in receptors.values()) else "failed",
            "receptors": receptors,
        })

    report = {
        "schema_version": 1,
        "created_at": utc_now(),
        "protocol_id": "a2a-external-validation-v1.4",
        "candidate_labels_loaded": False,
        "candidate_count": len(results),
        "valid_candidate_count": sum(row["status"] == "valid" for row in results),
        "failed_candidate_count": sum(row["status"] != "valid" for row in results),
        "source_hashes": {
            "external_config": sha256(EXTERNAL_CONFIG),
            "docking_config": sha256(DOCKING_CONFIG),
            "pose_selection_config": sha256(POSE_CONFIG),
            "ligand_manifest": sha256(LIGANDS),
            "preparation_status": sha256(PREPARATION),
            **{f"receptor_{name}": sha256(path) for name, path in receptor_paths.items()},
        },
        "results": results,
        "next_gate": "Use retained poses for the label-blind MD input manifest; do not unmask functional labels.",
    }
    report_path = OUTPUT / "literature_pilot_2025_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
    if report["failed_candidate_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
