#!/usr/bin/env python3

"""Run the development-only exploratory A2A Step 5 mechanistic analysis."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from scipy.stats import norm
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "mechanistic_analysis.v1.2.json"
OUTPUT_DIR = ROOT / "outputs" / "v1.2" / "mechanistic_analysis"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(config: dict) -> list[dict]:
    path = ROOT / config["input"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row["partition"] == config["partition"]]


def prepare_design(
    rows: list[dict],
    chemistry_columns: list[str],
    component_count: int,
    signal_columns: list[str],
) -> tuple[np.ndarray, np.ndarray, float]:
    chemistry = np.asarray(
        [[float(row[column]) for column in chemistry_columns] for row in rows], dtype=float
    )
    chemistry_scaled = StandardScaler().fit_transform(chemistry)
    pca = PCA(n_components=component_count)
    components = pca.fit_transform(chemistry_scaled)
    signals = np.asarray(
        [[float(row[column]) for column in signal_columns] for row in rows], dtype=float
    )
    design = StandardScaler().fit_transform(np.column_stack([components, signals]))
    labels = np.asarray([int(row["binary_label"]) for row in rows], dtype=int)
    return design, labels, float(pca.explained_variance_ratio_.sum())


def fit_coefficient(design: np.ndarray, labels: np.ndarray, coefficient_index: int) -> float:
    model = LogisticRegression(
        penalty=None,
        class_weight=None,
        solver="lbfgs",
        max_iter=10000,
    )
    model.fit(design, labels)
    return float(model.coef_[0, coefficient_index])


def fit_from_rows(
    rows: list[dict],
    config: dict,
    component_count: int,
    signal_columns: list[str],
    coefficient_index: int = -1,
) -> tuple[float, float]:
    design, labels, variance = prepare_design(
        rows, config["chemistry"]["descriptors"], component_count, signal_columns
    )
    return fit_coefficient(design, labels, coefficient_index), variance


def bootstrap_interval(
    rows: list[dict],
    config: dict,
    component_count: int,
    signal_columns: list[str],
    resamples: int,
    coefficient_index: int = -1,
    seed_offset: int = 0,
) -> dict:
    rng = np.random.default_rng(config["resampling"]["random_seed"] + seed_offset)
    values = []
    attempts = 0
    while len(values) < resamples and attempts < resamples * 2:
        attempts += 1
        indexes = rng.integers(0, len(rows), len(rows))
        sampled = [rows[index] for index in indexes]
        if len({row["binary_label"] for row in sampled}) < 2:
            continue
        coefficient, _ = fit_from_rows(
            sampled, config, component_count, signal_columns, coefficient_index
        )
        values.append(coefficient)
    confidence = config["resampling"]["confidence_level"]
    alpha = (1.0 - confidence) / 2.0
    return {
        "resamples": len(values),
        "median": float(np.median(values)),
        "lower": float(np.quantile(values, alpha)),
        "upper": float(np.quantile(values, 1.0 - alpha)),
    }


def permutation_test(
    rows: list[dict],
    config: dict,
    component_count: int,
    signal_columns: list[str],
    resamples: int,
    coefficient_index: int = -1,
    seed_offset: int = 0,
) -> dict:
    design, labels, _ = prepare_design(
        rows, config["chemistry"]["descriptors"], component_count, signal_columns
    )
    observed = fit_coefficient(design, labels, coefficient_index)
    rng = np.random.default_rng(config["resampling"]["random_seed"] + seed_offset)
    exceedances = 0
    for _ in range(resamples):
        permuted = rng.permutation(labels)
        coefficient = fit_coefficient(design, permuted, coefficient_index)
        exceedances += abs(coefficient) >= abs(observed)
    return {
        "observed_coefficient": observed,
        "resamples": resamples,
        "two_sided_p_value": float((exceedances + 1) / (resamples + 1)),
    }


def leave_one_out_sign_stability(rows: list[dict], config: dict) -> dict:
    coefficients = []
    for omitted in range(len(rows)):
        subset = rows[:omitted] + rows[omitted + 1:]
        coefficient, _ = fit_from_rows(
            subset,
            config,
            config["chemistry"]["pca_components"],
            ["m_cnnaffinity_pk", "d_cnnaffinity_pk"],
        )
        coefficients.append(coefficient)
    return {
        "refits": len(coefficients),
        "positive_sign_count": sum(value > 0 for value in coefficients),
        "positive_sign_fraction": float(np.mean(np.asarray(coefficients) > 0)),
        "minimum_coefficient": float(min(coefficients)),
        "maximum_coefficient": float(max(coefficients)),
    }


def pc_sensitivity(rows: list[dict], config: dict) -> list[dict]:
    results = []
    resamples = config["resampling"]["sensitivity_resamples"]
    for components in range(1, 7):
        coefficient, variance = fit_from_rows(
            rows, config, components, ["m_cnnaffinity_pk", "d_cnnaffinity_pk"]
        )
        permutation = permutation_test(
            rows, config, components, ["m_cnnaffinity_pk", "d_cnnaffinity_pk"],
            resamples, seed_offset=100 + components,
        )
        results.append({
            "chemistry_pc_count": components,
            "chemistry_variance_explained": variance,
            "d_pk_coefficient": coefficient,
            "permutation_p_value": permutation["two_sided_p_value"],
        })
    return results


def joint_pose_quality_model(rows: list[dict], config: dict) -> dict:
    columns = ["m_cnnaffinity_pk", "d_cnnaffinity_pk", "d_cnnscore"]
    design, labels, _ = prepare_design(
        rows,
        config["chemistry"]["descriptors"],
        config["chemistry"]["pca_components"],
        columns,
    )
    model = LogisticRegression(penalty=None, solver="lbfgs", max_iter=10000).fit(design, labels)
    coefficients = model.coef_[0]
    probabilities = model.predict_proba(design)[:, 1]
    augmented = np.column_stack([np.ones(len(design)), design])
    weights = probabilities * (1.0 - probabilities)
    covariance = np.linalg.pinv(augmented.T @ (augmented * weights[:, None]))
    standard_errors = np.sqrt(np.diag(covariance))[1:]
    d_pk_index = config["chemistry"]["pca_components"] + 1
    d_cnnscore_index = config["chemistry"]["pca_components"] + 2
    def conditional_summary(index: int) -> dict:
        coefficient = float(coefficients[index])
        standard_error = float(standard_errors[index])
        z_score = coefficient / standard_error
        return {
            "coefficient": coefficient,
            "standard_error": standard_error,
            "wald_95_interval": [
                coefficient - 1.959963984540054 * standard_error,
                coefficient + 1.959963984540054 * standard_error,
            ],
            "two_sided_wald_p": float(2.0 * norm.sf(abs(z_score))),
        }
    return {
        "inference": "conditional Wald inference from the joint unpenalized logistic model",
        "d_pk": conditional_summary(d_pk_index),
        "d_cnnscore": conditional_summary(d_cnnscore_index),
    }


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    input_path = ROOT / config["input"]
    rows = load_rows(config)
    components = config["chemistry"]["pca_components"]
    main_columns = ["m_cnnaffinity_pk", "d_cnnaffinity_pk"]
    coefficient, variance = fit_from_rows(rows, config, components, main_columns)
    bootstrap = bootstrap_interval(
        rows, config, components, main_columns,
        config["resampling"]["bootstrap_resamples"], seed_offset=10,
    )
    permutation = permutation_test(
        rows, config, components, main_columns,
        config["resampling"]["permutation_resamples"], seed_offset=20,
    )
    force_field_coefficient, _ = fit_from_rows(
        rows, config, components, ["m_affinity_kcal_mol", "d_affinity_kcal_mol"]
    )
    force_field_permutation = permutation_test(
        rows, config, components, ["m_affinity_kcal_mol", "d_affinity_kcal_mol"],
        config["resampling"]["sensitivity_resamples"], seed_offset=30,
    )
    loo = leave_one_out_sign_stability(rows, config)
    pc_results = pc_sensitivity(rows, config)
    joint = joint_pose_quality_model(rows, config)

    d_pk = np.asarray([float(row["d_cnnaffinity_pk"]) for row in rows])
    d_cnnscore = np.asarray([float(row["d_cnnscore"]) for row in rows])
    mw = np.asarray([float(row["molecular_weight"]) for row in rows])
    hac = np.asarray([float(row["heavy_atom_count"]) for row in rows])
    criteria = config["exploratory_robustness_criteria"]
    checks = {
        "bootstrap_interval_excludes_zero": bootstrap["lower"] > 0 or bootstrap["upper"] < 0,
        "permutation_p_within_limit": permutation["two_sided_p_value"] <= criteria["d_pk_two_sided_permutation_p_max"],
        "leave_one_out_sign_stable": loo["positive_sign_fraction"] >= criteria["leave_one_out_positive_sign_fraction_min"],
        "pc_1_to_6_positive": all(item["d_pk_coefficient"] > 0 for item in pc_results),
    }
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_id": config["protocol_id"],
        "interpretation": config["interpretation"],
        "formal_confirmatory_claim": False,
        "formal_label_review_gate_passed": False,
        "locked_holdout_accessed": False,
        "source_hashes": {
            "config": sha256(CONFIG),
            "feature_matrix": sha256(input_path),
        },
        "software": {"numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "dataset": {
            "molecule_count": len(rows),
            "agonists": sum(int(row["binary_label"]) for row in rows),
            "antagonists": sum(1 - int(row["binary_label"]) for row in rows),
        },
        "main_exploratory_model": {
            "chemistry_pc_count": components,
            "chemistry_variance_explained": variance,
            "standardized_d_pk_coefficient": coefficient,
            "bootstrap_95_interval": bootstrap,
            "permutation": permutation,
        },
        "leave_one_out_sign_stability": loo,
        "pc_count_sensitivity": pc_results,
        "force_field_d_affinity_comparator": {
            "standardized_coefficient": force_field_coefficient,
            "permutation": force_field_permutation,
        },
        "pose_quality_entanglement": {
            "pearson_correlation_d_pk_d_cnnscore": float(np.corrcoef(d_pk, d_cnnscore)[0, 1]),
            "joint_model": joint,
        },
        "descriptor_redundancy": {
            "pearson_correlation_molecular_weight_heavy_atom_count": float(np.corrcoef(mw, hac)[0, 1]),
            "retained": "heavy_atom_count",
            "dropped": "molecular_weight",
        },
        "exploratory_robustness_checks": checks,
        "exploratory_robustness_checks_passed": all(checks.values()),
        "limitations": config["formal_limitations"],
        "next_gate": "complete formal record-level dual review, freeze a prospective v1.3 hypothesis, then evaluate once on untouched data",
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "development_mechanistic_report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "dataset": report["dataset"],
        "main_exploratory_model": report["main_exploratory_model"],
        "force_field_d_affinity_comparator": report["force_field_d_affinity_comparator"],
        "pose_quality_entanglement": report["pose_quality_entanglement"],
        "exploratory_robustness_checks": checks,
        "formal_confirmatory_claim": False,
        "locked_holdout_accessed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
