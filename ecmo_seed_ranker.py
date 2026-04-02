#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path


FEATURES = [
    "affinity_strength_score",
    "specificity_score",
    "functional_immunomodulation_score",
    "surface_validation_score",
    "conjugation_feasibility_score",
    "hemocompatibility_proxy_score",
    "multivalency_or_clustering_score",
    "literature_confidence_score",
]

FEATURE_LABELS = {
    "affinity_strength_score": "strong affinity evidence",
    "specificity_score": "good target specificity",
    "functional_immunomodulation_score": "strong immunomodulation evidence",
    "surface_validation_score": "surface-translation support",
    "conjugation_feasibility_score": "good conjugation feasibility",
    "hemocompatibility_proxy_score": "good hemocompatibility proxy",
    "multivalency_or_clustering_score": "useful clustering or multivalency",
    "literature_confidence_score": "strong literature confidence",
}

TARGET_PRIORS = {
    "Siglec-9": {
        "affinity_strength_score": 0.24,
        "specificity_score": 0.12,
        "functional_immunomodulation_score": 0.25,
        "surface_validation_score": 0.12,
        "conjugation_feasibility_score": 0.08,
        "hemocompatibility_proxy_score": 0.08,
        "multivalency_or_clustering_score": 0.08,
        "literature_confidence_score": 0.03,
    },
    "SIRPa": {
        "affinity_strength_score": 0.22,
        "specificity_score": 0.10,
        "functional_immunomodulation_score": 0.20,
        "surface_validation_score": 0.20,
        "conjugation_feasibility_score": 0.09,
        "hemocompatibility_proxy_score": 0.12,
        "multivalency_or_clustering_score": 0.04,
        "literature_confidence_score": 0.03,
    },
}


def clamp(value, low, high):
    return max(low, min(high, value))


def affinity_um_to_score(affinity_um):
    if affinity_um is None:
        return None
    if affinity_um <= 0.01:
        return 0.98
    if affinity_um <= 0.10:
        return 0.92
    if affinity_um <= 1.00:
        return 0.82
    if affinity_um <= 10.0:
        return 0.74
    if affinity_um <= 50.0:
        return 0.64
    if affinity_um <= 200.0:
        return 0.50
    if affinity_um <= 1000.0:
        return 0.30
    return 0.18


def default_label(score):
    if score >= 80:
        return "advance"
    if score >= 65:
        return "secondary"
    if score >= 50:
        return "hold"
    return "reject"


def load_seed_records(path):
    with open(path, "r", encoding="utf-8") as handle:
        records = json.load(handle)
    for record in records:
        if record.get("affinity_strength_score") in ("", None):
            record["affinity_strength_score"] = affinity_um_to_score(record.get("affinity_uM"))
    return records


def load_candidate_csv(path):
    records = []
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cleaned = {}
            for key, value in row.items():
                if value is None:
                    cleaned[key] = value
                    continue
                cleaned[key] = value.strip()
            if not cleaned.get("candidate_name"):
                continue
            affinity_um = cleaned.get("affinity_uM")
            affinity_um = float(affinity_um) if affinity_um else None
            affinity_strength = cleaned.get("affinity_strength_score")
            affinity_strength = float(affinity_strength) if affinity_strength else affinity_um_to_score(affinity_um)
            record = {
                "id": cleaned.get("id") or cleaned["candidate_name"].lower().replace(" ", "_"),
                "candidate_name": cleaned["candidate_name"],
                "target_receptor": cleaned["target_receptor"],
                "modality": cleaned.get("modality", "unknown"),
                "affinity_uM": affinity_um,
                "affinity_note": cleaned.get("affinity_note") or "",
                "affinity_strength_score": affinity_strength,
                "specificity_score": float(cleaned["specificity_score"]),
                "functional_immunomodulation_score": float(cleaned["functional_immunomodulation_score"]),
                "surface_validation_score": float(cleaned["surface_validation_score"]),
                "conjugation_feasibility_score": float(cleaned["conjugation_feasibility_score"]),
                "hemocompatibility_proxy_score": float(cleaned["hemocompatibility_proxy_score"]),
                "multivalency_or_clustering_score": float(cleaned["multivalency_or_clustering_score"]),
                "literature_confidence_score": float(cleaned["literature_confidence_score"]),
                "training_label_score": None,
                "training_label": None,
                "evidence_summary": cleaned.get("evidence_summary") or "",
                "source_urls": [cleaned["source_url"]] if cleaned.get("source_url") else [],
            }
            records.append(record)
    return records


def vectorize(record):
    return [float(record[feature]) for feature in FEATURES]


def train_target_model(records, target, epochs=4000, learning_rate=0.08, reg_strength=0.35):
    target_rows = [row for row in records if row["target_receptor"] == target and row.get("training_label_score") is not None]
    if len(target_rows) < 3:
        raise ValueError(f"Need at least 3 training rows for {target}.")

    prior = [TARGET_PRIORS[target][feature] for feature in FEATURES]
    weights = prior[:]
    bias = 0.02

    xs = [vectorize(row) for row in target_rows]
    ys = [row["training_label_score"] / 100.0 for row in target_rows]

    for _ in range(epochs):
        grad_w = [0.0 for _ in FEATURES]
        grad_b = 0.0
        count = len(xs)
        for x, y in zip(xs, ys):
            pred = bias + sum(w * v for w, v in zip(weights, x))
            err = pred - y
            for idx in range(len(FEATURES)):
                grad_w[idx] += err * x[idx]
            grad_b += err

        for idx in range(len(FEATURES)):
            grad_w[idx] = (grad_w[idx] / count) + reg_strength * (weights[idx] - prior[idx])
            weights[idx] = clamp(weights[idx] - learning_rate * grad_w[idx], 0.0, 1.0)
        bias = clamp(bias - learning_rate * (grad_b / count), -0.25, 0.35)

    return {"target": target, "weights": dict(zip(FEATURES, weights)), "bias": bias}


