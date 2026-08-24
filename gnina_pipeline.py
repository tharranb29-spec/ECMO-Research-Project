#!/usr/bin/env python3

"""GNINA execution adapter and uncertainty-aware docking aggregation.

The prototype mode exercises the complete dashboard data flow without claiming
that simulated values are scientific results. Real mode requires prepared SDF
and receptor/autobox files and invokes a local Linux GNINA binary.
"""

import argparse
import hashlib
import itertools
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
GNINA_SEED_BASE = env_int("GNINA_SEED_BASE", 42)

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


def resolve_project_path(value):
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else ROOT / path


def candidate_dockability(candidate, mode=None):
    selected_mode = (mode or GNINA_MODE).lower()
    modality = str(candidate.get("modality") or candidate.get("modality_guess") or "literature_lead").lower()
    if candidate.get("approved_for_docking") is False:
        return "review_required", "Candidate is not approved for real docking in the batch manifest."
    if modality in UNSUPPORTED_MODALITIES:
        return "unsupported_modality", f"{modality} requires peptide or protein docking rather than GNINA."
    if modality not in SUPPORTED_MODALITIES:
        return "review_required", f"Modality '{modality}' has not been approved for the GNINA pipeline."
    if selected_mode == "prototype":
        return "prototype_eligible", "Eligible for a visibly simulated end-to-end workflow demonstration."
    ligand_path = candidate.get("ligand_sdf_path")
    if not ligand_path:
        return "awaiting_structure", "A verified, prepared ligand SDF is required for real GNINA execution."
    if not resolve_project_path(ligand_path).exists():
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
    for seed in range(GNINA_SEED_BASE, GNINA_SEED_BASE + run_count):
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
    receptor = candidate.get("receptor_path") or env_text(f"GNINA_RECEPTOR_{target_key}")
    autobox = candidate.get("autobox_ligand_path") or env_text(f"GNINA_AUTOBOX_{target_key}")
    box_center = candidate.get("box_center")
    box_size = candidate.get("box_size")
    return receptor, autobox, box_center, box_size


def real_gnina_runs(candidate, run_count=GNINA_RUN_COUNT):
    receptor, autobox, box_center, box_size = target_protocol(candidate)
    ligand = str(resolve_project_path(candidate["ligand_sdf_path"]).resolve())
    receptor_path = resolve_project_path(receptor) if receptor else None
    autobox_path = resolve_project_path(autobox) if autobox and "REPLACE_" not in str(autobox) else None
    if not receptor_path or not receptor_path.exists():
        raise ValueError(f"No prepared receptor is configured for {candidate.get('target_receptor')}.")
    has_explicit_box = (
        isinstance(box_center, (list, tuple))
        and len(box_center) == 3
        and isinstance(box_size, (int, float, list, tuple))
    )
    if not autobox_path and not has_explicit_box:
        raise ValueError(f"No validated autobox ligand or explicit binding box is configured for {candidate.get('target_receptor')}.")
    if autobox_path and not autobox_path.exists():
        raise ValueError(f"The configured autobox reference ligand does not exist for {candidate.get('target_receptor')}.")

    candidate_slug = re.sub(r"[^a-z0-9]+", "-", str(candidate.get("id") or candidate.get("candidate_name") or "candidate").lower()).strip("-")
    candidate_dir = DOCKING_OUTPUTS / candidate_slug
    candidate_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    for seed in range(GNINA_SEED_BASE, GNINA_SEED_BASE + run_count):
        output_path = candidate_dir / f"seed-{seed}.sdf"
        binary = GNINA_BINARY
        if os.sep in binary and not Path(binary).is_absolute():
            binary = str((ROOT / binary).resolve())
        command = [
            binary,
            "-r",
            str(receptor_path.resolve()),
            "-l",
            ligand,
        ]
        if autobox_path:
            command.extend(["--autobox_ligand", str(autobox_path.resolve())])
        else:
            sizes = list(box_size) if isinstance(box_size, (list, tuple)) else [box_size] * 3
            command.extend([
                "--center_x", str(float(box_center[0])),
                "--center_y", str(float(box_center[1])),
                "--center_z", str(float(box_center[2])),
                "--size_x", str(float(sizes[0])),
                "--size_y", str(float(sizes[1])),
                "--size_z", str(float(sizes[2])),
            ])
        command.extend([
            "--seed",
            str(seed),
            "--exhaustiveness",
            str(GNINA_EXHAUSTIVENESS),
            "--cnn_scoring",
            "rescore",
            "--num_modes",
            "1",
            "-o",
            str(output_path),
        ])
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


