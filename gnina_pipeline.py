#!/usr/bin/env python3

"""GNINA execution adapter and uncertainty-aware docking aggregation.

The prototype mode exercises the complete dashboard data flow without claiming
that simulated values are scientific results. Real mode requires prepared SDF
and receptor/autobox files and invokes a local Linux GNINA binary.
"""

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
DOCKING_OUTPUTS = OUTPUTS / "docking"


def env_text(name, default=""):
    value = os.environ.get(name)
    return default if value is None else str(value)


def env_int(name, default):
    try:
        return int(env_text(name, str(default)).strip())
    except (TypeError, ValueError):
        return default


def env_float(name, default):
    try:
        return float(env_text(name, str(default)).strip())
    except (TypeError, ValueError):
        return default


GNINA_MODE = env_text("GNINA_MODE", "prototype").strip().lower()
GNINA_BINARY = env_text("GNINA_BINARY", "gnina").strip()
GNINA_VERSION_LABEL = env_text("GNINA_VERSION_LABEL", "1.3.x")
GNINA_RUN_COUNT = max(2, env_int("GNINA_RUN_COUNT", 5))
GNINA_EXHAUSTIVENESS = max(1, env_int("GNINA_EXHAUSTIVENESS", 8))
GNINA_TIMEOUT_SECONDS = max(30, env_int("GNINA_TIMEOUT_SECONDS", 900))
GNINA_CNN_SCORE_MIN = env_float("GNINA_CNN_SCORE_MIN", 0.50)
GNINA_TIE_Z = env_float("GNINA_TIE_Z", 1.96)

SUPPORTED_MODALITIES = {
    "small_molecule",
    "glycomimetic",
    "sialoside",
    "glycan",
    "literature_lead",
}

