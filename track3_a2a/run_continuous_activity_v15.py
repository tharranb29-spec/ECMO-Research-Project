#!/usr/bin/env python3

"""Run the frozen exploratory v1.5 continuous-activity development pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "continuous_activity.v1.5.json"
SUMMARY = ROOT / "data" / "curated" / "activity_molecule_summary_v15_exploratory.csv"
FEATURES = ROOT / "outputs" / "v1.3" / "docking_clean_computational.csv"
OUTPUTS = ROOT / "outputs" / "v1.5" / "continuous_activity"
DESCRIPTORS = [
    "molecular_weight", "clogp", "h_bond_donors", "h_bond_acceptors",
    "rotatable_bonds", "tpsa", "heavy_atom_count", "qed",
]
DOCKING = [
    "m_affinity_kcal_mol", "d_affinity_kcal_mol", "m_cnnaffinity_pk",
    "d_cnnaffinity_pk", "m_cnnscore", "d_cnnscore",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fingerprint_data(rows: list[dict]) -> tuple[np.ndarray, list]:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    bit_vectors = []
    matrix = np.zeros((len(rows), 2048), dtype=np.uint8)
    for index, row in enumerate(rows):
        molecule = Chem.MolFromSmiles(row["standardized_smiles"])
        if molecule is None:
            raise ValueError(f"Invalid standardized SMILES for {row['molecule_id']}")
        vector = generator.GetFingerprint(molecule)
        bit_vectors.append(vector)
        DataStructs.ConvertToNumpyArray(vector, matrix[index])
    return matrix.astype(float), bit_vectors


def numeric_matrix(rows: list[dict], columns: list[str]) -> np.ndarray:
    return np.asarray([
        [float(row[column]) if row.get(column) not in {None, ""} else np.nan for column in columns]
        for row in rows
    ])


def rf(config: dict) -> RandomForestRegressor:
    params = config["models"]["qsar_primary"]["parameters"]
    return RandomForestRegressor(
        n_estimators=params["n_estimators"],
        max_features=params["max_features"],
        min_samples_leaf=params["min_samples_leaf"],
        random_state=params["random_state"],
        n_jobs=params["n_jobs"],
    )


def impute(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    imp = SimpleImputer(strategy="median")
    return imp.fit_transform(train), imp.transform(test)


def robust_distance(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = np.nanmedian(train, axis=0)
    scale = np.nanmedian(np.abs(train - center), axis=0)
    fallback = np.nanstd(train, axis=0)
    scale = np.where((scale > 1e-12) & np.isfinite(scale), scale, fallback)
    scale = np.where((scale > 1e-12) & np.isfinite(scale), scale, 1.0)
    train_distance = np.sqrt(np.mean(((train - center) / scale) ** 2, axis=1))
    test_distance = np.sqrt(np.mean(((test - center) / scale) ** 2, axis=1))
    return train_distance, test_distance


def metric_set(y: np.ndarray, prediction: np.ndarray, lower=None, upper=None) -> dict:
    result = {
        "n": int(len(y)),
        "r2": float(r2_score(y, prediction)) if len(y) >= 10 else None,
        "rmse": float(math.sqrt(mean_squared_error(y, prediction))),
        "mae": float(mean_absolute_error(y, prediction)),
        "spearman_rho": float(spearmanr(y, prediction).statistic) if len(y) >= 3 else None,
    }
    if len(y) >= 2 and float(np.std(prediction)) > 0:
        slope, intercept = np.polyfit(prediction, y, 1)
        result["calibration_intercept"] = float(intercept)
        result["calibration_slope"] = float(slope)
    else:
        result["calibration_intercept"] = None
        result["calibration_slope"] = None
    result["empirical_interval_coverage"] = (
        float(np.mean((y >= lower) & (y <= upper))) if lower is not None and upper is not None else None
    )
    return result


def percentile_interval(values: list[float]) -> dict:
    return {
        "estimate": float(np.median(values)),
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
    }


def bootstrap(y: np.ndarray, predictions: dict[str, np.ndarray], seed: int, count: int) -> dict:
    rng = np.random.default_rng(seed)
    values = {name: {metric: [] for metric in ["r2", "rmse", "mae", "spearman_rho"]} for name in predictions}
    deltas = {"delta_r2_E_minus_AB": [], "delta_rmse_E_minus_AB": []}
    for _ in range(count):
        selected = rng.integers(0, len(y), len(y))
        ys = y[selected]
        for name, prediction in predictions.items():
            ps = prediction[selected]
            values[name]["r2"].append(float(r2_score(ys, ps)))
            values[name]["rmse"].append(float(math.sqrt(mean_squared_error(ys, ps))))
            values[name]["mae"].append(float(mean_absolute_error(ys, ps)))
            values[name]["spearman_rho"].append(float(spearmanr(ys, ps).statistic))
        deltas["delta_r2_E_minus_AB"].append(
            r2_score(ys, predictions["E_RF"][selected]) - r2_score(ys, predictions["AB_RF"][selected])
        )
        deltas["delta_rmse_E_minus_AB"].append(
            math.sqrt(mean_squared_error(ys, predictions["E_RF"][selected]))
            - math.sqrt(mean_squared_error(ys, predictions["AB_RF"][selected]))
        )
    return {
        "model_intervals": {
            name: {metric: percentile_interval(samples) for metric, samples in metrics.items()}
            for name, metrics in values.items()
        },
        "paired_docking_increment": {name: percentile_interval(samples) for name, samples in deltas.items()},
        "resamples": count,
    }


def evaluate_endpoint(rows: list[dict], config: dict, endpoint: str, tag: str) -> tuple[dict, list[dict]]:
    y = np.asarray([float(row["aggregated_pactivity"]) for row in rows])
    fp, bit_vectors = fingerprint_data(rows)
    desc = numeric_matrix(rows, DESCRIPTORS)
    dock = numeric_matrix(rows, DOCKING)
    groups = np.asarray([row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in rows])
    repeats = len(config["development_evaluation"]["repeat_seeds"])
    folds = config["development_evaluation"]["folds"]
    if len(set(groups)) < folds:
        raise ValueError(f"{endpoint} has fewer than {folds} scaffold groups")

    names = ["Mean", "AB_Ridge", "AB_RF", "E_RF"]
    prediction_matrix = {name: np.full((repeats, len(rows)), np.nan) for name in names}
    similarity_matrix = np.full((repeats, len(rows)), np.nan)
    distance_matrix = np.full((repeats, len(rows)), np.nan)
    descriptor_training_distances = []
    fold_manifest = []

    for repeat, seed in enumerate(config["development_evaluation"]["repeat_seeds"]):
        splitter = GroupKFold(n_splits=folds, shuffle=True, random_state=seed)
        for fold, (train, test) in enumerate(splitter.split(fp, y, groups), start=1):
            train_desc, test_desc = impute(desc[train], desc[test])
            train_dock, test_dock = impute(dock[train], dock[test])
            train_ab = np.hstack([fp[train], train_desc])
            test_ab = np.hstack([fp[test], test_desc])
            train_e = np.hstack([fp[train], train_desc, train_dock])
            test_e = np.hstack([fp[test], test_desc, test_dock])

            prediction_matrix["Mean"][repeat, test] = float(np.mean(y[train]))
            ridge = Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))])
            ridge.fit(train_ab, y[train])
            prediction_matrix["AB_Ridge"][repeat, test] = ridge.predict(test_ab)
            ab_model = rf(config)
            ab_model.fit(train_ab, y[train])
            prediction_matrix["AB_RF"][repeat, test] = ab_model.predict(test_ab)
            e_model = rf(config)
            e_model.fit(train_e, y[train])
            prediction_matrix["E_RF"][repeat, test] = e_model.predict(test_e)

            for index in test:
                similarity_matrix[repeat, index] = max(DataStructs.BulkTanimotoSimilarity(bit_vectors[index], [bit_vectors[i] for i in train]))
            train_distance, test_distance = robust_distance(train_desc, test_desc)
            descriptor_training_distances.extend(train_distance.tolist())
            distance_matrix[repeat, test] = test_distance
            fold_manifest.append({
                "analysis": tag,
                "endpoint_name": endpoint,
                "repeat": repeat + 1,
                "seed": seed,
                "fold": fold,
                "train_n": len(train),
                "test_n": len(test),
                "test_ids": [rows[index]["molecule_id"] for index in test],
            })

    if any(np.isnan(values).any() for values in prediction_matrix.values()):
        raise RuntimeError(f"Incomplete OOF predictions for {endpoint}")
    predictions = {name: values.mean(axis=0) for name, values in prediction_matrix.items()}
    lower = {name: np.quantile(values, 0.025, axis=0) for name, values in prediction_matrix.items()}
    upper = {name: np.quantile(values, 0.975, axis=0) for name, values in prediction_matrix.items()}
    similarity = similarity_matrix.mean(axis=0)
    distance = distance_matrix.mean(axis=0)
    similarity_threshold = float(np.quantile(similarity_matrix, 0.05))
    distance_threshold = float(np.quantile(descriptor_training_distances, 0.99))
    inside = (similarity >= similarity_threshold) & (distance <= distance_threshold)

    metrics = {
        name: metric_set(y, prediction, lower[name], upper[name])
        for name, prediction in predictions.items()
    }
    strata = {}
    for label, mask in [("inside", inside), ("outside", ~inside)]:
        strata[label] = {
            name: metric_set(y[mask], prediction[mask], lower[name][mask], upper[name][mask])
            for name, prediction in predictions.items()
        } if mask.any() else {}
    boot = bootstrap(y, predictions, config["uncertainty"]["random_seed"], 2000)
    prediction_rows = []
    for index, row in enumerate(rows):
        prediction_rows.append({
            "analysis": tag,
            "endpoint_name": endpoint,
            "molecule_id": row["molecule_id"],
            "scaffold": groups[index],
            "observed_pactivity": y[index],
            **{f"prediction_{name}": predictions[name][index] for name in names},
            **{f"interval_lower_{name}": lower[name][index] for name in names},
            **{f"interval_upper_{name}": upper[name][index] for name in names},
            "nearest_training_tanimoto": similarity[index],
            "robust_descriptor_distance": distance[index],
            "inside_applicability_domain": bool(inside[index]),
            "high_disagreement_flag": row["high_disagreement_flag"],
        })
    return {
        "analysis": tag,
        "endpoint_name": endpoint,
        "n": len(rows),
        "scaffold_count": len(set(groups)),
        "small_sample_warning": len(rows) < 40,
        "metrics": metrics,
        "applicability_domain": {
            "similarity_threshold": similarity_threshold,
            "descriptor_distance_threshold": distance_threshold,
            "inside_n": int(inside.sum()),
            "outside_n": int((~inside).sum()),
            "stratified_metrics": strata,
        },
        "uncertainty": boot,
        "fold_manifest": fold_manifest,
        "interval_method": "2.5th and 97.5th percentiles across ten repeated OOF predictions; exploratory coverage diagnostic",
    }, prediction_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--features", type=Path, default=FEATURES)
    parser.add_argument("--output-dir", type=Path, default=OUTPUTS)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    summaries = read_csv(args.summary)
    features = {row["molecule_id"]: row for row in read_csv(args.features)}
    joined = []
    for summary in summaries:
        if summary["molecule_id"] not in features:
            raise ValueError(f"Missing feature row for {summary['molecule_id']}")
        row = {**features[summary["molecule_id"]], **summary}
        if row["review_status"] == "admitted_exploratory" and row["development_partition"] == "development":
            joined.append(row)
    counts = Counter(row["endpoint_name"] for row in joined)
    if args.validate_only:
        print(json.dumps({
            "status": "validated_not_run",
            "eligible_development_counts": dict(sorted(counts.items())),
            "locked_holdout_rows_used": 0,
        }, indent=2))
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    predictions = []
    for endpoint in ["pBind_Ki", "pFunc_agonism", "pFunc_inhibition"]:
        endpoint_rows = [row for row in joined if row["endpoint_name"] == endpoint]
        if len(endpoint_rows) < 10 or len({row["generic_murcko_scaffold_smiles"] for row in endpoint_rows}) < 5:
            results[endpoint] = {"status": "insufficient_development_data", "n": len(endpoint_rows)}
            continue
        primary, primary_predictions = evaluate_endpoint(endpoint_rows, config, endpoint, "primary")
        results[endpoint] = {"status": "complete_exploratory", "primary": primary}
        predictions.extend(primary_predictions)
        low_disagreement = [row for row in endpoint_rows if row["high_disagreement_flag"].lower() != "true"]
        if len(low_disagreement) != len(endpoint_rows) and len(low_disagreement) >= 10:
            sensitivity, sensitivity_predictions = evaluate_endpoint(
                low_disagreement, config, endpoint, "exclude_high_disagreement"
            )
            results[endpoint]["high_disagreement_sensitivity"] = sensitivity
            predictions.extend(sensitivity_predictions)

    prediction_path = args.output_dir / "development_oof_predictions.csv"
    write_csv(prediction_path, predictions)
    output = {
        "schema_version": 1,
        "created_at": utc_now(),
        "specification_id": config["specification_id"],
        "claim_status": "exploratory_only",
        "historical_locked_holdout_rows_used": 0,
        "source_hashes": {
            "config": sha256(CONFIG),
            "summary": sha256(args.summary),
            "features": sha256(args.features),
        },
        "eligible_development_counts": dict(sorted(counts.items())),
        "results": results,
        "prediction_file": str(prediction_path.relative_to(ROOT)) if predictions else None,
        "prediction_sha256": sha256(prediction_path) if predictions else None,
        "external_confirmation_performed": False,
        "model_promotion_allowed": False,
    }
    output_path = args.output_dir / "development_results.json"
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