KD_UNIT_TO_MOLAR = {"m": 1.0, "mm": 1e-3, "um": 1e-6, "µm": 1e-6, "nm": 1e-9, "pm": 1e-12}


def experimental_pkd(candidate):
    """Return pKd from an explicitly unit-labelled experimental value."""
    direct = candidate.get("experimental_pkd")
    if direct is not None:
        try:
            return float(direct)
        except (TypeError, ValueError):
            return None
    value = candidate.get("experimental_kd_value")
    unit = str(candidate.get("experimental_kd_unit") or "").strip().lower().replace("μ", "µ")
    try:
        kd_molar = float(value) * KD_UNIT_TO_MOLAR[unit]
    except (TypeError, ValueError, KeyError):
        return None
    return -math.log10(kd_molar) if kd_molar > 0 else None


def tied_ranks(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        average_rank = ((cursor + 1) + end) / 2.0
        for position in range(cursor, end):
            ranks[order[position]] = average_rank
        cursor = end
    return ranks


def pearson(values_x, values_y):
    mean_x = statistics.mean(values_x)
    mean_y = statistics.mean(values_y)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(values_x, values_y))
    denominator = math.sqrt(sum((x - mean_x) ** 2 for x in values_x) * sum((y - mean_y) ** 2 for y in values_y))
    return numerator / denominator if denominator else None


def spearman_with_exact_p(values_x, values_y):
    if len(values_x) < 3 or len(values_x) != len(values_y):
        return None, None
    ranks_x = tied_ranks(values_x)
    ranks_y = tied_ranks(values_y)
    rho = pearson(ranks_x, ranks_y)
    if rho is None:
        return None, None
    p_value = None
    if len(values_x) <= 8:
        extreme = 0
        total = 0
        for permuted in itertools.permutations(ranks_y):
            permuted_rho = pearson(ranks_x, permuted)
            if permuted_rho is not None and abs(permuted_rho) >= abs(rho) - 1e-12:
                extreme += 1
            total += 1
        p_value = extreme / total if total else None
    return rho, p_value


def build_experimental_validation(candidates, results):
    candidate_index = {candidate.get("id"): candidate for candidate in candidates if candidate.get("id")}
    pairs = []
    for result in results:
        if result.get("status") != "completed" or result.get("simulated"):
            continue
        candidate = candidate_index.get(result.get("candidate_id"), {})
        pkd = experimental_pkd(candidate)
        if pkd is None:
            continue
        pairs.append({
            "candidate_id": result.get("candidate_id"),
            "candidate_name": result.get("candidate_name"),
            "experimental_pkd": round(pkd, 4),
            "experimental_kd_value": candidate.get("experimental_kd_value"),
            "experimental_kd_unit": candidate.get("experimental_kd_unit"),
            "minimized_affinity_kcal_mol": result.get("minimized_affinity_mean_kcal_mol"),
            "cnn_score": result.get("cnn_score_mean"),
            "cnn_affinity_pk": result.get("cnn_affinity_mean_pk"),
            "experimental_source": candidate.get("experimental_source"),
        })

    metric_specs = [
        ("negated_minimized_affinity", "-minimized affinity vs pKd", "minimized_affinity_kcal_mol", -1.0),
        ("cnn_affinity", "CNNaffinity vs pKd", "cnn_affinity_pk", 1.0),
        ("cnn_score", "CNNscore vs pKd (diagnostic only)", "cnn_score", 1.0),
    ]
    correlations = []
    for metric_id, label, field, multiplier in metric_specs:
        matched = [pair for pair in pairs if pair.get(field) is not None]
        rho, p_value = spearman_with_exact_p(
            [float(pair[field]) * multiplier for pair in matched],
            [float(pair["experimental_pkd"]) for pair in matched],
        )
        correlations.append({
            "metric": metric_id,
            "label": label,
            "n": len(matched),
            "spearman_rho": round(rho, 4) if rho is not None else None,
            "exact_two_sided_p": round(p_value, 6) if p_value is not None else None,
        })
    return {
        "status": "exploratory_complete" if len(pairs) >= 3 else "awaiting_matched_experimental_data",
        "matched_candidate_count": len(pairs),
        "minimum_for_correlation": 3,
        "pairs": pairs,
        "correlations": correlations,
        "interpretation": "Exploratory rank validation only; five compounds are insufficient for a general performance claim.",
    }


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
        "structure_provenance": candidate.get("structure_provenance"),
        "structure_source_url": candidate.get("structure_source_url"),
        "structure_sha256": candidate.get("structure_sha256"),
        "candidate_role": candidate.get("candidate_role"),
    }