UNSUPPORTED_MODALITIES = {
    "protein",
    "engineered_protein",
    "antibody",
    "fusion_protein",
    "peptide",
    "glycopolypeptide",
    "glycopolypeptide_control",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def stable_unit_interval(*parts):
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def candidate_dockability(candidate, mode=None):
    selected_mode = (mode or GNINA_MODE).lower()
    modality = str(candidate.get("modality") or candidate.get("modality_guess") or "literature_lead").lower()
    if modality in UNSUPPORTED_MODALITIES:
        return "unsupported_modality", f"{modality} requires peptide or protein docking rather than GNINA."
    if modality not in SUPPORTED_MODALITIES:
        return "review_required", f"Modality '{modality}' has not been approved for the GNINA pipeline."
    if selected_mode == "prototype":
        return "prototype_eligible", "Eligible for a visibly simulated end-to-end workflow demonstration."
    ligand_path = candidate.get("ligand_sdf_path")
    if not ligand_path:
        return "awaiting_structure", "A verified, prepared ligand SDF is required for real GNINA execution."
    if not Path(ligand_path).expanduser().exists():
        return "awaiting_structure", "The configured ligand SDF path does not exist."
    return "dockable", "Prepared ligand structure is available."


def prototype_runs(candidate, run_count=GNINA_RUN_COUNT):
    """Create deterministic demo values that can never be mistaken for GNINA output."""
    candidate_id = candidate.get("id") or candidate.get("candidate_name") or "candidate"
    target = candidate.get("target_receptor") or "unknown"
    chemistry_signal = stable_unit_interval(candidate_id, target, "chemistry")
    base_affinity = -5.8 - (3.4 * chemistry_signal)
    base_cnnscore = 0.48 + (0.45 * stable_unit_interval(candidate_id, target, "pose"))
    base_cnnaffinity = 4.8 + (2.5 * stable_unit_interval(candidate_id, target, "pK"))
    runs = []
    for seed in range(1, run_count + 1):
        affinity_jitter = (stable_unit_interval(candidate_id, seed, "affinity") - 0.5) * 0.34
        score_jitter = (stable_unit_interval(candidate_id, seed, "score") - 0.5) * 0.08
        pk_jitter = (stable_unit_interval(candidate_id, seed, "pk") - 0.5) * 0.24
        runs.append(
            {
                "seed": seed,
                "minimized_affinity_kcal_mol": round(base_affinity + affinity_jitter, 3),
                "cnn_score": round(max(0.01, min(0.99, base_cnnscore + score_jitter)), 4),
                "cnn_affinity_pk": round(max(0.1, base_cnnaffinity + pk_jitter), 3),
                "pose_path": None,
                "execution_mode": "prototype",
                "simulated": True,
            }
        )
    return runs


def parse_gnina_sdf_properties(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")

    def property_value(*names):
        for name in names:
            match = re.search(rf">\s*<\s*{re.escape(name)}\s*>\s*\r?\n([^\r\n]+)", text, flags=re.I)
            if match:
                try:
                    return float(match.group(1).strip())
                except ValueError:
                    continue
        return None

    affinity = property_value("minimizedAffinity", "affinity")
    cnn_score = property_value("CNNscore")
    cnn_affinity = property_value("CNNaffinity")
    if affinity is None or cnn_score is None:
        raise ValueError("GNINA output is missing minimizedAffinity/affinity or CNNscore properties.")
    return {
        "minimized_affinity_kcal_mol": affinity,
        "cnn_score": cnn_score,
        "cnn_affinity_pk": cnn_affinity,
    }


def target_protocol(candidate):
    target_key = re.sub(r"[^A-Z0-9]+", "_", str(candidate.get("target_receptor") or "").upper()).strip("_")
    receptor = env_text(f"GNINA_RECEPTOR_{target_key}")
    autobox = env_text(f"GNINA_AUTOBOX_{target_key}")
    return receptor, autobox


def real_gnina_runs(candidate, run_count=GNINA_RUN_COUNT):
    receptor, autobox = target_protocol(candidate)
    ligand = str(Path(candidate["ligand_sdf_path"]).expanduser().resolve())
    if not receptor or not Path(receptor).expanduser().exists():
        raise ValueError(f"No prepared receptor is configured for {candidate.get('target_receptor')}.")
    if not autobox or not Path(autobox).expanduser().exists():
        raise ValueError(f"No autobox reference ligand is configured for {candidate.get('target_receptor')}.")

    candidate_slug = re.sub(r"[^a-z0-9]+", "-", str(candidate.get("id") or candidate.get("candidate_name") or "candidate").lower()).strip("-")
    candidate_dir = DOCKING_OUTPUTS / candidate_slug
    candidate_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    for seed in range(1, run_count + 1):
        output_path = candidate_dir / f"seed-{seed}.sdf"
        command = [
            GNINA_BINARY,
            "-r",
            str(Path(receptor).expanduser().resolve()),
            "-l",
            ligand,
            "--autobox_ligand",
            str(Path(autobox).expanduser().resolve()),
            "--seed",
            str(seed),
            "--exhaustiveness",
            str(GNINA_EXHAUSTIVENESS),
            "--cnn_scoring",
            "rescore",
            "-o",
            str(output_path),
        ]
        completed = subprocess.run(
            command,
            cwd=str(candidate_dir),
            capture_output=True,
            text=True,
            timeout=GNINA_TIMEOUT_SECONDS,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "GNINA failed").strip()[-800:]
            raise RuntimeError(f"GNINA seed {seed} failed: {detail}")
        metrics = parse_gnina_sdf_properties(output_path)
        runs.append(
            {
                "seed": seed,
                **metrics,
                "pose_path": str(output_path.relative_to(ROOT)),
                "execution_mode": "local",
                "simulated": False,
            }
        )
    return runs


def mean_sd(values):
    values = [float(value) for value in values if value is not None]
    if not values:
        return None, None
    return statistics.mean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def aggregate_candidate(candidate, runs, mode):
    affinity_mean, affinity_sd = mean_sd([run.get("minimized_affinity_kcal_mol") for run in runs])
    cnn_score_mean, cnn_score_sd = mean_sd([run.get("cnn_score") for run in runs])
    cnn_affinity_mean, cnn_affinity_sd = mean_sd([run.get("cnn_affinity_pk") for run in runs])
    pose_pass = cnn_score_mean is not None and cnn_score_mean >= GNINA_CNN_SCORE_MIN
    return {
        "candidate_id": candidate.get("id"),
        "candidate_name": candidate.get("candidate_name"),
        "target_receptor": candidate.get("target_receptor"),
        "modality": candidate.get("modality") or candidate.get("modality_guess"),
        "source_batch": candidate.get("source_batch") or candidate.get("article_id") or "autonomous-current",
        "execution_mode": mode,
        "simulated": mode == "prototype",
        "run_count": len(runs),
        "minimized_affinity_mean_kcal_mol": round(affinity_mean, 3) if affinity_mean is not None else None,
        "minimized_affinity_sd_kcal_mol": round(affinity_sd, 3) if affinity_sd is not None else None,
        "cnn_score_mean": round(cnn_score_mean, 4) if cnn_score_mean is not None else None,
        "cnn_score_sd": round(cnn_score_sd, 4) if cnn_score_sd is not None else None,
        "cnn_affinity_mean_pk": round(cnn_affinity_mean, 3) if cnn_affinity_mean is not None else None,
        "cnn_affinity_sd_pk": round(cnn_affinity_sd, 3) if cnn_affinity_sd is not None else None,
        "pose_quality_status": "pass" if pose_pass else "review",
        "pose_quality_threshold": GNINA_CNN_SCORE_MIN,
        "runs": runs,
        "functional_direction": candidate.get("functional_direction") or "unknown",
        "structure_status": candidate.get("structure_status") or ("prototype_unverified" if mode == "prototype" else "prepared"),
    }


def standard_error_difference(first, second):
    n_first = max(1, int(first.get("run_count") or 1))
    n_second = max(1, int(second.get("run_count") or 1))
    sd_first = float(first.get("minimized_affinity_sd_kcal_mol") or 0.0)
    sd_second = float(second.get("minimized_affinity_sd_kcal_mol") or 0.0)
    return math.sqrt((sd_first**2 / n_first) + (sd_second**2 / n_second))


def assign_uncertainty_ranks(results):
    by_target = {}
    for result in results:
        if result.get("status") != "completed" or result.get("pose_quality_status") != "pass":
            continue
        by_target.setdefault(result.get("target_receptor") or "Unknown", []).append(result)

    for target_results in by_target.values():
        target_results.sort(
            key=lambda item: (
                float(item.get("minimized_affinity_mean_kcal_mol") or 999),
                -float(item.get("cnn_score_mean") or 0),
            )
        )
        group = 1
        previous = None
        for index, result in enumerate(target_results, start=1):
            tied = False
            if previous is not None:
                difference = abs(
                    float(result["minimized_affinity_mean_kcal_mol"])
                    - float(previous["minimized_affinity_mean_kcal_mol"])
                )
                threshold = GNINA_TIE_Z * standard_error_difference(previous, result)
                tied = difference <= threshold if threshold > 0 else difference == 0
                if not tied:
                    group += 1
            result["gnina_rank"] = index
            result["uncertainty_group"] = group
            result["tied_with_previous"] = tied
            previous = result


def run_docking_pipeline(candidates, mode=None, run_count=None, persist=True):
    selected_mode = (mode or GNINA_MODE).lower()
    if selected_mode not in {"prototype", "local", "disabled"}:
        selected_mode = "disabled"
    selected_run_count = max(2, int(run_count or GNINA_RUN_COUNT))
    started_at = utc_now()
    results = []

    for candidate in candidates:
        dockability, reason = candidate_dockability(candidate, selected_mode)
        base = {
            "candidate_id": candidate.get("id"),
            "candidate_name": candidate.get("candidate_name"),
            "target_receptor": candidate.get("target_receptor"),
            "modality": candidate.get("modality") or candidate.get("modality_guess"),
            "dockability": dockability,
            "dockability_reason": reason,
        }
        if selected_mode == "disabled":
            results.append({**base, "status": "disabled", "simulated": False})
            continue
        if dockability not in {"prototype_eligible", "dockable"}:
            results.append({**base, "status": dockability, "simulated": False})
            continue
        try:
            runs = prototype_runs(candidate, selected_run_count) if selected_mode == "prototype" else real_gnina_runs(candidate, selected_run_count)
            results.append({**base, **aggregate_candidate(candidate, runs, selected_mode), "status": "completed"})
        except Exception as exc:  # noqa: BLE001
            results.append({**base, "status": "error", "simulated": selected_mode == "prototype", "error": str(exc)})

    assign_uncertainty_ranks(results)
    completed = [result for result in results if result.get("status") == "completed"]
    status_counts = {}
    for result in results:
        status_counts[result.get("status", "unknown")] = status_counts.get(result.get("status", "unknown"), 0) + 1

    validation_payload = read_json(OUTPUTS / "gnina_validation.json", {}) or {}
    target_validation_ready = bool(validation_payload.get("dashboard_real_ranking_ready"))
    payload = {
        "last_updated": utc_now(),
        "started_at": started_at,
        "mode": selected_mode,
        "simulated": selected_mode == "prototype",
        "scientific_status": (
            "workflow_demonstration_only"
            if selected_mode == "prototype"
            else "computational_prediction_validated_target"
            if target_validation_ready
            else "computational_prediction_unvalidated_target"
        ),
        "target_validation_ready": target_validation_ready,
        "validation_status": validation_payload.get("overall_status") or "not_run",
        "candidate_count": len(candidates),
        "completed_count": len(completed),
        "status_counts": status_counts,
        "protocol": {
            "gnina_version": GNINA_VERSION_LABEL,
            "run_count": selected_run_count,
            "cnn_scoring": "rescore",
            "cnn_score_min": GNINA_CNN_SCORE_MIN,
            "tie_z": GNINA_TIE_Z,
            "exhaustiveness": GNINA_EXHAUSTIVENESS,
            "ranking_rule": "pose-quality gate, then mean minimized affinity; CNNscore breaks unresolved ties",
        },
        "results": results,
    }
    if persist:
        write_json(OUTPUTS / "gnina_results.json", payload)
        write_json(
            OUTPUTS / "gnina_status.json",
            {
                key: payload[key]
                for key in [
                    "last_updated",
                    "started_at",
                    "mode",
                    "simulated",
                    "scientific_status",
                    "target_validation_ready",
                    "validation_status",
                    "candidate_count",
                    "completed_count",
                    "status_counts",
                    "protocol",
                ]
            },
        )
    return payload


def attach_docking_evidence(ranking_payload, docking_payload):
    ranking_payload = ranking_payload if isinstance(ranking_payload, dict) else {"models": {}, "metrics": {}, "ranked": []}
    result_index = {
        result.get("candidate_id"): result
        for result in docking_payload.get("results", [])
        if result.get("candidate_id")
    }
    for row in ranking_payload.get("ranked", []):
        row["translational_suitability_score"] = row.get("predicted_score")
        evidence = result_index.get(row.get("id"))
        if evidence:
            row["gnina"] = evidence
            row["gnina_rank"] = evidence.get("gnina_rank")
            if evidence.get("status") == "completed":
                row["ranking_basis"] = "gnina_b2_prototype" if evidence.get("simulated") else "gnina_b2"
            else:
                row["ranking_basis"] = "gnina_not_scored"
        else:
            row["ranking_basis"] = "translational_suitability_only"

    def ranking_key(row):
        evidence = row.get("gnina") or {}
        completed = evidence.get("status") == "completed" and evidence.get("pose_quality_status") == "pass"
        return (
            row.get("target_receptor") or "",
            0 if completed else 1,
            int(evidence.get("uncertainty_group") or 9999),
            -float(evidence.get("cnn_score_mean") or 0),
            -float(row.get("translational_suitability_score") or 0),
        )

    ranking_payload["ranked"].sort(key=ranking_key)
    ranking_payload["docking_summary"] = {
        "last_updated": docking_payload.get("last_updated"),
        "mode": docking_payload.get("mode"),
        "simulated": docking_payload.get("simulated"),
        "completed_count": docking_payload.get("completed_count"),
        "candidate_count": docking_payload.get("candidate_count"),
        "protocol": docking_payload.get("protocol"),
    }
    return ranking_payload


def refresh_existing_outputs(mode=None):
    candidates_payload = read_json(OUTPUTS / "autonomous_candidates.json", {}) or {}
    candidates = candidates_payload.get("candidates", []) if isinstance(candidates_payload, dict) else []
    docking_payload = run_docking_pipeline(candidates, mode=mode)
    ranking_payload = read_json(OUTPUTS / "autonomous_ranking_results.json", {}) or {"models": {}, "metrics": {}, "ranked": []}
    ranking_payload = attach_docking_evidence(ranking_payload, docking_payload)
    write_json(OUTPUTS / "autonomous_ranking_results.json", ranking_payload)

    # Keep the main review board synchronized after a docking-only rerun.
    promoted_path = OUTPUTS / "autonomous_promoted_results.json"
    promoted_payload = read_json(promoted_path, {}) or {}
    ranked_index = {
        row.get("id"): row
        for row in ranking_payload.get("ranked", [])
        if row.get("id")
    }
    refreshed_promoted = []
    for previous in promoted_payload.get("ranked", []):
        current = ranked_index.get(previous.get("id"))
        if not current:
            continue
        merged = dict(current)
        for key in ["promoted_to_main_view", "promotion_source", "promotion_reason", "promotion_rank"]:
            if key in previous:
                merged[key] = previous[key]
        refreshed_promoted.append(merged)
    if promoted_payload:
        promoted_payload["last_updated"] = utc_now()
        promoted_payload["ranked"] = refreshed_promoted
        write_json(promoted_path, promoted_payload)
    return docking_payload


def main():
    parser = argparse.ArgumentParser(description="Run the ECMO GNINA docking evidence pipeline.")
    parser.add_argument("--mode", choices=["prototype", "local", "disabled"], default=None)
    parser.add_argument("--from-existing", action="store_true", help="Process outputs/autonomous_candidates.json.")
    args = parser.parse_args()
    payload = refresh_existing_outputs(mode=args.mode)
    print(json.dumps({key: payload.get(key) for key in ["mode", "simulated", "candidate_count", "completed_count", "status_counts"]}, indent=2))


if __name__ == "__main__":
    main()
