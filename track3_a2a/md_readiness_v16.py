#!/usr/bin/env python3
"""Shared fail-closed validation for the v1.6 MD production boundary."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PRODUCTION_CONFIG = ROOT / "config" / "md_production.v1.6.json"
EQUILIBRATION_CONFIG = ROOT / "config" / "tier_a_equilibration.v1.6.4.json"
DEFAULT_EQUILIBRATION_ROOT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_equilibration"
DEFAULT_RELEASE_ROOT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_release_bundles"


class GateError(RuntimeError):
    """Raised when a prospective MD action is still locked."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def tier_a_systems(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["system_id"]: row for row in config["tier_a"]["systems"]}


def verify_release_bundle(system_id: str, release_root: Path = DEFAULT_RELEASE_ROOT) -> dict[str, Any]:
    manifest_path = release_root / f"{system_id}.manifest.json"
    archive_path = release_root / f"{system_id}.tar.gz"
    if not manifest_path.is_file() or not archive_path.is_file():
        raise GateError(f"missing signed release bundle for {system_id}")
    manifest = load_json(manifest_path)
    if manifest.get("specification_id") != "a2a-tier-a-release-bundle-v1.6":
        raise GateError(f"unexpected release specification for {system_id}")
    if manifest.get("system_id") != system_id or manifest.get("status") != "accepted_for_staged_equilibration":
        raise GateError(f"release bundle is not accepted for {system_id}")
    if manifest.get("candidate_labels_loaded") is not False or manifest.get("production_trajectory_started") is not False:
        raise GateError(f"release bundle provenance flags are unsafe for {system_id}")
    archive = manifest.get("archive", {})
    if sha256(archive_path) != archive.get("sha256") or archive_path.stat().st_size != archive.get("size_bytes"):
        raise GateError(f"release archive hash or size mismatch for {system_id}")
    return manifest


def materialize_release_bundle(system_id: str, destination: Path, release_root: Path = DEFAULT_RELEASE_ROOT) -> Path:
    manifest = verify_release_bundle(system_id, release_root)
    archive_path = release_root / f"{system_id}.tar.gz"
    destination = destination / system_id
    destination.mkdir(parents=True, exist_ok=True)
    required = set(manifest["members_sha256"]) | {"bundle_manifest.json"}
    with tarfile.open(archive_path, "r:gz") as archive:
        names = set(archive.getnames())
        if not required.issubset(names):
            raise GateError(f"release archive is incomplete for {system_id}")
        if any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise GateError(f"release archive has an unsafe member for {system_id}")
        for name in required:
            member = archive.getmember(name)
            handle = archive.extractfile(member)
            if not member.isfile() or handle is None:
                raise GateError(f"invalid release member {system_id}/{name}")
            (destination / name).write_bytes(handle.read())
    for name, expected in manifest["members_sha256"].items():
        if sha256(destination / name) != expected:
            raise GateError(f"release member hash mismatch: {system_id}/{name}")
    embedded = load_json(destination / "bundle_manifest.json")
    for key in ("specification_id", "system_id", "status", "members_sha256"):
        if embedded.get(key) != manifest.get(key):
            raise GateError(f"embedded/repository manifest mismatch for {system_id}: {key}")
    return destination


