#!/usr/bin/env python3
"""Create deterministic, GitHub-safe Tier A control bundles."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PERIODIC = ROOT / "outputs" / "v1.6" / "md" / "tier_a_periodic_systems"
SMOKE = ROOT / "outputs" / "v1.6" / "md" / "tier_a_smoke_tests"
OUTPUT = ROOT / "outputs" / "v1.6" / "md" / "tier_a_release_bundles"
SYSTEMS = ["5NM4_ZMA_native", "5G53_NECA_miniGs_native_nucleotide_free"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tar_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mtime = 0
    info.mode = 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def build(system_id: str) -> dict:
    periodic = PERIODIC / system_id
    smoke = SMOKE / system_id
    sources = {
        "system.xml": periodic / "system.xml",
        "positions.pdb": periodic / "positions.pdb",
        "native_contacts.json": periodic / "native_contacts.json",
        "assembly_audit.json": periodic / "assembly_audit.json",
        "smoke_final_state.xml": smoke / "smoke_final_state.xml",
        "smoke_audit.json": smoke / "smoke_audit.json",
    }
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Tier A inputs: " + ", ".join(missing))
    member_hashes = {name: sha256_bytes(path.read_bytes()) for name, path in sources.items()}
    manifest = {
        "schema_version": 1,
        "specification_id": "a2a-tier-a-release-bundle-v1.6",
        "system_id": system_id,
        "status": "accepted_for_staged_equilibration",
        "candidate_labels_loaded": False,
        "production_trajectory_started": False,
        "members_sha256": member_hashes,
    }
    members = {name: path.read_bytes() for name, path in sources.items()}
    members["bundle_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    archive = OUTPUT / f"{system_id}.tar.gz"
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as tar:
                for name in sorted(members):
                    data = members[name]
                    tar.addfile(tar_info(name, len(data)), io.BytesIO(data))
    manifest["archive"] = {
        "path": str(archive.relative_to(ROOT)),
        "size_bytes": archive.stat().st_size,
        "sha256": sha256_bytes(archive.read_bytes()),
    }
    (OUTPUT / f"{system_id}.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    systems = [build(system_id) for system_id in SYSTEMS]
    campaign = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "specification_id": "a2a-tier-a-release-campaign-v1.6",
        "systems": systems,
        "accepted_count": len(systems),
        "status": "all_tier_a_release_bundles_accepted",
        "claim_limit": "Bundles are accepted for staged equilibration only; Tier A production and Tier B remain locked.",
    }
    (OUTPUT / "campaign_manifest.json").write_text(json.dumps(campaign, indent=2) + "\n")
    print(json.dumps(campaign, indent=2))


if __name__ == "__main__":
    main()
