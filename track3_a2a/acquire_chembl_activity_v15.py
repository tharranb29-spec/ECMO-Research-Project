#!/usr/bin/env python3

"""Acquire a frozen ChEMBL evidence snapshot for exploratory v1.5 curation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import parse, request


ROOT = Path(__file__).resolve().parent
DEFAULT_COHORT = ROOT / "outputs" / "v1.3" / "docking_clean_computational.csv"
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "chembl251_activity_v15"
API = "https://www.ebi.ac.uk/chembl/api/data"
TARGET = "CHEMBL251"
USER_AGENT = "ZJU-ISM-A2A-Track3/1.5"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def fetch_json(url: str, attempts: int = 4) -> dict:
    last_error = None
    for attempt in range(attempts):
        try:
            req = request.Request(url, headers={"User-Agent": USER_AGENT})
            with request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"ChEMBL request failed: {url}: {last_error}")


def fetch_collection(resource: str, result_key: str, filters: dict[str, str]) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        query = parse.urlencode({**filters, "limit": 1000, "offset": offset})
        payload = fetch_json(f"{API}/{resource}.json?{query}")
        page = payload.get(result_key, [])
        rows.extend(page)
        meta = payload.get("page_meta", {})
        if not meta.get("next") or not page:
            break
        offset += len(page)
    return rows


def fetch_by_ids(resource: str, result_key: str, id_field: str, ids: list[str]) -> list[dict]:
    rows = []
    for batch in chunks(sorted(set(ids)), 40):
        rows.extend(fetch_collection(resource, result_key, {f"{id_field}__in": ",".join(batch)}))
    indexed = {str(row[id_field]): row for row in rows if row.get(id_field)}
    missing = sorted(set(ids) - set(indexed))
    if missing:
        raise RuntimeError(f"Missing {resource} metadata for: {missing}")
    return [indexed[key] for key in sorted(indexed)]


def load_cohort(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    ids = [row["molecule_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Cohort contains duplicate molecule_id values")
    return sorted(ids)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    output_paths = {
        "activities": args.output / "activities.json",
        "assays": args.output / "assays.json",
        "documents": args.output / "documents.json",
        "target": args.output / "target.json",
    }
    manifest_path = args.output / "acquisition_manifest.json"
    if all(path.exists() for path in output_paths.values()) and manifest_path.exists() and not args.refresh:
        print(manifest_path.read_text(encoding="utf-8"), end="")
        return
    else:
        molecule_ids = load_cohort(args.cohort)
        activities = []
        for batch in chunks(molecule_ids, 40):
            activities.extend(fetch_collection("activity", "activities", {
                "target_chembl_id": TARGET,
                "molecule_chembl_id__in": ",".join(batch),
            }))
        activities = sorted(
            {int(row["activity_id"]): row for row in activities if row.get("activity_id")}.values(),
            key=lambda row: int(row["activity_id"]),
        )
        assays = fetch_by_ids(
            "assay", "assays", "assay_chembl_id",
            [row["assay_chembl_id"] for row in activities if row.get("assay_chembl_id")],
        )
        documents = fetch_by_ids(
            "document", "documents", "document_chembl_id",
            [row["document_chembl_id"] for row in activities if row.get("document_chembl_id")],
        )
        target = fetch_json(f"{API}/target/{TARGET}.json")
        write_json(output_paths["activities"], activities)
        write_json(output_paths["assays"], assays)
        write_json(output_paths["documents"], documents)
        write_json(output_paths["target"], target)

    manifest = {
        "schema_version": 1,
        "specification_id": "a2a-continuous-activity-v1.5",
        "created_at": utc_now(),
        "source": "ChEMBL API",
        "target_chembl_id": TARGET,
        "cohort_path": str(args.cohort.relative_to(ROOT)),
        "cohort_sha256": sha256(args.cohort),
        "exploratory_only": True,
        "files": {},
    }
    for name, path in output_paths.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest["files"][name] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "records": len(payload) if isinstance(payload, list) else 1,
        }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
