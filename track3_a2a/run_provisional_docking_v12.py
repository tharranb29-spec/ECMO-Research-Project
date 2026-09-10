#!/usr/bin/env python3

"""Run resumable provisional dual-state GNINA docking, smoke mode by default."""

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CONFIG = ROOT / "config" / "docking_provisional.v1.2.json"
PREPARATION = ROOT / "outputs" / "v1.1.1" / "preparation_status.json"
LIGANDS = ROOT / "outputs" / "v1.2" / "ligand_preparation_manifest.json"
GNINA = PROJECT_ROOT / "scripts" / "gnina-docker"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sdf_property(path, name):
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf">\s*<\s*{re.escape(name)}\s*>\s*\r?\n([^\r\n]+)", text, flags=re.I)
    return float(match.group(1).strip()) if match else None


def select_ligands(entries, limit=None):
    primary = [entry for entry in entries if entry["primary_protomer"]]
    primary.sort(key=lambda row: hashlib.sha256(f"smoke-v1.2|{row['chembl_id']}".encode()).hexdigest())
    return primary if limit is None else primary[:limit]


def run_seed(
    ligand,
    receptor_name,
    receptor_path,
    box,
    config,
    output_root,
    seed,
    timeout_seconds,
    retry_timeouts=False,
):
    output_dir = output_root / ligand["chembl_id"] / receptor_name
    output_dir.mkdir(parents=True, exist_ok=True)
    pose = output_dir / f"seed-{seed}.sdf"
    log = output_dir / f"seed-{seed}.log"
    timeout_marker = output_dir / f"seed-{seed}.timeout.json"
    if timeout_marker.exists() and not retry_timeouts:
        timeout_record = json.loads(timeout_marker.read_text(encoding="utf-8"))
        return {
            "seed": seed,
            "status": "timed_out",
            "cached": True,
            "reason": timeout_record["reason"],
            "timeout_seconds": timeout_record["timeout_seconds"],
            "log_path": str(log.relative_to(ROOT)) if log.exists() else None,
        }
    if retry_timeouts:
        timeout_marker.unlink(missing_ok=True)
    if pose.exists() and pose.stat().st_size == 0:
        pose.unlink()
    cached = pose.exists()
    if not cached:
        protocol = config["gnina"]
        container_name = re.sub(
            r"[^a-z0-9_.-]+",
            "-",
            f"gnina-v12-{ligand['chembl_id']}-{receptor_name}-{seed}".lower(),
        )[:63]
        command = [
            str(GNINA), "-r", str(receptor_path.relative_to(PROJECT_ROOT)),
            "-l", str((ROOT / ligand["path"]).relative_to(PROJECT_ROOT)),
            "--center_x", str(box["center"][0]), "--center_y", str(box["center"][1]),
            "--center_z", str(box["center"][2]), "--size_x", str(box["size"][0]),
            "--size_y", str(box["size"][1]), "--size_z", str(box["size"][2]),
            "--seed", str(seed), "--exhaustiveness", str(protocol["exhaustiveness"]),
            "--cnn_scoring", protocol["cnn_scoring"], "--num_modes", str(protocol["num_modes"]),
            "-o", str(pose.relative_to(PROJECT_ROOT)), "--log", str(log.relative_to(PROJECT_ROOT)),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
                env={**os.environ, "GNINA_CONTAINER_NAME": container_name},
            )
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["docker", "stop", "--time", "10", container_name],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            pose.unlink(missing_ok=True)
            timeout_record = {
                "created_at": utc_now(),
                "seed": seed,
                "status": "timed_out",
                "timeout_seconds": timeout_seconds,
                "reason": f"job_exceeded_{timeout_seconds}_seconds",
            }
            timeout_marker.write_text(json.dumps(timeout_record, indent=2) + "\n", encoding="utf-8")
            return {
                "seed": seed,
                "status": "timed_out",
                "cached": False,
                "reason": timeout_record["reason"],
                "timeout_seconds": timeout_seconds,
                "log_path": str(log.relative_to(ROOT)) if log.exists() else None,
            }
        if completed.returncode != 0 or not pose.exists():
            return {"seed": seed, "status": "failed", "cached": False, "reason": (completed.stderr or completed.stdout or "no pose")[-1000:]}
    affinity = sdf_property(pose, "minimizedAffinity")
    cnn_score = sdf_property(pose, "CNNscore")
    cnn_affinity = sdf_property(pose, "CNNaffinity")
    if affinity is None or abs(affinity) < 1e-12:
        return {"seed": seed, "status": "failed", "cached": cached, "reason": "zero_or_missing_empirical_affinity"}
    return {
        "seed": seed,
        "status": "valid",
        "cached": cached,
        "minimized_affinity_kcal_mol": round(affinity, 4),
        "cnn_score": round(cnn_score, 4) if cnn_score is not None else None,
        "cnn_affinity_pk": round(cnn_affinity, 4) if cnn_affinity is not None else None,
        "cnnscore_flag": cnn_score is None or cnn_score <= config["pose_quality"]["cnnscore_flag_threshold"],
        "pose_path": str(pose.relative_to(ROOT)),
        "log_path": str(log.relative_to(ROOT)),
    }


