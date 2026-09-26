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
            "shadow_evidence_sprint",
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

    def test_shadow_evidence_sprint_is_metadata_only(self):
        sprint = self.payload["contracts"]["shadow_evidence_sprint"]["records"][0]
        self.assertEqual(sprint["status"], "shadow_worklist_only")
        self.assertEqual(sprint["counts"]["frozen_candidate_records"], 240)
        self.assertEqual(sprint["counts"]["publication_groups_checked"], 12)
        self.assertEqual(sprint["counts"]["metadata_verified"], 12)
        self.assertFalse(any(sprint["firewall"].values()))
        self.assertTrue(all(item["access_status"] == "metadata_verified" for item in sprint["checked_publications"]))
        self.assertEqual(len(sprint["source_grounded_review"]), 29)
        self.assertTrue(all(item["status"] == "shadow_review_required" for item in sprint["source_grounded_review"]))
        html = (ROOT / "track3-dashboard.html").read_text(encoding="utf-8")
        js = (ROOT / "track3-dashboard.js").read_text(encoding="utf-8")
        self.assertIn('id="review-packet-search"', html)
        self.assertIn('id="review-packet-list"', html)
        self.assertIn("sprint.source_grounded_review", js)
        self.assertIn("Frozen external cohort unchanged", js)

    def test_autonomy_is_shadow_only_and_promotion_is_locked(self):
        promotion = self.payload["promotion"]
        self.assertEqual(promotion["mode"], "shadow_only")
        self.assertIsNone(promotion["served_model"])
        self.assertFalse(promotion["external_gate_passed"])
        self.assertFalse(promotion["human_release_approved"])
        self.assertFalse(promotion["automatic_model_replacement_enabled"])
        queue = self.payload["contracts"]["candidate_portfolio"]["records"]
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["ordering"], "unordered_composition_only")
        self.assertFalse(queue[0]["release_authorized"])

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
        candidates = [molecule for molecule in molecules if molecule["role"] == "label-blind historical structural-context record"]
        self.assertEqual(len(candidates), 4)
        for molecule in candidates:
            self.assertTrue(molecule["functional_label_blinded"])
            self.assertFalse(molecule["training_eligible"])
            states = {row["receptor_state"] for row in docking if row["molecule_id"] == molecule["molecule_id"]}
            self.assertEqual(states, {"inactive", "active-like"})
        for row in docking:
            self.assertFalse(row["admission_signal"])
            self.assertFalse(row["priority_signal"])
            self.assertFalse(row["ordering_effect"])

    def test_review_queue_is_composition_only_and_independent_of_docking_and_md(self):
        queue = self.payload["contracts"]["candidate_portfolio"]["records"][0]
        self.assertEqual(queue["ordering"], "unordered_composition_only")
        self.assertEqual(queue["admission_basis"], "governed_eligibility_contract_only")
        self.assertEqual(queue["docking_role"], "separate_structural_context_only")
        self.assertEqual(queue["md_role"], "optional_mechanistic_context_only")
        self.assertEqual(queue["record_count"], 240)
        self.assertEqual(queue["eligible_count"], 0)
        self.assertFalse(queue["release_authorized"])
        for record in self.payload["contracts"]["md_gates"]["records"]:
            self.assertEqual(record["role"], "optional_mechanistic_context_only")
            self.assertFalse(record["review_queue_dependency"])
            self.assertFalse(record["dashboard_operation_dependency"])
            self.assertFalse(record["release_dependency"])

    def test_shadow_actions_are_bounded_and_provenanced(self):
        actions = self.payload["contracts"]["shadow_actions"]["records"]
        self.assertEqual(len(actions), 7)
        prohibited = {item for action in actions for item in action["prohibited_actions"]}
        self.assertTrue({"read_sealed_outcomes", "promote_model", "start_tier_b", "release_candidate"} <= prohibited)
        self.assertIn("order_candidates", prohibited)
        self.assertIn("use_docking_for_admission", prohibited)
        self.assertNotIn("Candidate ranking", {action["stage"] for action in actions})
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
        self.assertNotIn("computationally prioritized", html)
        self.assertNotIn("computationally prioritized", js)
        self.assertNotIn("candidate ranking", html)
        self.assertNotIn("candidate ranking", js)
        self.assertNotIn("prefer live deepseek · cached fallback", html)
        self.assertNotIn('data-sort="affinity"', html)
        self.assertNotIn('data-sort="delta"', html)
        self.assertNotIn("dockingsort", js)
        self.assertIn("shadow mode", html)
        self.assertIn("governed review queue", html)
        self.assertIn("live deepseek · no fallback", html)
        self.assertIn("structural context only · no queue or priority effect", html)
        self.assertIn("optional molecular-dynamics context", html)
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

    def test_teammate_pdf_reference_is_separate_from_frozen_contracts(self):
        html = (ROOT / "track3-dashboard.html").read_text(encoding="utf-8")
        js = (ROOT / "track3-dashboard.js").read_text(encoding="utf-8")
        source_note = (ROOT / "track3_a2a" / "TEAMMATE_PDF_REFERENCE_2026-09-22.md").read_text(encoding="utf-8")
        self.assertIn('data-panel="teammate"', html)
        self.assertIn('data-view="teammate"', html)
        self.assertIn("not independently reproduced", html)
        self.assertIn("240 held and 0 eligible", html)
        self.assertIn("funnel:[[\"Library\",2963],[\"Inside PDF domain\",423],[\"Antagonist class\",335],[\"Screen-eligible\",276]]", js)
        self.assertIn("pairwise:{total:55945,separable:2770,fraction:4.95", js)
        self.assertIn("developmentStress:{n:74,calibrated:{separablePercent:4.2,coverage:0.8919},narrowed:{separablePercent:56.8,coverage:0.3649}}", js)
        self.assertIn("literature:{compoundsWithStrippedValues:155,deliveredCompounds:276,strippedValues:310,uniqueDocuments:65}", js)
        self.assertIn('id="teammate-funnel-mode"', html)
        self.assertIn('id="teammate-precision-selector"', html)
        self.assertIn('id="teammate-separation-chart"', html)
        self.assertIn('id="teammate-literature"', html)
        self.assertIn('id="teammate-download"', html)
        self.assertIn('status:"provisional_not_independently_reproduced"', js)
        self.assertIn('link.download="a2a_teammate_pdf_reported_aggregates.json"', js)
        self.assertIn('function renderTeammateFunnel()', js)
        self.assertIn('function renderSeparation(mode)', js)
        self.assertIn('function renderPrecision(size)', js)
        self.assertIn("sha256:\"5308b8041c28657c9234b9a5a0f8b50b886ebe6146affa0b877a21f73fb9145f\"", js)
        self.assertIn("The PDF is not an external-validation result", source_note)
        self.assertEqual(self.payload["summary"]["uncertainty_queue_count"], 240)
        self.assertEqual(self.payload["summary"]["uncertainty_queue_eligible"], 0)
        self.assertEqual(self.payload["summary"]["external_admitted"], 0)

    def test_design_keeps_long_content_and_status_badges_contained(self):
        html = (ROOT / "track3-dashboard.html").read_text(encoding="utf-8")
        css = (ROOT / "track3-dashboard.css").read_text(encoding="utf-8")
        js = (ROOT / "track3-dashboard.js").read_text(encoding="utf-8")
        self.assertIn('id="project-full-title"', html)
        self.assertIn('class="panel span-7 gate-panel"', html)
        self.assertIn('class="mobile-scroll-hint"', html)
        self.assertIn('$("project-full-title").textContent=data.project.title', js)
        self.assertIn('.docking-card header,.portfolio-card header{align-items:flex-start', css)
        self.assertIn('.shadow-workflow{grid-template-columns:repeat(4,minmax(0,1fr));overflow:visible', css)
        self.assertIn('.audit-item>div:nth-child(3) strong,.audit-item>div:nth-child(3) code{display:block', css)
        self.assertIn('.search,.search input{width:100%;max-width:100%;min-width:0}', css)

    def test_simplified_navigation_and_discovery_evidence_layout(self):
        html = (ROOT / "track3-dashboard.html").read_text(encoding="utf-8")
        css = (ROOT / "track3-dashboard.css").read_text(encoding="utf-8")
        js = (ROOT / "track3-dashboard.js").read_text(encoding="utf-8")
        self.assertIn('id="nav-more"', html)
        self.assertIn('class="overview-actions"', html)
        self.assertIn('id="overview-model-chart"', html)
        self.assertIn('id="overview-precision-chart"', html)
        self.assertIn('class="panel span-5 discovery-queue-panel"', html)
        self.assertIn('class="source-badges"', js)
        self.assertIn('.source-badges{display:flex;flex-wrap:wrap;align-items:center;gap:7px}', css)
        self.assertIn('function renderOverviewModels()', js)
        self.assertIn('function renderOverviewPrecision()', js)
        self.assertIn('Three reported development-set estimates, not prospective hit rates.', html)
        self.assertIn('Scientific gates and detailed status', html)

    def test_team_sign_in_describes_track3_without_legacy_ranking_claims(self):
        login = (ROOT / "login.html").read_text(encoding="utf-8")
        login_js = (ROOT / "login.js").read_text(encoding="utf-8")
        self.assertIn("Evidence first. Discovery under review.", login)
        self.assertIn("shadow-mode literature discovery", login)
        self.assertIn("A2A Track 3 dashboard", login_js)
        self.assertNotIn("Siglec-9", login)
        self.assertNotIn("Ranking Engine", login)

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
