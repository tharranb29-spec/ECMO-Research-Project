#!/usr/bin/env python3

"""Create a post-hoc numerical-stability diagnostic for the holdout joint model."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from track3_a2a.run_confirmatory_holdout_v131 import (
    CONFIG,
    FEATURES,
    ROOT,
    fit_logistic,
    transformed_design,
)


REPORT = ROOT / "outputs" / "v1.3" / "confirmatory" / "holdout_report_v1.3.1.json"
OUTPUT = ROOT / "outputs" / "v1.3" / "confirmatory" / "joint_model_posthoc_diagnostic_v1.3.1.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not REPORT.exists():
        raise FileNotFoundError("The one-time holdout report must exist before post-hoc diagnosis.")
    with FEATURES.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    development = [row for row in rows if row["partition"] == "development"]
    holdout = [row for row in rows if row["partition"] == "locked_holdout"]
    labels = np.asarray([int(row["binary_label"]) for row in holdout], dtype=int)
    _, design, _ = transformed_design(
        development,
        holdout,
        config["model"]["chemistry_descriptors"],
        ["m_cnnaffinity_pk", "d_cnnaffinity_pk", "d_cnnscore"],
        config["model"]["pca_components"],
    )
    unpenalized = fit_logistic(design, labels)
    probabilities = unpenalized.predict_proba(design)[:, 1]
    ridge = LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=10000).fit(design, labels)
    result = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "post_hoc_numerical_stability_diagnostic_not_confirmatory",
        "source_hashes": {"holdout_report": sha256(REPORT), "feature_matrix": sha256(FEATURES)},
        "design_condition_number": float(np.linalg.cond(np.column_stack([np.ones(len(design)), design]))),
        "unpenalized_iterations": int(unpenalized.n_iter_[0]),
        "unpenalized_coefficient_norm": float(np.linalg.norm(unpenalized.coef_[0])),
        "unpenalized_probability_min": float(probabilities.min()),
        "unpenalized_probability_max": float(probabilities.max()),
        "near_zero_probability_count": int((probabilities < 1e-6).sum()),
        "near_one_probability_count": int((probabilities > 1 - 1e-6).sum()),
        "ridge_sensitivity_d_pk_coefficient": float(ridge.coef_[0, 4]),
        "ridge_sensitivity_d_cnnscore_coefficient": float(ridge.coef_[0, 5]),
        "interpretation": (
            "The unpenalized joint sensitivity model is separation-dominated; its extreme coefficients "
            "are numerically unstable and must not be interpreted as independent biological effects."
        ),
        "changes_primary_result": False,
        "human_validation_claimed": False,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
