#!/usr/bin/env python3

"""Run the hash-verified v1.3.1 locked-holdout analysis exactly once."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from track3_a2a.run_model_evaluation_v12 import build_feature_sets, estimator


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "confirmatory_spec.v1.3.1.json"
FEATURES = ROOT / "outputs" / "v1.3" / "docking_clean_computational.csv"
PARTITIONS = ROOT / "data" / "curated" / "chembl251_computational_partitions_v1.3.json"
FEATURE_AUDIT = ROOT / "outputs" / "v1.3" / "feature_construction_audit.json"
MODEL_CONFIG = ROOT / "config" / "model_evaluation.v1.2.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_logistic(design, labels):
    model = LogisticRegression(penalty=None, solver="lbfgs", max_iter=10000)
    model.fit(design, labels)
    return model


def transformed_design(development, holdout, chemistry_columns, signals, component_count=3):
    development_chemistry = np.asarray(
        [[float(row[column]) for column in chemistry_columns] for row in development], dtype=float
    )
    holdout_chemistry = np.asarray(
        [[float(row[column]) for column in chemistry_columns] for row in holdout], dtype=float
    )
    chemistry_scaler = StandardScaler().fit(development_chemistry)
    pca = PCA(n_components=component_count).fit(chemistry_scaler.transform(development_chemistry))
    development_pcs = pca.transform(chemistry_scaler.transform(development_chemistry))
    holdout_pcs = pca.transform(chemistry_scaler.transform(holdout_chemistry))
    development_signals = np.asarray(
        [[float(row[column]) for column in signals] for row in development], dtype=float
    )
    holdout_signals = np.asarray(
        [[float(row[column]) for column in signals] for row in holdout], dtype=float
    )
    scaler = StandardScaler().fit(np.column_stack([development_pcs, development_signals]))
    return (
        scaler.transform(np.column_stack([development_pcs, development_signals])),
        scaler.transform(np.column_stack([holdout_pcs, holdout_signals])),
        float(pca.explained_variance_ratio_.sum()),
    )


def one_sided_permutation(design, labels, coefficient_index, resamples, seed):
    observed = float(fit_logistic(design, labels).coef_[0, coefficient_index])
    rng = np.random.default_rng(seed)
    exceedances = 0
    for _ in range(resamples):
        permuted = rng.permutation(labels)
        coefficient = float(fit_logistic(design, permuted).coef_[0, coefficient_index])
        exceedances += coefficient >= observed
    return {
        "observed_coefficient": observed,
        "alternative": "greater_than_zero",
        "resamples": resamples,
        "exceedances": exceedances,
        "one_sided_p_value": float((exceedances + 1) / (resamples + 1)),
    }


def verify_freeze(config, manifest):
    expected = manifest["source_hashes"]
    actual = {
        "confirmatory_spec": sha256(CONFIG),
        "feature_matrix": sha256(FEATURES),
        "partition_manifest": sha256(PARTITIONS),
        "feature_audit": sha256(FEATURE_AUDIT),
        "holdout_runner": sha256(Path(__file__)),
        "predictive_model_config_v1.2": sha256(MODEL_CONFIG),
    }
    if actual != expected:
        raise RuntimeError(f"Frozen input or implementation hash mismatch: expected {expected}, got {actual}")
    if manifest["specification_id"] != config["specification_id"]:
        raise RuntimeError("Freeze manifest and confirmatory specification disagree.")


def predictive_sensitivity(development, holdout):
    config = json.loads(MODEL_CONFIG.read_text(encoding="utf-8"))
    development_features, _ = build_feature_sets(development, config)
    holdout_features, _ = build_feature_sets(holdout, config)
    development_labels = np.asarray([int(row["binary_label"]) for row in development], dtype=int)
    holdout_labels = np.asarray([int(row["binary_label"]) for row in holdout], dtype=int)
    probabilities = {}
    for name in ("AB", "E"):
        model = estimator(config)
        model.fit(development_features[name], development_labels)
        probabilities[name] = model.predict_proba(holdout_features[name])[:, 1]
    auc_ab = float(roc_auc_score(holdout_labels, probabilities["AB"]))
    auc_e = float(roc_auc_score(holdout_labels, probabilities["E"]))
    return {
        "claim_status": "descriptive_only",
        "roc_auc_AB": auc_ab,
        "roc_auc_E": auc_e,
        "delta_E_minus_AB": auc_e - auc_ab,
    }, probabilities


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    freeze_path = ROOT / config["outputs"]["freeze_manifest"]
    report_path = ROOT / config["outputs"]["holdout_report"]
    predictions_path = ROOT / config["outputs"]["holdout_predictions"]
    if report_path.exists() or predictions_path.exists():
        raise FileExistsError("The one-time holdout output already exists; refusing to rerun or overwrite it.")
    manifest = json.loads(freeze_path.read_text(encoding="utf-8"))
    verify_freeze(config, manifest)

    with FEATURES.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    development = [row for row in rows if row["partition"] == "development"]
    holdout = [row for row in rows if row["partition"] == "locked_holdout"]
    labels = np.asarray([int(row["binary_label"]) for row in holdout], dtype=int)
    chemistry = config["model"]["chemistry_descriptors"]

    _, holdout_main, variance = transformed_design(
        development,
        holdout,
        chemistry,
        ["m_cnnaffinity_pk", "d_cnnaffinity_pk"],
        config["model"]["pca_components"],
    )
    primary = one_sided_permutation(
        holdout_main,
        labels,
        coefficient_index=4,
        resamples=config["confirmatory_endpoint"]["resamples"],
        seed=20260911,
    )
    primary["success"] = (
        primary["observed_coefficient"] > 0
        and primary["one_sided_p_value"] <= config["confirmatory_endpoint"]["alpha"]
    )

    _, holdout_joint, _ = transformed_design(
        development, holdout, chemistry,
        ["m_cnnaffinity_pk", "d_cnnaffinity_pk", "d_cnnscore"],
        config["model"]["pca_components"],
    )
    joint_coefficients = fit_logistic(holdout_joint, labels).coef_[0]
    _, holdout_force_field, _ = transformed_design(
        development,
        holdout,
        chemistry,
        ["m_affinity_kcal_mol", "d_affinity_kcal_mol"],
        config["model"]["pca_components"],
    )
    force_field = one_sided_permutation(
        holdout_force_field, labels, coefficient_index=4, resamples=2000, seed=20260912
    )
    predictive, predictive_probabilities = predictive_sensitivity(development, holdout)

    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "specification_id": config["specification_id"],
        "analysis_status": "one_time_locked_holdout_evaluation_complete",
        "freeze_manifest_sha256": sha256(freeze_path),
        "holdout_accessed": True,
        "holdout_record_count": len(holdout),
        "holdout_agonists": int(labels.sum()),
        "holdout_antagonists": int(len(labels) - labels.sum()),
        "development_fitted_chemistry_variance_explained": variance,
        "primary_confirmatory_endpoint": primary,
        "mandatory_sensitivity": {
            "pose_quality_correlation_d_pk_d_cnnscore": float(np.corrcoef(
                [float(row["d_cnnaffinity_pk"]) for row in holdout],
                [float(row["d_cnnscore"]) for row in holdout],
            )[0, 1]),
            "joint_model_standardized_d_pk_coefficient": float(joint_coefficients[4]),
            "joint_model_standardized_d_cnnscore_coefficient": float(joint_coefficients[5]),
            "force_field_d_affinity": force_field,
            "predictive_AB_vs_E": predictive,
        },
        "interpretation_boundary": config["promotion_rule"],
        "human_validation_claimed": False,
        "biological_efficacy_claimed": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    with predictions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["molecule_id", "label", "probability_AB", "probability_E"])
        writer.writeheader()
        for index, row in enumerate(holdout):
            writer.writerow({
                "molecule_id": row["molecule_id"],
                "label": row["label"],
                "probability_AB": float(predictive_probabilities["AB"][index]),
                "probability_E": float(predictive_probabilities["E"][index]),
            })
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
