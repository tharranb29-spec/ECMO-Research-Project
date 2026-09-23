#!/usr/bin/env python3
"""Audit a bounded set of source access gaps without reading activity outcomes.

The frozen v1.6 cohort is read only. This script retrieves publication metadata,
never article text, supplementary content, or assay values. Its output is a new
shadow worklist for evidence review, not a new external-confirmation cohort.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PASS1 = ROOT / "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight.json"
PASS2 = ROOT / "outputs/v1.6/external_evidence/pass2_source_extraction/pass2_source_extraction.json"
OUTPUT = ROOT / "outputs/v1.6.1/shadow_evidence/source_access_sprint"
SNAPSHOT = OUTPUT / "publication_metadata_snapshot.json"
RELEASE = OUTPUT / "shadow_evidence_release.json"
LIMIT = 12


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_key(row: dict) -> str:
    pmid = str(row.get("pmid") or "").split("|")[0].strip()
    doi = str(row.get("doi") or "").split("|")[0].strip().lower()
    return f"PMID:{pmid}" if pmid else (f"DOI:{doi}" if doi else "")


def make_worklist(pass1: dict, pass2: dict) -> tuple[list[dict], list[dict]]:
    if pass1.get("outcome_fields_loaded") or pass2.get("outcome_fields_loaded") or pass2.get("numeric_ki_extracted"):
        raise RuntimeError("Outcome firewall violation in source packets")
    prior = {row["candidate_id"]: row for row in pass2["records"]}
    if len(prior) != len(pass2["records"]):
        raise RuntimeError("Duplicate candidate in frozen pass-2 packet")
    rows, groups = [], defaultdict(list)
    for row in pass1["records"]:
        candidate_id = row["candidate_id"]
        if candidate_id not in prior:
            raise RuntimeError(f"Missing pass-2 candidate: {candidate_id}")
        earlier = prior[candidate_id]
        if row["standardized_inchikey"] != earlier["standardized_inchikey"]:
            raise RuntimeError(f"Identity mismatch: {candidate_id}")
        key = source_key(row)
        reasons = list(earlier["quarantine_reasons"])
        item = {
            "candidate_id": candidate_id,
            "inchikey": row["standardized_inchikey"],
            "scaffold": row["generic_murcko_scaffold_smiles"],
            "source_key": key or None,
            "pass_1_status": row["pass_1_status"],
            "frozen_pass_2_reasons": reasons,
            "shadow_review_band": (
                "source_text_missing" if "retrieved_primary_full_text_unavailable" in reasons
                else "source_or_identity_unresolved" if any(reason.startswith("unresolved_") for reason in reasons)
                else "other_quarantine"
            ),
        }
        rows.append(item)
        if key and row["pass_1_status"].startswith("metadata_pass") and item["shadow_review_band"] == "source_text_missing":
            groups[key].append(candidate_id)
    rows.sort(key=lambda item: item["candidate_id"])
    publications = []
    for key, ids in groups.items():
        matches = [row for row in pass1["records"] if row["candidate_id"] in ids]
        publications.append({
            "source_key": key,
            "pmid": key.removeprefix("PMID:") if key.startswith("PMID:") else None,
            "doi": str(matches[0].get("doi") or "").split("|")[0].strip().lower() or None,
            "candidate_ids": sorted(ids),
            "affected_count": len(ids),
            "title_from_frozen_packet": str(matches[0].get("article_titles") or "").split("|")[0],
        })
    publications.sort(key=lambda item: (-item["affected_count"], item["source_key"]))
    return rows, publications


def fetch_publication(item: dict) -> dict:
    query = f"EXT_ID:{item['pmid']} AND SRC:MED" if item["pmid"] else f"DOI:{item['doi']}"
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({
        "query": query, "format": "json", "pageSize": "3", "resultType": "lite",
    })
    req = urllib.request.Request(url, headers={"User-Agent": "A2A-Track3-ShadowEvidence/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            payload = json.load(response)
    except (OSError, ValueError) as exc:
        return {"source_key": item["source_key"], "lookup_url": url, "status": "retrieval_failed", "error": str(exc)[:240]}
    results = (payload.get("resultList") or {}).get("result") or []
    matching = [row for row in results if (
        (item["pmid"] and str(row.get("pmid") or "") == item["pmid"])
        or (not item["pmid"] and str(row.get("doi") or "").lower() == item["doi"])
    )]
    if len(matching) != 1:
        return {"source_key": item["source_key"], "lookup_url": url, "status": "missing_or_ambiguous_match", "matched_count": len(matching)}
    row = matching[0]
    observed_doi = str(row.get("doi") or "").lower()
    if item["doi"] and observed_doi != item["doi"]:
        return {"source_key": item["source_key"], "lookup_url": url, "status": "doi_mismatch", "observed_doi": observed_doi}
    return {
        "source_key": item["source_key"], "lookup_url": url, "status": "metadata_verified",
        "pmid": row.get("pmid"), "doi": row.get("doi"), "pmcid": row.get("pmcid"),
        "title": row.get("title"), "publication_year": row.get("pubYear"),
        "in_pmc": row.get("inPMC") == "Y", "open_access": row.get("isOpenAccess") == "Y",
        "supplement_flag": row.get("hasSuppl") == "Y",
        "source_url": f"https://europepmc.org/article/{row.get('source', 'MED')}/{row.get('id')}",
    }


def title_target_flag(title: str) -> str:
    compact = re.sub(r"[^A-Z0-9]", "", (title or "").upper())
    if "A2A" not in compact and ("A2B" in compact or re.search(r"A1(?:ADENOSINE|RECEPTOR)", compact)):
        return "other_receptor_focus_in_title"
    return "a2a_or_unspecified_title"


def build_release(pass1: dict, pass2: dict, snapshot: dict) -> dict:
    rows, publications = make_worklist(pass1, pass2)
    selected = publications[:LIMIT]
    selected_keys = [item["source_key"] for item in selected]
    if snapshot.get("selected_source_keys") != selected_keys:
        raise RuntimeError("Snapshot selection differs from current frozen inputs")
    metadata = {item["source_key"]: item for item in snapshot["results"]}
    if set(metadata) != set(selected_keys):
        raise RuntimeError("Metadata snapshot is incomplete or contains unexpected sources")
    for item in selected:
        found = metadata[item["source_key"]]
        item["access_status"] = found["status"]
        item["open_access"] = found.get("open_access")
        item["in_pmc"] = found.get("in_pmc")
        item["supplement_flag"] = found.get("supplement_flag")
        item["source_url"] = found.get("source_url")
        item["title_target_flag"] = title_target_flag(found.get("title") or "") if found["status"] == "metadata_verified" else "unresolved"
        item["retrieval_note"] = (
            "Primary text and candidate-to-structure linkage still require independent review."
            if found["status"] == "metadata_verified" else "Publication metadata needs resolution."
        )
    return {
        "schema_version": 1,
        "release_id": "a2a-shadow-evidence-source-access-v1.6.1",
        "status": "shadow_worklist_only",
        "created_at_utc": snapshot["retrieved_at_utc"],
        "source_hashes": {"frozen_pass1": digest(PASS1), "frozen_pass2": digest(PASS2), "publication_metadata_snapshot": digest(SNAPSHOT)},
        "source_access_checked_at_utc": snapshot["retrieved_at_utc"],
        "selection_rule": f"Among frozen metadata-pass records lacking primary text, group by first PMID (DOI fallback), sort by affected candidate count descending then source key ascending, inspect first {LIMIT} groups.",
        "counts": {
            "frozen_candidate_records": len(rows), "publication_groups_with_missing_text": len(publications),
            "publication_groups_checked": len(selected),
            "affected_candidates_in_checked_groups": sum(item["affected_count"] for item in selected),
            "metadata_verified": sum(item["access_status"] == "metadata_verified" for item in selected),
            "open_access_metadata_flags": sum(item["open_access"] is True for item in selected),
            "supplement_metadata_flags": sum(item["supplement_flag"] is True for item in selected),
            "other_receptor_title_flags": sum(item["title_target_flag"] == "other_receptor_focus_in_title" for item in selected),
        },
        "review_bands": dict(sorted(Counter(item["shadow_review_band"] for item in rows).items())),
        "checked_publications": selected,
        "candidate_worklist": rows,
        "firewall": {"numeric_ki_extracted": False, "external_outcomes_loaded": False,
                     "frozen_membership_modified": False, "candidate_promoted": False},
        "claim_limit": "Metadata access checks do not resolve assay endpoints, exact compound rows, stereochemistry, or potency. Frozen external confirmation remains failed and closed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Retrieve only publication metadata for the selected source groups")
    args = parser.parse_args()
    pass1, pass2 = read(PASS1), read(PASS2)
    _, publications = make_worklist(pass1, pass2)
    selected = publications[:LIMIT]
    if args.refresh:
        snapshot = {
            "schema_version": 1, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "selection_rule_version": "affected-count-then-source-key-v1",
            "selected_source_keys": [item["source_key"] for item in selected],
            "results": [fetch_publication(item) for item in selected],
        }
        write(SNAPSHOT, snapshot)
    if not SNAPSHOT.exists():
        raise SystemExit("No metadata snapshot. Run once with --refresh.")
    release = build_release(pass1, pass2, read(SNAPSHOT))
    write(RELEASE, release)
    print(json.dumps({"release": str(RELEASE), "counts": release["counts"], "review_bands": release["review_bands"]}, indent=2))


if __name__ == "__main__":
    main()
