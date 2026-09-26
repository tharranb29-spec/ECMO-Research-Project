#!/usr/bin/env python3
"""Export a transparent, development-only AB_Ridge scorer for shadow display.

This fits the frozen v1.6 chemistry model on development rows only. It does not
calibrate intervals, read external outcomes, or authorize model promotion.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import rdkit
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from run_continuous_activity_v15 import DESCRIPTORS, fingerprint_data, numeric_matrix


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "config/protocol.v1.6.json"
SUMMARY = ROOT / "data/curated/activity_molecule_summary_v15_exploratory.csv"
FEATURES = ROOT / "outputs/v1.3/docking_clean_computational.csv"
OUTPUT = ROOT / "outputs/v1.6/model_reproduction/ab_ridge_shadow_scorer.json"


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    primary = protocol["models"]["primary_external_predictor"]
    if primary["name"] != "AB_Ridge" or primary["parameters"] != {"alpha": 1.0}:
        raise RuntimeError("Frozen primary model is not AB_Ridge(alpha=1.0).")
    features = {row["molecule_id"]: row for row in read_rows(FEATURES)}
    rows = []
    for summary in read_rows(SUMMARY):
        if (summary["endpoint_name"] == "pBind_Ki"
                and summary["review_status"] == "admitted_exploratory"
                and summary["development_partition"] == "development"):
            molecule_id = summary["molecule_id"]
            if molecule_id not in features:
                raise RuntimeError(f"Missing development feature row: {molecule_id}")
            rows.append({**features[molecule_id], **summary})
    # The frozen reproduction has 78 endpoint rows but 69 distinct molecule IDs.
    # Retain those rows exactly; silently deduplicating would change the fit.
    if len(rows) != 78 or len({row["molecule_id"] for row in rows}) != 69:
        raise RuntimeError(f"Unexpected development cohort: {len(rows)} rows")

    fingerprint, _ = fingerprint_data(rows)
    descriptors = numeric_matrix(rows, DESCRIPTORS)
    imputer = SimpleImputer(strategy="median")
    matrix = np.hstack([fingerprint, imputer.fit_transform(descriptors)])
    y = np.asarray([float(row["aggregated_pactivity"]) for row in rows])
    pipeline = Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))])
    pipeline.fit(matrix, y)
    scale = pipeline.named_steps["scale"]
    ridge = pipeline.named_steps["model"]
    weights = ridge.coef_ / scale.scale_
    intercept = float(ridge.intercept_ - np.dot(weights, scale.mean_))
    shadow_predictions = intercept + matrix @ weights
    if not np.allclose(shadow_predictions, pipeline.predict(matrix), atol=1e-9, rtol=0):
        raise RuntimeError("Exported linear scorer differs from the frozen pipeline.")

    payload = {
        "schema_id": "a2a-ab-ridge-shadow.v1",
        "status": "development_fit_only_not_external_confirmation",
        "endpoint": "pBind_Ki",
        "model_id": "AB_Ridge(alpha=1.0)",
        "promotion_allowed": False,
        "external_outcomes_loaded": False,
        "training_partition": "development_only",
        "training_n": len(rows),
        "training_distinct_molecules": 69,
        "training_molecule_ids_sha256": hashlib.sha256("\n".join(sorted(row["molecule_id"] for row in rows)).encode()).hexdigest(),
        "fingerprint": {"type": "Morgan", "radius": 2, "size": 2048},
        "descriptors": DESCRIPTORS,
        "descriptor_medians": [float(value) for value in imputer.statistics_],
        "intercept": intercept,
        "weights": [float(value) for value in weights],
        "source_sha256": {"protocol": sha256(PROTOCOL), "summary": sha256(SUMMARY), "features": sha256(FEATURES)},
        "software": {"rdkit": rdkit.__version__, "sklearn": sklearn.__version__},
        "claim_limit": "Exploratory development-fit point estimate only; no validated interval, applicability admission, candidate rank, or external confirmation.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUTPUT), "sha256": sha256(OUTPUT), "training_n": len(rows)}))


if __name__ == "__main__":
    main()