def aggregate_runs(runs, minimum_valid):
    valid = [run for run in runs if run["status"] == "valid"]
    values = [run["minimized_affinity_kcal_mol"] for run in valid]
    cnn_scores = [run["cnn_score"] for run in valid if run["cnn_score"] is not None]
    return {
        "status": "valid" if len(valid) >= minimum_valid else "failed",
        "valid_seed_count": len(valid),
        "failed_seed_count": len(runs) - len(valid),
        "median_affinity_kcal_mol": round(statistics.median(values), 4) if values else None,
        "mean_affinity_kcal_mol": round(statistics.mean(values), 4) if values else None,
        "affinity_sd": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0 if values else None,
        "median_cnn_score": round(statistics.median(cnn_scores), 4) if cnn_scores else None,
        "cnnscore_flagged_seed_count": sum(bool(run.get("cnnscore_flag")) for run in valid),
        "runs": runs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=2, help="Deterministic smoke size; ignored with --full")
    parser.add_argument("--full", action="store_true", help="Run every prepared primary protomer")
    parser.add_argument(
        "--job-timeout-seconds",
        type=int,
        default=2700,
        help="Maximum wall time for one receptor/ligand/seed job (default: 45 minutes)",
    )
    parser.add_argument(
        "--retry-timeouts",
        action="store_true",
        help="Retry jobs previously quarantined by the timeout safeguard",
    )
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    preparation = json.loads(PREPARATION.read_text(encoding="utf-8"))
    ligand_manifest = json.loads(LIGANDS.read_text(encoding="utf-8"))
    limit = None if args.full else args.limit
    selected = select_ligands(ligand_manifest["entries"], limit)
    mode = "full" if args.full else f"smoke-{len(selected)}"
    output_root = ROOT / "outputs" / "v1.2" / f"docking-{mode}"
    receptor_paths = {
        name: ROOT / path
        for name, path in config["receptors"].items()
    }
    minimum_valid = config["aggregation"]["minimum_valid_seeds_per_receptor"]
    molecules = []
    for ligand in selected:
        receptor_results = {}
        for receptor_name, receptor_path in receptor_paths.items():
            runs = [
                run_seed(
                    ligand,
                    receptor_name,
                    receptor_path,
                    preparation["shared_box"],
                    config,
                    output_root,
                    seed,
                    args.job_timeout_seconds,
                    args.retry_timeouts,
                )
                for seed in config["gnina"]["seeds"]
            ]
            receptor_results[receptor_name] = aggregate_runs(runs, minimum_valid)
        valid = all(result["status"] == "valid" for result in receptor_results.values())
        inactive = receptor_results["inactive_5NM4"]["median_affinity_kcal_mol"]
        active = receptor_results["active_like_2YDO"]["median_affinity_kcal_mol"]
        molecules.append({
            "chembl_id": ligand["chembl_id"],
            "status": "valid" if valid else "failed",
            "primary_protomer_sha256": ligand["sha256"],
            "receptors": receptor_results,
            "m_affinity": round((active + inactive) / 2, 4) if valid else None,
            "d_affinity": round(active - inactive, 4) if valid else None,
        })
    report = {
        "schema_version": 1,
        "created_at": utc_now(),
        "protocol_id": config["protocol_id"],
        "mode": mode,
        "job_timeout_seconds": args.job_timeout_seconds,
        "human_validation_claimed": False,
        "molecule_count": len(molecules),
        "valid_molecule_count": sum(row["status"] == "valid" for row in molecules),
        "failed_molecule_count": sum(row["status"] != "valid" for row in molecules),
        "molecules": molecules,
        "next_gate": "inspect smoke diagnostics before authorizing full provisional docking" if not args.full else "build orthogonal feature matrix"
    }
    report_path = output_root / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "molecules"}, indent=2))
    if report["failed_molecule_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
