#!/usr/bin/env python3
"""Build a non-ranked, outcome-blind uncertainty review queue.

The current audited candidate ledger is always projected.  A separately supplied
prediction artifact is accepted only when its schema, provenance hashes, interval
construction, threshold provenance, and outcome/docking firewalls all validate.
Any artifact-level error rejects the entire prediction intake.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "outputs" / "v1.6" / "external_evidence" / "pass1_metadata_preflight" / "pass1_metadata_preflight.json"
LEDGER_AUDIT = ROOT / "outputs" / "v1.6" / "external_evidence" / "pass1_metadata_preflight" / "pass1_metadata_preflight_audit.json"
PROTOCOL = ROOT / "config" / "protocol.v1.6.json"
ELIGIBILITY_CONTRACT_PATH = ROOT / "config" / "review_eligibility.v1.json"
DEFAULT_PREDICTIONS = ROOT / "outputs" / "v1.6" / "uncertainty_review_queue" / "source_predictions.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6" / "uncertainty_review_queue"

ELIGIBILITY_CONTRACT = json.loads(ELIGIBILITY_CONTRACT_PATH.read_text(encoding="utf-8"))

CLAIMED_SOURCE_COUNT = 335
CLAIMED_SCREEN_ELIGIBLE_COUNT = 276
CLAIMED_THRESHOLD = 6.7412
INTERVAL_LEVEL = ELIGIBILITY_CONTRACT["decision_rule"]["interval_level"]
SHIPMENT_FLOOR = 60

REQUIRED_PREDICTION_COLUMNS = [
    "candidate_id",
    "standardized_inchikey",
    "model_id",
    "model_artifact_path",
    "model_artifact_sha256",
    "prediction_code_path",
    "prediction_code_sha256",
    "prediction_pbind_ki",
    "interval_lower_90",
    "interval_upper_90",
    "interval_level",
    "interval_method",
    "interval_calibration_source_path",
    "interval_calibration_source_sha256",
    "applicability_status",
    "nearest_neighbor_similarity",
    "descriptor_distance",
    "threshold_pbind_ki",
    "threshold_operator",
    "threshold_source_path",
    "threshold_source_sha256",
    "threshold_derivation",
    "external_outcomes_loaded",
    "docking_used_for_selection",
]

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
APPLICABILITY_STATUSES = {"inside_domain", "outside_domain", "indeterminate"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(value: str) -> str:
    digest = hashlib.sha256(f"a2a-uncertainty-review-v1|{value}".encode()).hexdigest()
    return f"URQ-{digest[:16]}"


def parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"expected true/false, received {value!r}")
    return normalized == "true"


def parse_finite(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"expected finite number, received {value!r}")
    return parsed


def wilson_rate(numerator: int, denominator: int, confidence_level: float = 0.95) -> dict:
    if denominator == 0:
        return {
            "numerator": numerator,
            "denominator": denominator,
            "estimate": None,
            "confidence_level": confidence_level,
            "method": "Wilson score interval",
            "lower": None,
            "upper": None,
            "status": "not_estimable_zero_denominator",
        }
    z = 1.959963984540054
    p = numerator / denominator
    scale = 1 + z * z / denominator
    center = (p + z * z / (2 * denominator)) / scale
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * denominator)) / denominator) / scale
    return {
        "numerator": numerator,
        "denominator": denominator,
        "estimate": p,
        "confidence_level": confidence_level,
        "method": "Wilson score interval",
        "lower": max(0.0, center - half),
        "upper": min(1.0, center + half),
        "status": "estimated",
    }


def evidence_quality(status: str) -> str:
    return {
        "metadata_pass_fulltext_ready": "source_fulltext_ready",
        "metadata_pass_needs_fulltext": "primary_metadata_requires_fulltext",
        "metadata_pass_doi_only_needs_source_retrieval": "primary_locator_requires_retrieval",
        "metadata_pass_requires_endpoint_resolution": "endpoint_resolution_required",
        "quarantine_nonprimary_source": "quarantined_nonprimary_source",
        "quarantine_target_not_supported": "quarantined_target_not_supported",
    }.get(status, "unresolved")


def verified_repository_artifact(root: Path, relative: str, expected_hash: str) -> tuple[bool, str]:
    if not relative or Path(relative).is_absolute() or not SHA256_RE.fullmatch(expected_hash or ""):
        return False, "invalid_path_or_sha256"
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False, "path_outside_repository"
    if not path.is_file():
        return False, "artifact_missing"
    if sha256(path) != expected_hash:
        return False, "artifact_hash_mismatch"
    return True, "verified"


def validate_predictions(
    path: Path,
    ledger_by_id: dict[str, dict],
    repository_root: Path,
    expected_source_count: int = CLAIMED_SOURCE_COUNT,
) -> tuple[dict[str, dict], dict]:
    try:
        display_path = str(path.resolve().relative_to(repository_root.resolve()))
    except ValueError:
        display_path = str(path)
    result = {
        "path": display_path,
        "present": path.is_file(),
        "accepted": False,
        "errors": [],
        "required_columns": REQUIRED_PREDICTION_COLUMNS,
        "source_row_count": 0,
    }
    if not path.is_file():
        result["errors"].append("source_predictions_missing")
        return {}, result

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    result["source_row_count"] = len(rows)
    missing_columns = [name for name in REQUIRED_PREDICTION_COLUMNS if name not in columns]
    if missing_columns:
        result["errors"].append(f"missing_columns:{'|'.join(missing_columns)}")
        return {}, result
    if len(rows) != expected_source_count:
        result["errors"].append(f"source_count_mismatch:expected={expected_source_count}:observed={len(rows)}")

    seen: set[str] = set()
    parsed: dict[str, dict] = {}
    provenance_tuples = set()
    for index, raw_row in enumerate(rows, 2):
        row = {name: str(raw_row.get(name) or "").strip() for name in REQUIRED_PREDICTION_COLUMNS}
        candidate_id = row["candidate_id"].strip()
        prefix = f"row_{index}:{candidate_id or 'missing_candidate_id'}"
        if not candidate_id or candidate_id in seen:
            result["errors"].append(f"{prefix}:missing_or_duplicate_candidate_id")
            continue
        seen.add(candidate_id)
        ledger = ledger_by_id.get(candidate_id)
        if ledger is None:
            result["errors"].append(f"{prefix}:candidate_absent_from_audited_ledger")
            continue
        if row["standardized_inchikey"].strip() != ledger["standardized_inchikey"]:
            result["errors"].append(f"{prefix}:structure_identity_mismatch")
            continue
        try:
            point = parse_finite(row["prediction_pbind_ki"])
            lower = parse_finite(row["interval_lower_90"])
            upper = parse_finite(row["interval_upper_90"])
            level = parse_finite(row["interval_level"])
            threshold = parse_finite(row["threshold_pbind_ki"])
            similarity = parse_finite(row["nearest_neighbor_similarity"])
            distance = parse_finite(row["descriptor_distance"])
            outcomes_loaded = parse_bool(row["external_outcomes_loaded"])
            docking_used = parse_bool(row["docking_used_for_selection"])
        except ValueError as exc:
            result["errors"].append(f"{prefix}:{exc}")
            continue
        row_errors = []
        if not lower <= point <= upper:
            row_errors.append("interval_does_not_contain_point_prediction")
        if not math.isclose(level, INTERVAL_LEVEL, abs_tol=1e-12):
            row_errors.append("interval_level_must_equal_0.90")
        if not math.isclose(threshold, CLAIMED_THRESHOLD, abs_tol=1e-12):
            row_errors.append("threshold_value_mismatch")
        if row["threshold_operator"].strip() != ELIGIBILITY_CONTRACT["decision_rule"]["operator"]:
            row_errors.append("threshold_operator_must_be_greater_than_or_equal")
        if outcomes_loaded:
            row_errors.append("external_outcome_firewall_violation")
        if docking_used:
            row_errors.append("docking_selection_firewall_violation")
        applicability = row["applicability_status"].strip()
        if applicability not in APPLICABILITY_STATUSES:
            row_errors.append("invalid_applicability_status")
        if not 0.0 <= similarity <= 1.0:
            row_errors.append("nearest_neighbor_similarity_out_of_range")
        for path_column, hash_column in [
            ("model_artifact_path", "model_artifact_sha256"),
            ("prediction_code_path", "prediction_code_sha256"),
            ("interval_calibration_source_path", "interval_calibration_source_sha256"),
            ("threshold_source_path", "threshold_source_sha256"),
        ]:
            ok, reason = verified_repository_artifact(
                repository_root, row[path_column].strip(), row[hash_column].strip()
            )
            if not ok:
                row_errors.append(f"{path_column}:{reason}")
        if not row["interval_method"].strip():
            row_errors.append("interval_method_missing")
        if not row["threshold_derivation"].strip():
            row_errors.append("threshold_derivation_missing")
        if row_errors:
            result["errors"].extend(f"{prefix}:{error}" for error in row_errors)
            continue

        provenance_tuples.add((
            row["model_id"].strip(), row["model_artifact_sha256"].strip(),
            row["prediction_code_sha256"].strip(), row["interval_method"].strip(),
            row["interval_calibration_source_sha256"].strip(),
            row["threshold_source_sha256"].strip(), row["threshold_derivation"].strip(),
        ))
        interval_label = (
            "robust_threshold_support" if lower >= threshold
            else "screen_eligible_not_ruled_out" if upper >= threshold
            else "ruled_out_by_90pct_interval"
        )
        parsed[candidate_id] = {
            "model_id": row["model_id"].strip(),
            "prediction_pbind_ki": point,
            "interval_lower_90": lower,
            "interval_upper_90": upper,
            "interval_method": row["interval_method"].strip(),
            "threshold_pbind_ki": threshold,
            "threshold_source_path": row["threshold_source_path"].strip(),
            "threshold_source_sha256": row["threshold_source_sha256"].strip(),
            "interval_eligibility": interval_label,
            "applicability_status": applicability,
            "nearest_neighbor_similarity": similarity,
            "descriptor_distance": distance,
        }
    if len(provenance_tuples) > 1:
        result["errors"].append("artifact_contains_inconsistent_model_interval_or_threshold_provenance")
    if result["errors"]:
        return {}, result
    result["accepted"] = True
    result["sha256"] = sha256(path)
    return parsed, result


def record_for_dashboard(row: dict, prediction: dict | None, scaffold_count: int, ledger_hash: str) -> dict:
    quality = evidence_quality(row["pass_1_status"])
    reasons = []
    if prediction is None:
        eligibility = "blocked_missing_validated_prediction"
        reasons.append("validated_prediction_and_interval_unavailable")
    elif not row["pass_1_status"].startswith("metadata_pass"):
        eligibility = "ineligible_evidence_gate"
        reasons.append("pass_1_evidence_gate_not_passed")
    elif prediction["interval_eligibility"] == "ruled_out_by_90pct_interval":
        eligibility = "ineligible_interval_upper_below_threshold"
        reasons.append("upper_90_below_threshold")
    else:
        eligibility = "eligible_for_human_review"
        reasons.append("upper_90_meets_threshold_and_evidence_preflight_passed")
        if prediction["applicability_status"] != "inside_domain":
            reasons.append("applicability_caution")

    interval = None if prediction is None else {
        "level": INTERVAL_LEVEL,
        "lower": prediction["interval_lower_90"],
        "upper": prediction["interval_upper_90"],
        "method": prediction["interval_method"],
    }
    return {
        "review_record_id": stable_id(row["candidate_id"]),
        "candidate_id": row["candidate_id"],
        "standardized_inchikey": row["standardized_inchikey"],
        "generic_murcko_scaffold_smiles": row["generic_murcko_scaffold_smiles"] or "ACYCLIC",
        "scaffold_member_count": scaffold_count,
        "scaffold_composition": "singleton" if scaffold_count == 1 else "multi_member",
        "evidence_quality": quality,
        "pass_1_status": row["pass_1_status"],
        "source_prediction_status": "validated" if prediction else "unavailable_or_rejected",
        "model_id": prediction["model_id"] if prediction else None,
        "prediction_pbind_ki": prediction["prediction_pbind_ki"] if prediction else None,
        "interval_90": interval,
        "threshold_pbind_ki": prediction["threshold_pbind_ki"] if prediction else None,
        "threshold_provenance_status": "verified" if prediction else "missing_or_rejected",
        "interval_eligibility": prediction["interval_eligibility"] if prediction else "not_assessed",
        "applicability_status": prediction["applicability_status"] if prediction else "not_assessed",
        "nearest_neighbor_similarity": prediction["nearest_neighbor_similarity"] if prediction else None,
        "descriptor_distance": prediction["descriptor_distance"] if prediction else None,
        "deterministic_review_eligibility": eligibility,
        "eligibility_reasons": reasons,
        "human_disposition": {
            "status": "not_started_upstream_blocked" if prediction is None else "unreviewed",
            "decision": None,
            "reviewer": None,
            "decided_at_utc": None,
            "notes": None,
        },
        "source": {
            "ledger": str(LEDGER.relative_to(ROOT)),
            "ledger_sha256": ledger_hash,
        },
    }


def write_csv(path: Path, records: list[dict]) -> None:
    fields = [
        "review_record_id", "candidate_id", "standardized_inchikey",
        "generic_murcko_scaffold_smiles", "scaffold_member_count", "scaffold_composition",
        "evidence_quality", "pass_1_status", "source_prediction_status", "model_id",
        "prediction_pbind_ki", "interval_lower_90", "interval_upper_90",
        "threshold_pbind_ki", "threshold_provenance_status", "interval_eligibility",
        "applicability_status", "nearest_neighbor_similarity", "descriptor_distance",
        "deterministic_review_eligibility", "eligibility_reasons", "human_disposition_status",
        "human_decision", "human_reviewer", "human_notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in records:
            interval = record["interval_90"] or {}
            disposition = record["human_disposition"]
            writer.writerow({
                **{field: record.get(field, "") for field in fields},
                "interval_lower_90": interval.get("lower", ""),
                "interval_upper_90": interval.get("upper", ""),
                "eligibility_reasons": "|".join(record["eligibility_reasons"]),
                "human_disposition_status": disposition["status"],
                "human_decision": disposition["decision"] or "",
                "human_reviewer": disposition["reviewer"] or "",
                "human_notes": disposition["notes"] or "",
            })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    ledger_packet = json.loads(LEDGER.read_text(encoding="utf-8"))
    ledger_audit = json.loads(LEDGER_AUDIT.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if ledger_packet.get("outcome_fields_loaded") or ledger_audit.get("outcome_fields_loaded"):
        raise RuntimeError("outcome firewall violation in audited candidate ledger")
    rows = ledger_packet["records"]
    ledger_by_id = {row["candidate_id"]: row for row in rows}
    if len(ledger_by_id) != len(rows):
        raise RuntimeError("duplicate candidate ID in audited candidate ledger")

    predictions, intake = validate_predictions(args.predictions, ledger_by_id, ROOT.parent)
    scaffold_counts = Counter(row["generic_murcko_scaffold_smiles"] or "ACYCLIC" for row in rows)
    ledger_hash = sha256(LEDGER)
    records = [
        record_for_dashboard(row, predictions.get(row["candidate_id"]), scaffold_counts[row["generic_murcko_scaffold_smiles"] or "ACYCLIC"], ledger_hash)
        for row in sorted(rows, key=lambda item: item["candidate_id"])
    ]
    eligible = [record for record in records if record["deterministic_review_eligibility"] == "eligible_for_human_review"]
    valid_predictions = [record for record in records if record["source_prediction_status"] == "validated"]
    screen_supported = [record for record in valid_predictions if record["interval_eligibility"] in {"screen_eligible_not_ruled_out", "robust_threshold_support"}]
    robust_supported = [record for record in valid_predictions if record["interval_eligibility"] == "robust_threshold_support"]
    inside_domain = [record for record in valid_predictions if record["applicability_status"] == "inside_domain"]
    fulltext_ready = [record for record in records if record["evidence_quality"] == "source_fulltext_ready"]
    singleton = [record for record in records if record["scaffold_composition"] == "singleton"]

    args.output.mkdir(parents=True, exist_ok=True)
    json_path = args.output / "uncertainty_review_queue.json"
    csv_path = args.output / "uncertainty_review_queue.csv"
    audit_path = args.output / "uncertainty_review_queue_audit.json"
    payload = {
        "schema_id": "a2a-dashboard.uncertainty-review-queue.v1",
        "contract_version": "1.0.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready" if intake["accepted"] else "fail_closed_prediction_intake",
        "ranking_prohibited": True,
        "per_molecule_hit_probabilities_present": False,
        "external_outcomes_loaded": False,
        "docking_used_for_selection": False,
        "threshold_rule_semantics": {
            **ELIGIBILITY_CONTRACT["artifact_projection"],
        },
        "records": records,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_csv(csv_path, records)

    external = protocol["external_confirmation"]
    audit = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-uncertainty-aware-review-queue-v1",
        "status": payload["status"],
        "source_prediction_intake": intake,
        "unverified_teammate_claims": {
            "source_candidate_count": CLAIMED_SOURCE_COUNT,
            "screen_eligible_count": CLAIMED_SCREEN_ELIGIBLE_COUNT,
            "threshold_pbind_ki": CLAIMED_THRESHOLD,
            "verified": bool(
                intake["accepted"]
                and intake["source_row_count"] == CLAIMED_SOURCE_COUNT
                and len(screen_supported) == CLAIMED_SCREEN_ELIGIBLE_COUNT
            ),
            "rule_used_by_teammate": "not_determinable_without_source_artifact",
        },
        "audited_candidate_count": len(records),
        "generic_murcko_scaffold_count": len(scaffold_counts),
        "review_shipment": {
            "operational_minimum": SHIPMENT_FLOOR,
            "eligible_count": len(eligible),
            "minimum_met": len(eligible) >= SHIPMENT_FLOOR,
            "purpose": "human review workload shipment only",
        },
        "external_confirmation_floor": {
            "minimum_molecules": protocol["endpoints"]["primary"]["minimum_records_for_external_evaluation"],
            "minimum_generic_murcko_scaffolds": protocol["endpoints"]["primary"]["minimum_generic_murcko_scaffolds"],
            "independent_outcomes_required": True,
            "membership_freeze_before_outcome_join": external["membership_freeze_before_outcome_join"],
            "not_satisfied_by_review_shipment": True,
        },
        "set_level_rates": {
            "source_prediction_coverage": wilson_rate(len(valid_predictions), len(records)),
            "screen_eligible_not_ruled_out_among_valid_predictions": wilson_rate(len(screen_supported), len(valid_predictions)),
            "robust_threshold_support_among_valid_predictions": wilson_rate(len(robust_supported), len(valid_predictions)),
            "inside_domain_among_valid_predictions": wilson_rate(len(inside_domain), len(valid_predictions)),
            "fulltext_ready_evidence": wilson_rate(len(fulltext_ready), len(records)),
            "singleton_scaffold_composition": wilson_rate(len(singleton), len(records)),
            "eligible_for_human_review": wilson_rate(len(eligible), len(records)),
        },
        "governance": {
            "ordinal_ranking_present": False,
            "per_position_reporting_present": False,
            "per_molecule_hit_probability_present": False,
            "docking_used_for_selection": False,
            "external_outcomes_loaded": False,
            "all_candidate_records_retained_without_rank": True,
        },
        "source_hashes": {
            str(LEDGER.relative_to(ROOT)): ledger_hash,
            str(LEDGER_AUDIT.relative_to(ROOT)): sha256(LEDGER_AUDIT),
            str(PROTOCOL.relative_to(ROOT)): sha256(PROTOCOL),
        },
        "artifact_hashes": {
            str(json_path.relative_to(ROOT)): sha256(json_path),
            str(csv_path.relative_to(ROOT)): sha256(csv_path),
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
