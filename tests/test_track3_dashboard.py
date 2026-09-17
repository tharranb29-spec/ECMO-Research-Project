import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "track3_a2a" / "outputs" / "dashboard" / "v1" / "contracts.json"


def canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class Track3DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "build_track3_dashboard.py"], cwd=ROOT, check=True, capture_output=True)
        cls.payload = json.loads(OUTPUT.read_text(encoding="utf-8"))

    def test_contract_set_and_versions_are_complete(self):
        expected = {
            "evidence_inbox", "molecule_registry", "model_registry",
            "applicability_uncertainty", "dual_state_docking", "md_gates",
            "candidate_portfolio", "audit_log",
        }
        self.assertEqual(set(self.payload["contracts"]), expected)
        for contract in self.payload["contracts"].values():
            self.assertEqual(contract["contract_version"], "1.0.0")

    def test_source_hashes_match_repository_artifacts(self):
        a2a = ROOT / "track3_a2a"
        for contract in self.payload["contracts"].values():
            for record in contract["records"]:
                source = record["source"]
                digest = hashlib.sha256((a2a / source["path"]).read_bytes()).hexdigest()
                self.assertEqual(source["sha256"], digest)

    def test_autonomy_is_shadow_only_and_promotion_is_locked(self):
        promotion = self.payload["promotion"]
        self.assertEqual(promotion["mode"], "shadow_only")
        self.assertIsNone(promotion["served_model"])
        self.assertFalse(promotion["external_gate_passed"])
        self.assertFalse(promotion["human_release_approved"])
        self.assertFalse(promotion["automatic_model_replacement_enabled"])
        for candidate in self.payload["contracts"]["candidate_portfolio"]["records"]:
            self.assertEqual(candidate["promotion_status"], "shadow_proposal")

    def test_outcomes_and_tier_b_remain_locked(self):
        self.assertFalse(self.payload["summary"]["external_outcomes_loaded"])
        self.assertEqual(self.payload["summary"]["external_admitted"], 0)
        self.assertFalse(self.payload["summary"]["tier_b_unlocked"])
        self.assertEqual(self.payload["summary"]["md_runs_passed"], 5)
        self.assertEqual(self.payload["summary"]["md_runs_required"], 6)

    def test_docking_contract_is_dual_state_and_label_blind(self):
        docking = self.payload["contracts"]["dual_state_docking"]["records"]
        molecules = self.payload["contracts"]["molecule_registry"]["records"]
        self.assertEqual(len(docking), 8)
        self.assertEqual(len(molecules), 4)
        for molecule in molecules:
            self.assertTrue(molecule["functional_label_blinded"])
            self.assertFalse(molecule["training_eligible"])
            states = {row["receptor_state"] for row in docking if row["molecule_id"] == molecule["molecule_id"]}
            self.assertEqual(states, {"inactive", "active-like"})

    def test_audit_log_is_hash_chained(self):
        previous = "GENESIS"
        for entry in self.payload["contracts"]["audit_log"]["records"]:
            self.assertEqual(entry["previous_entry_hash"], previous)
            recorded = entry["entry_hash"]
            unhashed = {key: value for key, value in entry.items() if key != "entry_hash"}
            self.assertEqual(recorded, canonical_hash(unhashed))
            previous = recorded

    def test_ui_does_not_present_candidates_as_validated_hits(self):
        html = (ROOT / "track3-dashboard.html").read_text(encoding="utf-8").lower()
        js = (ROOT / "track3-dashboard.js").read_text(encoding="utf-8").lower()
        self.assertNotIn("validated hit", html)
        self.assertNotIn("validated hit", js)
        self.assertIn("shadow mode only", html)


if __name__ == "__main__":
    unittest.main()
