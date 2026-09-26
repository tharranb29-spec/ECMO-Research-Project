#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
TARGET = ROOT / "dashboard-data.js"
CONFIG = ROOT / "dashboard-config.json"


def ensure_render_rdkit():
    # The existing Render service uses this script in its build command. A
    # specific-commit deploy may not sync render.yaml first, so install the
    # pinned runtime dependency here as well. Local builds remain untouched.
    if os.environ.get("RENDER") != "true":
        return
    try:
        import rdkit
    except ImportError:
        installed = None
    else:
        installed = rdkit.__version__
    if installed != "2025.09.6":
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "rdkit==2025.9.6"], check=True)
        import rdkit
        if rdkit.__version__ != "2025.09.6":
            raise RuntimeError("Pinned RDKit installation failed.")


def load_json(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    ensure_render_rdkit()
    payload = {
        "config": load_json(CONFIG),
        "seed": load_json(OUTPUTS / "seed_ranking_results.json"),
        "custom": load_json(OUTPUTS / "custom_results.json"),
        "autonomous": load_json(OUTPUTS / "autonomous_ranking_results.json"),
        "autonomous_promoted": load_json(OUTPUTS / "autonomous_promoted_results.json"),
        "research_leads": load_json(OUTPUTS / "research_leads.json"),
        "research_status": load_json(OUTPUTS / "research_status.json"),
        "research_runtime": load_json(OUTPUTS / "research_runtime_status.json"),
        "gnina_results": load_json(OUTPUTS / "gnina_results.json"),
        "gnina_bridge_results": load_json(OUTPUTS / "gnina_bridge_results.json"),
        "gnina_status": load_json(OUTPUTS / "gnina_status.json"),
        "gnina_validation": load_json(OUTPUTS / "gnina_validation.json"),
        "a2a_curation": load_json(ROOT / "track3_a2a" / "outputs" / "v1.3" / "computational_curation_audit.json"),
        "a2a_partitions": load_json(ROOT / "track3_a2a" / "outputs" / "v1.3" / "computational_partition_audit.json"),
        "a2a_features": load_json(ROOT / "track3_a2a" / "outputs" / "v1.3" / "feature_construction_audit.json"),
        "a2a_confirmatory": load_json(ROOT / "track3_a2a" / "outputs" / "v1.3" / "confirmatory" / "holdout_report_v1.3.1.json"),
    }
    serialized = json.dumps(payload, indent=2)
    content = f"window.ECMO_DASHBOARD_DATA = {serialized};\n"
    TARGET.write_text(content, encoding="utf-8")
    print(f"Wrote {TARGET.name}")


if __name__ == "__main__":
    main()
