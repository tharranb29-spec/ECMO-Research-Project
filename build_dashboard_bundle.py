#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
TARGET = ROOT / "dashboard-data.js"
CONFIG = ROOT / "dashboard-config.json"


def load_json(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    payload = {
        "config": load_json(CONFIG),
        "seed": load_json(OUTPUTS / "seed_ranking_results.json"),
        "custom": load_json(OUTPUTS / "custom_results.json"),
        "autonomous": load_json(OUTPUTS / "autonomous_ranking_results.json"),
        "research_leads": load_json(OUTPUTS / "research_leads.json"),
        "research_status": load_json(OUTPUTS / "research_status.json"),
    }
    serialized = json.dumps(payload, indent=2)
    content = f"window.ECMO_DASHBOARD_DATA = {serialized};\n"
    TARGET.write_text(content, encoding="utf-8")
    print(f"Wrote {TARGET.name}")


if __name__ == "__main__":
    main()
