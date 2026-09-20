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
            "candidate_portfolio", "shadow_actions", "governance_scope",
            "uncertainty_review_queue", "md_production_cutoff", "audit_log",
        }
        self.assertEqual(set(self.payload["contracts"]), expected)
        for contract in self.payload["contracts"].values():
            self.assertEqual(contract["contract_version"], "1.0.0")
        runtime_schema = ROOT / "track3_a2a" / "dashboard_contracts" / "v1" / "discovery-run.schema.json"
        schema = json.loads(runtime_schema.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["governance"]["properties"]["autonomy_mode"]["const"], "shadow_only")
        self.assertIn("eligibility_contract", schema["properties"]["screen_eligible_queue"]["required"])

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
        self.assertFalse(self.payload["summary"]["outcome_join_authorized"])
        self.assertTrue(self.payload["summary"]["external_membership_frozen"])
        self.assertFalse(self.payload["summary"]["external_floors_passed"])
        self.assertEqual(self.payload["summary"]["external_admitted"], 0)
        self.assertEqual(self.payload["summary"]["external_scaffolds"], 0)
        self.assertFalse(self.payload["summary"]["tier_b_unlocked"])
        self.assertTrue(self.payload["summary"]["tier_a_production_unlocked"])
        self.assertEqual(self.payload["summary"]["md_runs_passed"], 6)
        self.assertEqual(self.payload["summary"]["md_runs_required"], 6)
        self.assertTrue(self.payload["summary"]["tier_a_production_started"])
        self.assertEqual(self.payload["summary"]["tier_a_production_observed_replicas"], 1)
        self.assertEqual(self.payload["summary"]["tier_a_production_completed_replicas"], 0)
        self.assertEqual(self.payload["summary"]["tier_a_production_reported_ns"], 5.92)
        self.assertEqual(self.payload["summary"]["uncertainty_queue_count"], 240)
        self.assertEqual(self.payload["summary"]["uncertainty_queue_eligible"], 0)

    def test_scope_and_uncertainty_queue_forbid_rank_and_probabilities(self):
        scope = self.payload["contracts"]["governance_scope"]["records"][0]
        queue = self.payload["contracts"]["uncertainty_review_queue"]["records"]
        self.assertFalse(scope["candidate_review"]["scientific_rank_allowed"])
        self.assertFalse(scope["candidate_review"]["candidate_probability_allowed"])
        self.assertFalse(scope["autonomy"]["model_promotion"])
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["candidate_count"], 240)
        self.assertEqual(queue[0]["validated_prediction_count"], 0)
        self.assertEqual(queue[0]["validated_interval_count"], 0)
        self.assertEqual(queue[0]["review_eligible_count"], 0)
        self.assertTrue(queue[0]["ranking_prohibited"])
        eligibility = dict(queue[0]["eligibility_contract"])
        expected = json.loads((ROOT / "track3_a2a/config/review_eligibility.v1.json").read_text())
        source = eligibility.pop("source")
        self.assertEqual(eligibility, expected)
        self.assertEqual(source["path"], "config/review_eligibility.v1.json")
        self.assertEqual(queue[0]["threshold_rule_semantics"], expected["artifact_projection"])
        self.assertTrue(all(value is False for value in expected["firewalls"].values()))

    def test_docking_contract_is_dual_state_and_label_blind(self):
        docking = self.payload["contracts"]["dual_state_docking"]["records"]
        molecules = self.payload["contracts"]["molecule_registry"]["records"]
        self.assertEqual(len(docking), 8)
        self.assertEqual(len(molecules), 6)
        candidates = [molecule for molecule in molecules if molecule["role"] == "label-blind prospective candidate"]
        self.assertEqual(len(candidates), 4)
        for molecule in candidates:
            self.assertTrue(molecule["functional_label_blinded"])
            self.assertFalse(molecule["training_eligible"])
            states = {row["receptor_state"] for row in docking if row["molecule_id"] == molecule["molecule_id"]}
            self.assertEqual(states, {"inactive", "active-like"})

    def test_shadow_actions_are_bounded_and_provenanced(self):
        actions = self.payload["contracts"]["shadow_actions"]["records"]
        self.assertEqual(len(actions), 7)
        prohibited = {item for action in actions for item in action["prohibited_actions"]}
        self.assertTrue({"read_sealed_outcomes", "promote_model", "start_tier_b", "release_candidate"} <= prohibited)
        for action in actions:
            self.assertTrue(action["authority"])
            self.assertTrue(action["required_gate"])
            self.assertIn("source", action)

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
        self.assertIn("shadow mode", html)
        self.assertIn("governed review queue", html)
        self.assertIn("eligibility.display_label", js)
        self.assertIn("molecule.eligibility_state", js)

    def test_information_architecture_covers_every_competition_workspace(self):
        html = (ROOT / "track3-dashboard.html").read_text(encoding="utf-8")
        expected_views = {
            "overview", "evidence", "molecules", "models", "applicability",
            "docking", "md", "portfolio", "discovery", "shadow", "audit",
        }
        for view in expected_views:
            self.assertIn(f'data-panel="{view}"', html)
            self.assertIn(f'data-view="{view}"', html)

    def test_application_server_and_render_blueprint_are_read_only_track3(self):
        server = (ROOT / "research_assistant_server.py").read_text(encoding="utf-8")
        blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
        self.assertIn('"/": ROOT / "track3-dashboard.html"', server)
        self.assertIn('"/track3-dashboard-data.js"', server)
        self.assertIn('"release": "a2a-track3-autonomous-deepseek-v4"', server)
        self.assertIn('"/api/discovery/run"', server)
        self.assertIn('"/api/discovery/disposition"', server)
        self.assertIn('AI_PROVIDER = "deepseek"', server)
        self.assertNotIn('call_openai_responses', server)
        self.assertIn('build_track3_dashboard.py', blueprint)
        self.assertIn('key: AI_PROVIDER\n        value: deepseek', blueprint)
        self.assertIn('key: DEEPSEEK_API_KEY\n        sync: false', blueprint)
        self.assertNotIn('OPENAI_API_KEY', blueprint)
        self.assertIn('key: AUTO_RESEARCH_ENABLED\n        value: "0"', blueprint)
        self.assertIn('key: AUTO_RESEARCH_LLM_ENABLED\n        value: "0"', blueprint)
        self.assertIn('key: GNINA_MODE\n        value: disabled', blueprint)


if __name__ == "__main__":
    unittest.main()
