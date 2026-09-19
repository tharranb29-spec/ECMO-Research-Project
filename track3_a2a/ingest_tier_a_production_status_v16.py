#!/usr/bin/env python3
"""Validate live Tier A status artifacts and emit an auditable cutoff report."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from md_readiness_v16 import (
    DEFAULT_EQUILIBRATION_ROOT,
    DEFAULT_RELEASE_ROOT,
    GateError,
    PRODUCTION_CONFIG,
    atomic_json,
    load_json,
    sha256,
    tier_a_systems,
    verify_equilibration_gate,
    verify_release_bundle,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_production_cutoff" / "cutoff_status.json"
DEFAULT_MARKDOWN = ROOT / "outputs" / "v1.6" / "md" / "tier_a_production_cutoff" / "CUTOFF_STATUS.md"
SPECIFICATION_ID = "a2a-tier-a-production-cutoff-v1.6"
DASHBOARD_SCHEMA_ID = "a2a-dashboard.md-production-cutoff.v1"
IMMUTABLE_FIELDS = (
    "specification_id", "system_id", "replica", "seed",
    "production_config_sha256", "equilibration_gate_sha256",
    "equilibration_audit_sha256", "equilibrated_state_sha256",
    "release_archive_sha256", "target_steps", "target_ns",
)


class SnapshotError(ValueError):
    """Raised when an external status artifact fails the frozen contract."""


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise SnapshotError(f"{field} must be an ISO-8601 UTC timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SnapshotError(f"{field} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise SnapshotError(f"{field} must be UTC")
    return parsed


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SnapshotError(f"{field} must be an integer")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise SnapshotError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _run_identity(payload: dict[str, Any]) -> tuple[str, int]:
    return str(payload.get("system_id")), _integer(payload.get("replica"), "replica")


def _expected_provenance(system_id: str, replica: int) -> dict[str, Any]:
    config = load_json(PRODUCTION_CONFIG)
    systems = tier_a_systems(config)
    if system_id not in systems:
        raise SnapshotError(f"unknown Tier A system: {system_id}")
    if replica not in (1, 2, 3):
        raise SnapshotError("replica must be 1, 2, or 3")
    seed = config["tier_a"]["replica_seeds"][replica - 1]
    audit_path = DEFAULT_EQUILIBRATION_ROOT / system_id / f"seed-{seed}" / "equilibration_audit.json"
    audit = load_json(audit_path)
    release = verify_release_bundle(system_id, DEFAULT_RELEASE_ROOT)
    gate = verify_equilibration_gate(require_states=False)
    timestep_fs = float(config["integration_timestep_femtoseconds"])
    target_ns = float(config["tier_a"]["pilot_ns_per_replica"])
    return {
        "specification_id": config["specification_id"],
        "system_id": system_id,
        "replica": replica,
        "seed": seed,
        "production_config_sha256": sha256(PRODUCTION_CONFIG),
        "equilibration_gate_sha256": gate["equilibration_gate_sha256"],
        "equilibration_audit_sha256": sha256(audit_path),
        "equilibrated_state_sha256": audit["files"]["equilibrated_state.xml"],
        "release_archive_sha256": release["archive"]["sha256"],
        "target_steps": round(target_ns * 1_000_000 / timestep_fs),
        "target_ns": target_ns,
        "timestep_femtoseconds": timestep_fs,
        "state_interval_steps": round(float(config["state_interval_ps"]) * 1000 / timestep_fs),
        "checkpoint_interval_steps": round(float(config["checkpoint_interval_ps"]) * 1000 / timestep_fs),
    }


def _validate_common(payload: dict[str, Any], source: Path, artifact_type: str) -> dict[str, Any]:
    system_id, replica = _run_identity(payload)
    expected = _expected_provenance(system_id, replica)
    for field in IMMUTABLE_FIELDS:
        actual = payload.get(field)
        wanted = expected[field]
        if actual != wanted:
            raise SnapshotError(f"{source.name}: {field} mismatch: expected {wanted!r}, got {actual!r}")
    if payload.get("candidate_labels_loaded") is not False:
        raise SnapshotError(f"{source.name}: candidate label firewall is not explicit")
    if payload.get("trajectory_started") is not True:
        raise SnapshotError(f"{source.name}: artifact does not describe a started production trajectory")
    if payload.get("tier_b_unlocked") is not False:
        raise SnapshotError(f"{source.name}: Tier B must remain locked")
    if payload.get("platform") != "CUDA" or payload.get("platform_properties") != {"Precision": "mixed"}:
        raise SnapshotError(f"{source.name}: only CUDA mixed-precision production snapshots are accepted")
    current_step = _integer(payload.get("current_step"), "current_step")
    if current_step < 0 or current_step > expected["target_steps"]:
        raise SnapshotError(f"{source.name}: current_step is outside the frozen run bounds")
    completed_ns = current_step * expected["timestep_femtoseconds"] / 1_000_000
    if "completed_ns" in payload and not math.isclose(float(payload["completed_ns"]), completed_ns, abs_tol=1e-9):
        raise SnapshotError(f"{source.name}: completed_ns does not match current_step")
    updated = _timestamp(payload.get("updated_at_utc"), "updated_at_utc")
    checkpoint_step = current_step - (current_step % expected["checkpoint_interval_steps"])
    return {
        "artifact_type": artifact_type,
        "source_name": source.name,
        "source_sha256": sha256(source),
        "updated_at_utc": updated.isoformat().replace("+00:00", "Z"),
        "status": payload.get("status"),
        "system_id": system_id,
        "replica": replica,
        "seed": expected["seed"],
        "platform": "CUDA",
        "precision": "mixed",
        "current_step": current_step,
        "target_steps": expected["target_steps"],
        "reported_completed_ns": completed_ns,
        "target_ns": expected["target_ns"],
        "last_scheduled_checkpoint_step": checkpoint_step,
        "last_scheduled_checkpoint_ns": checkpoint_step * expected["timestep_femtoseconds"] / 1_000_000,
        "checkpoint_file_observed": False,
        "tier_b_unlocked": False,
        **{field: expected[field] for field in IMMUTABLE_FIELDS if field not in {"system_id", "replica", "seed", "target_steps", "target_ns"}},
    }


def validate_run_status(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    normalized = _validate_common(payload, path, "run_status")
    status = payload.get("status")
    if status not in {"running", "complete"}:
        raise SnapshotError(f"{path.name}: run_status must be running or complete")
    expected = _expected_provenance(normalized["system_id"], normalized["replica"])
    if normalized["current_step"] % expected["state_interval_steps"]:
        raise SnapshotError(f"{path.name}: current_step is not aligned to the 10 ps status cadence")
    if status == "running" and not 0 < normalized["current_step"] < normalized["target_steps"]:
        raise SnapshotError(f"{path.name}: running status requires partial positive progress")
    if status == "complete":
        if normalized["current_step"] != normalized["target_steps"]:
            raise SnapshotError(f"{path.name}: complete status requires target_steps")
        files = payload.get("files")
        required = {"trajectory.dcd", "state.csv", "final_state.xml", "restart.chk"}
        if not isinstance(files, dict) or set(files) != required:
            raise SnapshotError(f"{path.name}: complete status requires the four output hashes")
        for name, digest in files.items():
            _sha(digest, f"files.{name}")
        normalized["output_file_hashes"] = dict(sorted(files.items()))
    return normalized


def validate_failure_audit(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    normalized = _validate_common(payload, path, "failure_audit")
    if payload.get("status") != "technical_failure":
        raise SnapshotError(f"{path.name}: failure_audit must have technical_failure status")
    if payload.get("failed_replica_may_not_be_omitted") is not True:
        raise SnapshotError(f"{path.name}: failed-replica retention rule is missing")
    if not payload.get("error_type") or not isinstance(payload.get("error"), str):
        raise SnapshotError(f"{path.name}: failure details are incomplete")
    normalized["error_type"] = payload["error_type"]
    normalized["error"] = payload["error"]
    return normalized


def _validate_monotonic(snapshots: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for snapshot in snapshots:
        grouped[(snapshot["system_id"], snapshot["replica"])].append(snapshot)
    for key, rows in grouped.items():
        rows.sort(key=lambda row: (_timestamp(row["updated_at_utc"], "updated_at_utc"), row["source_sha256"]))
        terminal = False
        previous_step = -1
        previous_time = None
        immutable = None
        for row in rows:
            current_immutable = tuple(row[field] for field in IMMUTABLE_FIELDS if field in row)
            if immutable is None:
                immutable = current_immutable
            elif current_immutable != immutable:
                raise SnapshotError(f"immutable provenance changed within run {key}")
            if row["current_step"] < previous_step:
                raise SnapshotError(f"progress regressed within run {key}")
            if previous_time == row["updated_at_utc"]:
                raise SnapshotError(f"conflicting snapshots share a timestamp for run {key}")
            if terminal:
                raise SnapshotError(f"artifact follows a terminal status for run {key}")
            terminal = row["status"] in {"complete", "technical_failure"}
            previous_step = row["current_step"]
            previous_time = row["updated_at_utc"]


def _deduplicate(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_hash = {}
    for snapshot in snapshots:
        existing = by_hash.get(snapshot["source_sha256"])
        if existing is not None and existing != snapshot:
            raise SnapshotError("one source hash maps to conflicting normalized records")
        by_hash[snapshot["source_sha256"]] = snapshot
    return sorted(
        by_hash.values(),
        key=lambda row: (
            _timestamp(row["updated_at_utc"], "updated_at_utc"),
            row["system_id"], row["replica"], row["source_sha256"],
        ),
    )


def _validate_previous_snapshot(row: dict[str, Any]) -> None:
    if row.get("artifact_type") not in {"run_status", "failure_audit"}:
        raise SnapshotError("previous report contains an unsupported artifact type")
    _sha(row.get("source_sha256"), "source_sha256")
    parsed_time = _timestamp(row.get("updated_at_utc"), "updated_at_utc")
    if row.get("updated_at_utc") != parsed_time.isoformat().replace("+00:00", "Z"):
        raise SnapshotError("previous report timestamp is not canonical UTC")
    system_id, replica = _run_identity(row)
    expected = _expected_provenance(system_id, replica)
    for field in IMMUTABLE_FIELDS:
        actual = row.get(field)
        wanted = expected[field]
        if actual != wanted:
            raise SnapshotError(f"previous report has a {field} mismatch for {(system_id, replica)}")
    if row.get("platform") != "CUDA" or row.get("precision") != "mixed" or row.get("tier_b_unlocked") is not False:
        raise SnapshotError("previous report violates platform or Tier B lock semantics")
    current_step = _integer(row.get("current_step"), "current_step")
    if current_step < 0 or current_step > expected["target_steps"]:
        raise SnapshotError("previous report has invalid progress semantics")
    if row["artifact_type"] == "run_status" and current_step % expected["state_interval_steps"]:
        raise SnapshotError("previous run_status is not aligned to the status cadence")
    expected_ns = current_step * expected["timestep_femtoseconds"] / 1_000_000
    checkpoint_step = current_step - current_step % expected["checkpoint_interval_steps"]
    if not math.isclose(float(row.get("reported_completed_ns")), expected_ns, abs_tol=1e-9):
        raise SnapshotError("previous report has inconsistent completed ns")
    if row.get("last_scheduled_checkpoint_step") != checkpoint_step:
        raise SnapshotError("previous report has inconsistent checkpoint semantics")
    status = row.get("status")
    if status == "running" and not 0 < current_step < expected["target_steps"]:
        raise SnapshotError("previous running snapshot has invalid progress")
    if status == "complete" and current_step != expected["target_steps"]:
        raise SnapshotError("previous complete snapshot has invalid progress")
    if status not in {"running", "complete", "technical_failure"}:
        raise SnapshotError("previous report has an invalid status")


def build_cutoff(
    run_statuses: list[Path],
    failure_audits: list[Path],
    previous_report: Path | None = None,
) -> dict[str, Any]:
    snapshots = []
    if previous_report is not None:
        previous = load_json(previous_report)
        if previous.get("specification_id") != SPECIFICATION_ID:
            raise SnapshotError("previous report uses a different cutoff specification")
        previous_snapshots = previous.get("snapshots", [])
        if not isinstance(previous_snapshots, list):
            raise SnapshotError("previous report snapshots must be a list")
        for snapshot in previous_snapshots:
            _validate_previous_snapshot(snapshot)
        snapshots.extend(previous_snapshots)
    snapshots.extend(validate_run_status(path) for path in run_statuses)
    snapshots.extend(validate_failure_audit(path) for path in failure_audits)
    snapshots = _deduplicate(snapshots)
    if not snapshots:
        raise SnapshotError("at least one run_status or failure_audit is required")
    _validate_monotonic(snapshots)

    latest = {}
    for snapshot in snapshots:
        latest[(snapshot["system_id"], snapshot["replica"])] = snapshot
    current = list(latest.values())
    config = load_json(PRODUCTION_CONFIG)
    required_replicas = len(config["tier_a"]["systems"]) * len(config["tier_a"]["replica_seeds"])
    required_ns = required_replicas * float(config["tier_a"]["pilot_ns_per_replica"])
    completed = sum(row["status"] == "complete" for row in current)
    running = sum(row["status"] == "running" for row in current)
    failed = sum(row["status"] == "technical_failure" for row in current)
    observed_ns = sum(row["reported_completed_ns"] for row in current)
    completed_replica_ns = sum(row["reported_completed_ns"] for row in current if row["status"] == "complete")
    checkpoint_floor_ns = sum(row["last_scheduled_checkpoint_ns"] for row in current)
    gate = load_json(DEFAULT_EQUILIBRATION_ROOT / "equilibration_gate_report.json")
    cutoff_row = max(snapshots, key=lambda row: _timestamp(row["updated_at_utc"], "updated_at_utc"))
    cutoff = cutoff_row["updated_at_utc"]
    claim_limit = config["claim_limit"]
    production = {
        "status": "started_campaign_incomplete" if completed < required_replicas else "campaign_complete_pending_analysis",
        "required_replicas": required_replicas,
        "observed_replicas": len(current),
        "completed_replicas": completed,
        "running_replicas": running,
        "failed_replicas": failed,
        "not_observed_replicas": required_replicas - len(current),
        "required_ns": required_ns,
        "aggregate_reported_ns": round(observed_ns, 9),
        "aggregate_completed_replica_ns": round(completed_replica_ns, 9),
        "aggregate_last_scheduled_checkpoint_ns": round(checkpoint_floor_ns, 9),
        "completion_fraction_by_reported_ns": observed_ns / required_ns,
    }
    dashboard_record = {
        "cutoff_id": f"tier-a-production:{cutoff}",
        "status": production["status"],
        "equilibration_passed_runs": gate["passed_run_count"],
        "equilibration_required_runs": gate["expected_run_count"],
        **production,
        "tier_b_status": "not_executed_locked",
        "tier_b_executed_replicas": 0,
        "tier_b_unlocked": False,
        "model_training_status": "not_assessed_by_md_cutoff",
        "md_campaign_incomplete_does_not_imply_model_training_incomplete": True,
        "claim_limit": claim_limit,
    }
    return {
        "schema_version": 1,
        "specification_id": SPECIFICATION_ID,
        "cutoff_at_utc": cutoff,
        "equilibration": {
            "status": gate["status"],
            "passed_runs": gate["passed_run_count"],
            "required_runs": gate["expected_run_count"],
            "tier_a_production_unlocked": gate["tier_a_production_unlocked"],
            "source_sha256": sha256(DEFAULT_EQUILIBRATION_ROOT / "equilibration_gate_report.json"),
        },
        "tier_a_production": production,
        "tier_b": {"status": "not_executed_locked", "executed_replicas": 0, "tier_b_unlocked": False},
        "model_training_interpretation": {
            "status": "not_assessed_by_md_cutoff",
            "md_campaign_incomplete_does_not_imply_model_training_incomplete": True,
        },
        "claim_limit": claim_limit,
        "snapshots": snapshots,
        "dashboard_contract": {
            "schema_id": DASHBOARD_SCHEMA_ID,
            "contract_version": "1.0.0",
            "records": [dashboard_record],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    production = report["tier_a_production"]
    lines = [
        "# Tier A production cutoff status",
        "",
        f"**Cutoff:** {report['cutoff_at_utc']}",
        "",
        f"**Equilibration:** {report['equilibration']['passed_runs']}/{report['equilibration']['required_runs']} passed",
        "",
        "**Tier A production:** started; campaign incomplete",
        "",
        f"**Tier B:** not executed; locked",
        "",
        "## Exact cutoff totals",
        "",
        f"- Completed production replicas: {production['completed_replicas']}/{production['required_replicas']}",
        f"- Running replicas: {production['running_replicas']}",
        f"- Failed replicas: {production['failed_replicas']}",
        f"- Replicas not observed in the supplied cutoff artifacts: {production['not_observed_replicas']}",
        f"- Aggregate reported production: {production['aggregate_reported_ns']:.2f}/{production['required_ns']:.2f} ns",
        f"- Sampling in completed replicas: {production['aggregate_completed_replica_ns']:.2f}/{production['required_ns']:.2f} ns",
        f"- Last scheduled checkpoint floor represented by snapshots: {production['aggregate_last_scheduled_checkpoint_ns']:.2f} ns",
        "",
        "## Ingested replica snapshots",
        "",
        "| System | Replica | Seed | Status | Reported ns | Target ns | Scheduled checkpoint floor ns | Source SHA-256 |",
        "| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    latest = {}
    for row in report["snapshots"]:
        latest[(row["system_id"], row["replica"])] = row
    for key in sorted(latest):
        row = latest[key]
        lines.append(
            f"| {row['system_id']} | {row['replica']} | {row['seed']} | {row['status']} | "
            f"{row['reported_completed_ns']:.2f} | {row['target_ns']:.2f} | "
            f"{row['last_scheduled_checkpoint_ns']:.2f} | `{row['source_sha256']}` |"
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        report["claim_limit"],
        "",
        "This MD cutoff does not assess model-training status. An incomplete MD campaign must not be described as incomplete model training.",
        "",
        "A status snapshot establishes only what the hashed artifact reports, including scheduled checkpoint semantics; it does not prove that the checkpoint file itself was supplied. The binary trajectory, checkpoint, and state-data files were not ingested by this cutoff layer.",
        "",
    ])
    return "\n".join(lines)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-status", type=Path, action="append", default=[])
    parser.add_argument("--failure-audit", type=Path, action="append", default=[])
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        report = build_cutoff(args.run_status, args.failure_audit, args.previous_report)
    except (GateError, SnapshotError, FileNotFoundError, json.JSONDecodeError) as exc:
        raise SystemExit(f"REJECTED: {exc}") from exc
    if not args.check_only:
        atomic_json(args.output, report)
        atomic_text(args.markdown, render_markdown(report))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
