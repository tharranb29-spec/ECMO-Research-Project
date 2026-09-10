#!/usr/bin/env python3

"""Run the pre-registered five-seed A2A cognate-redocking gate."""

import json
import re
import statistics
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "config" / "protocol.json"
STATUS_PATH = ROOT / "outputs" / "preparation_status.json"
REPORT_PATH = ROOT / "outputs" / "redocking_report.json"
GNINA = PROJECT_ROOT / "scripts" / "gnina-docker"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sdf_property(path, name):
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf">\s*<\s*{re.escape(name)}\s*>\s*\r?\n([^\r\n]+)", text, flags=re.I)
    return float(match.group(1).strip()) if match else None


def rmsd(reference, pose):
    command = [
        "docker", "run", "--rm", "--platform", "linux/amd64",
        "--volume", f"{PROJECT_ROOT}:/data", "--workdir", "/data",
        "--entrypoint", "/usr/local/bin/obrms", "gnina/gnina:v1.3.3", "-m",
        str(reference.relative_to(PROJECT_ROOT)), str(pose.relative_to(PROJECT_ROOT)),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "obrms failed").strip())
    match = re.search(r"RMSD\s+\S+\s+([0-9.]+)", completed.stdout)
    if not match:
        raise RuntimeError(f"Could not parse RMSD output: {completed.stdout.strip()}")
    return float(match.group(1))


def run_case(case_id, receptor, ligand, box, config):
    protocol = config["gnina"]
    output_dir = ROOT / "outputs" / "redocking" / case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    for seed in protocol["seeds"]:
        pose = output_dir / f"seed-{seed}.sdf"
        log = output_dir / f"seed-{seed}.log"
        command = [
            str(GNINA), "-r", str(receptor.relative_to(PROJECT_ROOT)),
            "-l", str(ligand.relative_to(PROJECT_ROOT)),
            "--center_x", str(box["center"][0]), "--center_y", str(box["center"][1]),
            "--center_z", str(box["center"][2]), "--size_x", str(box["size"][0]),
            "--size_y", str(box["size"][1]), "--size_z", str(box["size"][2]),
            "--seed", str(seed), "--exhaustiveness", str(protocol["exhaustiveness"]),
            "--cnn_scoring", protocol["cnn_scoring"], "--num_modes", str(protocol["num_modes"]),
            "-o", str(pose.relative_to(PROJECT_ROOT)), "--log", str(log.relative_to(PROJECT_ROOT)),
        ]
        completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
        if completed.returncode != 0 or not pose.exists():
            runs.append({
                "seed": seed,
                "status": "failed",
                "reason": (completed.stderr or completed.stdout or "GNINA produced no pose").strip()[-1000:],
            })
            continue
        affinity = sdf_property(pose, "minimizedAffinity")
        cnnscore = sdf_property(pose, "CNNscore")
        cnnaffinity = sdf_property(pose, "CNNaffinity")
        if affinity is None or abs(affinity) < 1e-12:
            runs.append({"seed": seed, "status": "failed", "reason": "zero_or_missing_empirical_affinity"})
            continue
        pose_rmsd = rmsd(ligand, pose)
        runs.append({
            "seed": seed,
            "status": "valid",
            "rmsd_angstrom": round(pose_rmsd, 4),
            "minimized_affinity_kcal_mol": round(affinity, 4),
            "cnn_score": round(cnnscore, 4) if cnnscore is not None else None,
            "cnn_affinity_pk": round(cnnaffinity, 4) if cnnaffinity is not None else None,
            "pose_path": str(pose.relative_to(ROOT)),
            "log_path": str(log.relative_to(ROOT)),
        })

    valid = [run for run in runs if run["status"] == "valid"]
    rmsds = [run["rmsd_angstrom"] for run in valid]
    gate = config["redocking_gate"]
    threshold = gate["rmsd_threshold_angstrom"]
    pass_count = sum(value <= threshold for value in rmsds)
    median_rmsd = statistics.median(rmsds) if rmsds else None
    gate_passed = (
        pass_count >= gate["minimum_passing_seeds"]
        and median_rmsd is not None
        and (not gate["median_rmsd_must_pass"] or median_rmsd <= threshold)
    )
    return {
        "case_id": case_id,
        "status": "pass" if gate_passed else "fail",
        "valid_run_count": len(valid),
        "failed_run_count": len(runs) - len(valid),
        "passing_pose_count": pass_count,
        "median_rmsd_angstrom": round(median_rmsd, 4) if median_rmsd is not None else None,
        "mean_rmsd_angstrom": round(statistics.mean(rmsds), 4) if rmsds else None,
        "runs": runs,
    }


def main():
    config = read_json(CONFIG_PATH)
    status = read_json(STATUS_PATH)
    if not status.get("source_checksums_verified") or not status["shared_box"].get("aligned_adenosine_inside"):
        raise SystemExit("Source/alignment gate is not ready.")
    box = status["shared_box"]
    cases = [
        run_case(
            "4EIY",
            ROOT / "docking_inputs" / "receptors" / "4EIY_inactive_ph7.4.pdb",
            ROOT / "docking_inputs" / "ligands" / "4EIY_ZMA_crystal.sdf",
            box,
            config,
        ),
        run_case(
            "2YDO",
            ROOT / "docking_inputs" / "receptors" / "2YDO_active_like_ph7.4.pdb",
            ROOT / "docking_inputs" / "ligands" / "2YDO_ADN_crystal_aligned.sdf",
            box,
            config,
        ),
    ]
    gate_passed = all(case["status"] == "pass" for case in cases)
    report = {
        "protocol_id": config["protocol_id"],
        "gate": "cognate_redocking",
        "status": "pass" if gate_passed else "fail",
        "production_screening_unlocked": False,
        "interpretation": "Pose-recovery validation only; no biological efficacy or affinity claim.",
        "acceptance_rule": config["redocking_gate"],
        "cases": cases,
        "next_gate": "curate and audit functional-label benchmark" if gate_passed else "review receptor preparation and docking setup",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    status["stage"] = "redocking_gate_passed" if gate_passed else "redocking_gate_failed"
    status["redocking_gate_passed"] = gate_passed
    status["production_screening_unlocked"] = False
    status["receptor_preparation"] = {
        "tool": "PDB2PQR",
        "version": "3.6.2",
        "force_field": "AMBER",
        "ph": 7.4,
        "hydrogen_bond_optimization": True,
        "gnina_prepare_receptor_supported": False,
    }
    status["next_gate"] = report["next_gate"]
    STATUS_PATH.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