def verify_equilibration_gate(
    equilibration_root: Path = DEFAULT_EQUILIBRATION_ROOT,
    release_root: Path = DEFAULT_RELEASE_ROOT,
    require_states: bool = True,
) -> dict[str, Any]:
    config = load_json(PRODUCTION_CONFIG)
    equil_config = load_json(EQUILIBRATION_CONFIG)
    gate_path = equilibration_root / "equilibration_gate_report.json"
    if not gate_path.is_file():
        raise GateError("aggregate Tier A equilibration gate report is missing")
    gate = load_json(gate_path)
    start_gate = config["tier_a"]["start_gate"]
    if gate.get("specification_id") != "a2a-tier-a-equilibration-gate-v1.6.4":
        raise GateError("aggregate equilibration gate has the wrong specification")
    if gate.get("status") != start_gate["required_equilibration_gate_status"]:
        raise GateError(f"Tier A production locked by aggregate equilibration status: {gate.get('status')}")
    if gate.get("tier_a_production_unlocked") is not True or gate.get("tier_b_unlocked") is not False:
        raise GateError("aggregate equilibration gate has inconsistent lock flags")
    required_runs = int(start_gate["required_equilibration_run_count"])
    required_passes = int(start_gate["required_equilibration_pass_count"])
    if gate.get("expected_run_count") != required_runs or gate.get("observed_run_count") != required_runs:
        raise GateError("all six equilibration audits are required before Tier A production")
    if gate.get("passed_run_count") != required_passes or gate.get("missing_audits"):
        raise GateError("all six equilibration audits must pass without omissions")
    expected_config_hash = sha256(EQUILIBRATION_CONFIG)
    if gate.get("config_sha256") != expected_config_hash:
        raise GateError("aggregate equilibration gate does not match the frozen v1.6.4 config")

    systems = tier_a_systems(config)
    expected = {(system_id, seed) for system_id in systems for seed in config["tier_a"]["replica_seeds"]}
    observed: set[tuple[str, int]] = set()
    verified_runs = []
    for row in gate.get("runs", []):
        system_id, seed = row.get("system_id"), row.get("seed")
        key = (system_id, seed)
        if key not in expected or key in observed:
            raise GateError(f"unexpected or duplicate equilibration run: {key}")
        observed.add(key)
        relative = Path(str(row.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise GateError(f"unsafe equilibration audit path: {relative}")
        audit_path = equilibration_root / relative
        if not audit_path.is_file() or sha256(audit_path) != row.get("sha256"):
            raise GateError(f"equilibration audit missing or hash mismatch: {relative}")
        audit = load_json(audit_path)
        release = verify_release_bundle(system_id, release_root)
        if audit.get("specification_id") != equil_config["specification_id"]:
            raise GateError(f"equilibration specification mismatch: {relative}")
        if audit.get("status") != "equilibration_gate_passed" or audit.get("scale") != 1.0:
            raise GateError(f"equilibration run did not pass at full duration: {relative}")
        if audit.get("system_id") != system_id or audit.get("seed") != seed:
            raise GateError(f"equilibration identity mismatch: {relative}")
        if audit.get("config_sha256") != expected_config_hash or row.get("config_sha256") != expected_config_hash:
            raise GateError(f"equilibration config hash mismatch: {relative}")
        members = release["members_sha256"]
        if audit.get("source_system_sha256") != members["system.xml"]:
            raise GateError(f"equilibration system provenance mismatch: {relative}")
        if audit.get("source_smoke_state_sha256") != members["smoke_final_state.xml"]:
            raise GateError(f"equilibration state provenance mismatch: {relative}")
        state_path = audit_path.parent / "equilibrated_state.xml"
        if require_states and (not state_path.is_file() or sha256(state_path) != audit.get("files", {}).get("equilibrated_state.xml")):
            raise GateError(f"equilibrated state missing or hash mismatch: {state_path}")
        verified_runs.append({"system_id": system_id, "seed": seed, "audit_path": str(audit_path), "state_path": str(state_path)})
    if observed != expected:
        raise GateError(f"equilibration run set is incomplete: missing {sorted(expected - observed)}")
    return {
        "status": "tier_a_production_preflight_passed",
        "production_config_sha256": sha256(PRODUCTION_CONFIG),
        "equilibration_config_sha256": expected_config_hash,
        "equilibration_gate_sha256": sha256(gate_path),
        "verified_runs": verified_runs,
    }


def verify_tier_a_control_gate(control_gate_path: Path) -> dict[str, Any]:
    config = load_json(PRODUCTION_CONFIG)
    if not control_gate_path.is_file():
        raise GateError("Tier A production control-gate report is missing")
    gate = load_json(control_gate_path)
    if gate.get("specification_id") != config["specification_id"]:
        raise GateError("Tier A control gate uses the wrong production specification")
    if gate.get("status") != "both_tier_a_controls_passed" or gate.get("tier_b_unlocked") is not True:
        raise GateError("Tier B remains locked until both Tier A controls pass")
    if gate.get("candidate_labels_loaded") is not False:
        raise GateError("Tier A control gate violated the label firewall")
    expected = set(tier_a_systems(config))
    rows = gate.get("systems", [])
    if {row.get("system_id") for row in rows} != expected:
        raise GateError("Tier A control gate has an incomplete system set")
    required = config["tier_a"]["analysis_gate"]["required_passing_replicas_per_control"]
    for row in rows:
        replicas = row.get("replicas", [])
        if len(replicas) != 3 or {item.get("replica") for item in replicas} != {1, 2, 3}:
            raise GateError(f"all three replicas must be reported for {row.get('system_id')}")
        if row.get("passed_replica_count", 0) < required or row.get("passed") is not True:
            raise GateError(f"Tier A control did not pass 2/3: {row.get('system_id')}")
    return gate
