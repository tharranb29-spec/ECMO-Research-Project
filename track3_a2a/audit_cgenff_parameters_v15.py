#!/usr/bin/env python3

"""Audit returned CGenFF stream files against the frozen v1.5 requests."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUESTS = ROOT / "outputs" / "v1.5" / "md" / "cgenff_requests" / "request_manifest.json"
DEFAULT_INPUT = ROOT / "outputs" / "v1.5" / "md" / "cgenff_parameters"
DEFAULT_OUTPUT = DEFAULT_INPUT / "parameter_audit.json"
PENALTY_RE = re.compile(r"penalty\s*=\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
RESI_RE = re.compile(r"^\s*RESI\s+(\S+)\s+([-+]?[0-9]+(?:\.[0-9]+)?)", re.MULTILINE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sensitivity-review", type=Path)
    args = parser.parse_args()
    manifest = json.loads(REQUESTS.read_text(encoding="utf-8"))
    results = []
    blockers = []
    reviews = []
    for entry in manifest["entries"]:
        residue = entry["residue_name"]
        matches = sorted(args.input_dir.glob(f"{residue}*.str")) if args.input_dir.exists() else []
        if len(matches) != 1:
            reason = "missing_stream_file" if not matches else "ambiguous_stream_files"
            blockers.append({"residue_name": residue, "reason": reason, "matches": [p.name for p in matches]})
            results.append({"residue_name": residue, "status": reason})
            continue
        path = matches[0]
        text = path.read_text(encoding="utf-8", errors="replace")
        penalties = [float(value) for value in PENALTY_RE.findall(text)]
        resi = RESI_RE.search(text)
        returned_charge = float(resi.group(2)) if resi else None
        expected_charge = float(entry["expected_formal_charge"])
        max_penalty = max(penalties) if penalties else None
        item = {
            "residue_name": residue,
            "stream_file": path.name,
            "sha256": sha256(path),
            "expected_net_charge": expected_charge,
            "returned_net_charge": returned_charge,
            "penalty_count": len(penalties),
            "maximum_reported_penalty": max_penalty,
        }
        if returned_charge is None:
            blockers.append({"residue_name": residue, "reason": "resi_net_charge_not_found"})
            item["status"] = "blocked"
        elif abs(returned_charge - expected_charge) > 0.01:
            blockers.append({"residue_name": residue, "reason": "net_charge_mismatch"})
            item["status"] = "blocked"
        elif not penalties:
            blockers.append({"residue_name": residue, "reason": "no_cgenff_penalties_found"})
            item["status"] = "blocked"
        elif max_penalty > 50:
            blockers.append({"residue_name": residue, "reason": "penalty_above_50", "maximum": max_penalty})
            item["status"] = "blocked"
        elif max_penalty >= 10:
            reviews.append({"residue_name": residue, "reason": "penalty_10_through_50", "maximum": max_penalty})
            item["status"] = "human_review_required"
        else:
            item["status"] = "accepted"
        results.append(item)
    sensitivity = {}
    if args.sensitivity_review and args.sensitivity_review.is_file():
        sensitivity = json.loads(args.sensitivity_review.read_text(encoding="utf-8"))
    approved = set(sensitivity.get("approved_residue_names", [])) if sensitivity.get("status") == "computational_sensitivity_passed" else set()
    unresolved_reviews = [row for row in reviews if row["residue_name"] not in approved]
    if blockers:
        status = "blocked_or_parameters_pending"
    elif unresolved_reviews:
        status = "computational_parameter_sensitivity_required"
    else:
        status = "all_ligand_parameters_audited_and_accepted"
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "candidate_labels_loaded": False,
        "request_manifest_sha256": sha256(REQUESTS),
        "results": results,
        "computational_sensitivity_reviews_required": unresolved_reviews,
        "computational_sensitivity_review": sensitivity,
        "blockers": blockers,
        "production_parameter_gate_passed": status == "all_ligand_parameters_audited_and_accepted",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
