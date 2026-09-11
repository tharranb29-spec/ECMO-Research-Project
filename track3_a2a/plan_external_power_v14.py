#!/usr/bin/env python3

"""Run the frozen simulation-based sample-size analysis for v1.4."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "external_power.v1.4.json"
OUTPUT = ROOT / "outputs" / "v1.4" / "external_power_analysis.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expit(values: np.ndarray) -> np.ndarray:
    values = np.clip(values, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-values))


def intercept_for_prevalence(linear_predictor: np.ndarray, prevalence: float) -> float:
    low, high = -30.0, 30.0
    for _ in range(100):
        midpoint = (low + high) / 2.0
        if float(expit(midpoint + linear_predictor).mean()) < prevalence:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def fit_logistic_wald(design: np.ndarray, labels: np.ndarray) -> tuple[float, float] | None:
    """Return the final coefficient and its one-sided Wald p-value."""
    augmented = np.column_stack([np.ones(len(design)), design])
    coefficients = np.zeros(augmented.shape[1], dtype=float)
    converged = False
    for _ in range(80):
        probabilities = expit(augmented @ coefficients)
        weights = np.clip(probabilities * (1.0 - probabilities), 1e-10, None)
        information = augmented.T @ (augmented * weights[:, None])
        score = augmented.T @ (labels - probabilities)
        try:
            step = np.linalg.solve(information, score)
        except np.linalg.LinAlgError:
            return None
        coefficients += step
        if not np.all(np.isfinite(coefficients)) or np.max(np.abs(coefficients)) > 50:
            return None
        if np.max(np.abs(step)) < 1e-8:
            converged = True
            break
    if not converged:
        return None
    probabilities = expit(augmented @ coefficients)
    weights = np.clip(probabilities * (1.0 - probabilities), 1e-10, None)
    information = augmented.T @ (augmented * weights[:, None])
    try:
        variance = np.linalg.inv(information)[-1, -1]
    except np.linalg.LinAlgError:
        return None
    if not np.isfinite(variance) or variance <= 0:
        return None
    standard_error = math.sqrt(float(variance))
    z_score = float(coefficients[-1] / standard_error)
    one_sided_p = 0.5 * math.erfc(z_score / math.sqrt(2.0))
    return float(coefficients[-1]), one_sided_p


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> dict:
    estimate = successes / trials
    denominator = 1.0 + z * z / trials
    center = (estimate + z * z / (2.0 * trials)) / denominator
    margin = z * math.sqrt(estimate * (1.0 - estimate) / trials + z * z / (4.0 * trials * trials)) / denominator
    return {"estimate": estimate, "lower": center - margin, "upper": center + margin}


def empirical_design(config: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    feature_path = ROOT / config["historical_feature_matrix"]
    with feature_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    chemistry = np.asarray(
        [[float(row[column]) for column in config["chemistry_descriptors"]] for row in rows],
        dtype=float,
    )
    chemistry_scaled = StandardScaler().fit_transform(chemistry)
    pca = PCA(n_components=config["chemistry_pca_components"]).fit(chemistry_scaled)
    pcs = pca.transform(chemistry_scaled)
    signals = np.asarray(
        [[float(row[column]) for column in config["signals"]] for row in rows], dtype=float
    )
    design = StandardScaler().fit_transform(np.column_stack([pcs, signals]))
    labels = np.asarray([int(row["binary_label"]) for row in rows], dtype=int)
    nuisance_model = LogisticRegression(penalty=None, solver="lbfgs", max_iter=10000)
    nuisance_model.fit(design[:, :-1], labels)
    metadata = {
        "historical_row_count": len(rows),
        "historical_positive_fraction": float(labels.mean()),
        "chemistry_pca_variance_explained": float(pca.explained_variance_ratio_.sum()),
        "standardized_nuisance_coefficients": nuisance_model.coef_[0].tolist(),
    }
    return design, nuisance_model.coef_[0], metadata


def simulate_scenario(
    design: np.ndarray,
    nuisance_coefficients: np.ndarray,
    effect: float,
    sample_size: int,
    config: dict,
    rng: np.random.Generator,
) -> dict:
    linear_predictor = design[:, :-1] @ nuisance_coefficients + effect * design[:, -1]
    intercept = intercept_for_prevalence(linear_predictor, config["positive_class_fraction"])
    successes = 0
    failures = 0
    positive_counts = []
    for _ in range(config["simulations_per_scenario"]):
        selected = rng.integers(0, len(design), sample_size)
        sampled = design[selected]
        probabilities = expit(
            intercept + sampled[:, :-1] @ nuisance_coefficients + effect * sampled[:, -1]
        )
        labels = rng.binomial(1, probabilities)
        positive_counts.append(int(labels.sum()))
        if len(np.unique(labels)) != 2:
            failures += 1
            continue
        fitted = fit_logistic_wald(sampled, labels)
        if fitted is None:
            failures += 1
            continue
        coefficient, p_value = fitted
        successes += coefficient > 0 and p_value <= config["alpha_one_sided"]
    interval = wilson_interval(successes, config["simulations_per_scenario"])
    return {
        "sample_size": sample_size,
        "expected_positive_count": float(np.mean(positive_counts)),
        "expected_negative_count": float(sample_size - np.mean(positive_counts)),
        "successful_rejections": successes,
        "fit_failures_counted_as_non_rejections": failures,
        "estimated_power": interval["estimate"],
        "power_wilson_95_ci": {"lower": interval["lower"], "upper": interval["upper"]},
    }


def choose_sample_size(scenarios: dict[str, list[dict]], config: dict) -> int | None:
    planning_rows = scenarios[f"beta_{config['planning_effect']:.2f}"]
    for row in planning_rows:
        minimum_expected = min(row["expected_positive_count"], row["expected_negative_count"])
        if row["estimated_power"] >= config["target_power"] and minimum_expected >= config["minimum_expected_per_class"]:
            return int(row["sample_size"])
    return None


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError("Power-analysis output already exists; refusing to overwrite a frozen result.")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    feature_path = ROOT / config["historical_feature_matrix"]
    design, nuisance_coefficients, metadata = empirical_design(config)
    rng = np.random.default_rng(config["random_seed"])
    scenarios = {}
    for effect in config["standardized_d_pk_effect_scenarios"]:
        key = f"beta_{effect:.2f}"
        scenarios[key] = [
            simulate_scenario(design, nuisance_coefficients, effect, size, config, rng)
            for size in config["sample_sizes"]
        ]
    selected = choose_sample_size(scenarios, config)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"],
        "analysis_status": "frozen_sample_size_result",
        "source_hashes": {
            "power_config": sha256(CONFIG),
            "historical_feature_matrix": sha256(feature_path),
            "power_runner": sha256(Path(__file__)),
        },
        "design_metadata": metadata,
        "simulation_scenarios": scenarios,
        "selected_total_sample_size": selected,
        "selected_expected_per_class": selected * config["positive_class_fraction"] if selected else None,
        "selection_rule_satisfied": selected is not None,
        "interpretation": "This simulation plans collection; it does not test the external endpoint. Labels remain masked until the later one-time evaluation.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "analysis_status": report["analysis_status"],
        "selected_total_sample_size": selected,
        "selected_expected_per_class": report["selected_expected_per_class"],
    }, indent=2))


if __name__ == "__main__":
    main()