def predict_score(model, record):
    score = model["bias"]
    for feature in FEATURES:
        score += model["weights"][feature] * float(record[feature])
    return clamp(score, 0.0, 1.0)


def explain_prediction(model, record):
    contributions = []
    for feature in FEATURES:
        contribution = model["weights"][feature] * float(record[feature])
        contributions.append((contribution, FEATURE_LABELS[feature], float(record[feature])))
    contributions.sort(reverse=True)
    reasons = []
    for contribution, label, feature_value in contributions:
        if contribution < 0.045 or feature_value < 0.20:
            continue
        reasons.append(label)
        if len(reasons) == 3:
            break
    if not reasons:
        return "Limited positive evidence in the current seed features."
    return ", ".join(reasons) + "."


def leave_one_out_mae(records, target):
    target_rows = [row for row in records if row["target_receptor"] == target and row.get("training_label_score") is not None]
    if len(target_rows) < 4:
        return None

    absolute_errors = []
    for holdout in target_rows:
        train_rows = [row for row in target_rows if row["id"] != holdout["id"]]
        model = train_target_model(train_rows, target)
        pred = predict_score(model, holdout) * 100.0
        absolute_errors.append(abs(pred - holdout["training_label_score"]))
    return sum(absolute_errors) / len(absolute_errors)


def rank_records(seed_records, candidate_records):
    models = {}
    metrics = {}
    for target in sorted({row["target_receptor"] for row in seed_records}):
        models[target] = train_target_model(seed_records, target)
        metrics[target] = leave_one_out_mae(seed_records, target)

    ranked = []
    for record in candidate_records:
        target = record["target_receptor"]
        if target not in models:
            raise ValueError(f"No trained model available for target '{target}'.")
        model = models[target]
        raw_score = predict_score(model, record)
        score_100 = round(raw_score * 100, 1)
        ranked.append(
            {
                "id": record["id"],
                "candidate_name": record["candidate_name"],
                "target_receptor": target,
                "modality": record["modality"],
                "predicted_score": score_100,
                "recommendation": default_label(score_100),
                "explanation": explain_prediction(model, record),
                "evidence_summary": record.get("evidence_summary", ""),
                "source_urls": record.get("source_urls", []),
            }
        )

    ranked.sort(key=lambda item: (item["target_receptor"], -item["predicted_score"], item["candidate_name"]))
    return {"models": models, "metrics": metrics, "ranked": ranked}


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def write_markdown(path, payload, input_name):
    lines = []
    lines.append("# ECMO Seed Ranking Report")
    lines.append("")
    lines.append(f"Input set: `{input_name}`")
    lines.append("")
    lines.append("This report comes from a small literature-seeded ranking prototype. It is useful for project design and prioritization discussions, not as a final discovery model.")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    for target, mae in payload["metrics"].items():
        if mae is None:
            metric_text = "not enough rows for leave-one-out validation"
        else:
            metric_text = f"leave-one-out MAE: {mae:.1f} score points"
        lines.append(f"- `{target}`: {metric_text}")
    lines.append("")
    current_target = None
    for row in payload["ranked"]:
        if row["target_receptor"] != current_target:
            current_target = row["target_receptor"]
            lines.append(f"## {current_target}")
            lines.append("")
        lines.append(f"- `{row['candidate_name']}`: {row['predicted_score']:.1f} ({row['recommendation']})")
        lines.append(f"  Reasoning: {row['explanation']}")
        if row["evidence_summary"]:
            lines.append(f"  Evidence: {row['evidence_summary']}")
    lines.append("")
    lines.append("## Learned Weights")
    lines.append("")
    for target, model in payload["models"].items():
        lines.append(f"### {target}")
        lines.append("")
        lines.append(f"- `bias`: {model['bias']:.3f}")
        for feature in FEATURES:
            lines.append(f"- `{feature}`: {model['weights'][feature]:.3f}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Train and run a rough ECMO ligand ranking model.")
    parser.add_argument(
        "--seed",
        default="data/seed_ligands.json",
        help="Path to the literature-seeded training records JSON file.",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Optional candidate CSV to rank. If omitted, the seed set itself is ranked.",
    )
    parser.add_argument(
        "--json-out",
        default="outputs/seed_ranking_results.json",
        help="Output JSON path.",
    )
    parser.add_argument(
        "--report-out",
        default="outputs/seed_ranking_report.md",
        help="Output Markdown report path.",
    )
    args = parser.parse_args()

    seed_records = load_seed_records(args.seed)
    candidate_records = load_candidate_csv(args.input) if args.input else seed_records
    payload = rank_records(seed_records, candidate_records)
    write_json(args.json_out, payload)
    write_markdown(args.report_out, payload, args.input or args.seed)

    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report_out}")


if __name__ == "__main__":
    main()