def standard_error_difference(first, second):
    n_first = max(1, int(first.get("run_count") or 1))
    n_second = max(1, int(second.get("run_count") or 1))
    sd_first = float(first.get("minimized_affinity_sd_kcal_mol") or 0.0)
    sd_second = float(second.get("minimized_affinity_sd_kcal_mol") or 0.0)
    return math.sqrt((sd_first**2 / n_first) + (sd_second**2 / n_second))


def assign_uncertainty_ranks(results):
    # Preserve a transparent raw-score ordering even when the pose-quality gate
    # blocks candidates from receiving a target-specific GNINA rank.
    comparative_by_target = {}
    for result in results:
        if result.get("status") != "completed":
            continue
        comparative_by_target.setdefault(result.get("target_receptor") or "Unknown", []).append(result)
    for target_results in comparative_by_target.values():
        target_results.sort(
            key=lambda item: (
                float(item.get("minimized_affinity_mean_kcal_mol") or 999),
                -float(item.get("cnn_score_mean") or 0),
            )
        )
        for index, result in enumerate(target_results, start=1):
            result["comparative_affinity_rank"] = index

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
        "experimental_validation": build_experimental_validation(candidates, results),
        "protocol": {
            "gnina_version": GNINA_VERSION_LABEL,
            "run_count": selected_run_count,
            "seed_start": GNINA_SEED_BASE,
            "num_modes": 1,
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
                    "experimental_validation",
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


def load_batch_manifest(path):
    manifest_path = resolve_project_path(path)
    payload = read_json(manifest_path, {}) or {}
    receptor = payload.get("receptor") or {}
    candidates = payload.get("candidates") or []
    if not isinstance(candidates, list):
        raise ValueError("Batch manifest candidates must be a list.")
    prepared = []
    for candidate in candidates:
        row = dict(candidate)
        row.setdefault("target_receptor", receptor.get("target"))
        row.setdefault("receptor_path", receptor.get("prepared_path"))
        row.setdefault("autobox_ligand_path", receptor.get("autobox_reference_ligand_path"))
        row.setdefault("box_center", receptor.get("box_center"))
        row.setdefault("box_size", receptor.get("box_size"))
        prepared.append(row)
    return prepared


def main():
    parser = argparse.ArgumentParser(description="Run the ECMO GNINA docking evidence pipeline.")
    parser.add_argument("--mode", choices=["prototype", "local", "disabled"], default=None)
    parser.add_argument("--from-existing", action="store_true", help="Process outputs/autonomous_candidates.json.")
    parser.add_argument("--manifest", help="Process a reviewed five-ligand batch manifest.")
    args = parser.parse_args()
    if args.manifest:
        payload = run_docking_pipeline(load_batch_manifest(args.manifest), mode=args.mode, persist=False)
        write_json(OUTPUTS / "gnina_bridge_results.json", payload)
    else:
        payload = refresh_existing_outputs(mode=args.mode)
    print(json.dumps({key: payload.get(key) for key in ["mode", "simulated", "candidate_count", "completed_count", "status_counts"]}, indent=2))


if __name__ == "__main__":
    main()
