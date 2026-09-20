import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import track3_discovery_workflow as workflow
from research_assistant_server import Handler


class Track3DiscoveryWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "state.json"
        self.state_patch = mock.patch.object(workflow, "STATE_PATH", self.state_path)
        self.key_patch = mock.patch.object(workflow, "DEEPSEEK_API_KEY", "")
        self.state_patch.start()
        self.key_patch.start()

    def tearDown(self):
        self.key_patch.stop()
        self.state_patch.stop()
        self.temp_dir.cleanup()

    def test_cached_demo_is_cited_gated_and_fail_closed(self):
        result = workflow.run_workflow("human ADORA2A evidence", provider_mode="demo")
        self.assertEqual(result["workflow_state"], "cached_demo")
        self.assertTrue(all(source["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/") for source in result["sources"]))
        self.assertTrue(all(item["evidence_quality"] == "quarantine" for item in result["extractions"]))
        self.assertEqual(result["screen_eligible_queue"]["ordering"], "unordered_composition_only")
        self.assertEqual(result["screen_eligible_queue"]["count"], 0)
        self.assertTrue(all(item["state"] == "available" for item in result["contract_inputs"].values()))
        self.assertTrue(all(item["provisional_score"] is None for item in result["molecules"]))
        self.assertTrue(all(item["score_state"] == "unavailable_no_serialized_ab_ridge" for item in result["molecules"]))
        self.assertTrue(all(not item["screen_eligible"] for item in result["molecules"]))
        self.assertTrue(all(item["eligibility_state"] == "simulated_identity_demo" for item in result["molecules"]))
        self.assertEqual(
            result["screen_eligible_queue"]["eligibility_contract"]["schema_id"],
            "a2a-review-eligibility.v1",
        )
        self.assertEqual(result["governance"]["autonomy_mode"], "shadow_only")
        self.assertFalse(result["governance"]["external_outcomes_loaded"])
        self.assertFalse(result["governance"]["model_promotion_enabled"])
        self.assertFalse(result["governance"]["tier_b_unlocked"])
        self.assertFalse(result["governance"]["ordinal_ranking_presented"])
        self.assertFalse(result["governance"]["per_position_probability_presented"])
        self.assertFalse(result["governance"]["certified_hit_presented"])

    def test_audit_chain_and_human_disposition_are_append_only(self):
        result = workflow.run_workflow("A2A evidence", provider_mode="demo")
        previous = "GENESIS"
        for entry in result["audit_log"]:
            self.assertEqual(entry["previous_entry_hash"], previous)
            recorded = entry["entry_hash"]
            self.assertEqual(recorded, workflow.canonical_hash({key: value for key, value in entry.items() if key != "entry_hash"}))
            previous = recorded
        updated = workflow.apply_disposition(result["run_id"], "quarantine", "Dr. Reviewer", "Insufficient primary text")
        self.assertEqual(updated["human_disposition"]["status"], "quarantine")
        self.assertEqual(updated["audit_log"][-1]["previous_entry_hash"], previous)
        self.assertEqual(updated["audit_log"][-1]["event_type"], "human_disposition")

    def test_duplicate_identity_is_removed_from_queue(self):
        smiles = "Nc1ncnc2c1ncn2[C@@H]1O[C@H](CO)[C@@H](O)[C@H]1O"
        result = workflow.run_workflow(
            "A2A evidence",
            molecules=[{"name": "A", "smiles": smiles}, {"name": "B", "smiles": smiles}],
            provider_mode="demo",
        )
        self.assertEqual(result["screen_eligible_queue"]["count"], 0)
        self.assertIsNotNone(result["molecules"][1]["duplicate_of"])
        self.assertEqual(result["molecules"][1]["eligibility_state"], "duplicate_identity")

    def governed_record(self):
        return {
            "molecule_id": "novel:test",
            "standardization_state": "standardized",
            "state_label": "live",
            "duplicate_of": None,
            "provisional_score": 6.8,
            "interval_90": {"lower": 6.4, "upper": 7.1, "level": 0.9},
            "threshold_pbind_ki": 6.7412,
            "model_provenance_status": "verified_frozen_artifact",
            "interval_provenance_status": "verified",
            "threshold_provenance_status": "verified",
            "external_outcomes_loaded": False,
            "docking_used_for_admission": False,
            "eligibility_reasons": [],
            "screen_eligible": False,
            "eligibility_state": "blocked_missing_governed_inputs",
        }

    def test_every_required_governed_input_fails_closed_when_missing(self):
        contract = workflow.load_eligibility_contract()
        for field in (
            "provisional_score", "interval_90", "threshold_pbind_ki",
            "model_provenance_status", "interval_provenance_status", "threshold_provenance_status",
        ):
            with self.subTest(field=field):
                record = self.governed_record()
                record[field] = None
                self.assertFalse(workflow.evaluate_governed_eligibility(record, contract))
                self.assertFalse(record["screen_eligible"])
                self.assertEqual(record["eligibility_state"], "blocked_missing_governed_inputs")

    def test_authoritative_upper_bound_rule_admits_only_fully_governed_record(self):
        contract = workflow.load_eligibility_contract()
        record = self.governed_record()
        self.assertTrue(workflow.evaluate_governed_eligibility(record, contract))
        self.assertTrue(record["screen_eligible"])
        self.assertEqual(record["eligibility_state"], "screen_eligible_not_ruled_out")
        record = self.governed_record()
        record["interval_90"] = {"lower": 6.2, "upper": 6.7, "level": 0.9}
        record["provisional_score"] = 6.5
        self.assertFalse(workflow.evaluate_governed_eligibility(record, contract))
        self.assertEqual(record["eligibility_state"], "ruled_out_by_90pct_interval")

    def test_novel_query_without_governed_scientific_inputs_is_not_eligible(self):
        result = workflow.run_workflow(
            "novel ADORA2A query",
            molecules=[{"name": "Novel", "smiles": "CCO"}],
            provider_mode="demo",
        )
        self.assertEqual(result["screen_eligible_queue"]["count"], 0)
        self.assertFalse(result["molecules"][0]["screen_eligible"])
        self.assertIn(
            result["molecules"][0]["eligibility_state"],
            {"simulated_identity_demo", "blocked_identity_unavailable"},
        )

    def test_legacy_cached_state_is_reprojected_fail_closed(self):
        legacy = {
            "workflow_state": "cached_demo",
            "molecules": [{
                **self.governed_record(),
                "state_label": "simulated",
                "standardization_state": "cached_precomputed",
                "screen_eligible": True,
                "eligibility_reasons": ["Simulated demo eligibility only; not external admission."],
            }],
            "screen_eligible_queue": {"count": 1, "records": [{"molecule_id": "novel:test"}]},
        }
        self.state_path.write_text(json.dumps(legacy))
        migrated = workflow.load_state()
        self.assertEqual(migrated["screen_eligible_queue"]["count"], 0)
        self.assertFalse(migrated["molecules"][0]["screen_eligible"])
        self.assertEqual(migrated["molecules"][0]["eligibility_state"], "simulated_identity_demo")
        self.assertEqual(
            migrated["screen_eligible_queue"]["eligibility_contract"]["schema_id"],
            "a2a-review-eligibility.v1",
        )

    def test_missing_rdkit_holds_uncached_live_input(self):
        with mock.patch.object(workflow, "rdkit_available", return_value=False):
            result = workflow.run_workflow(
                "A2A evidence",
                molecules=[{"name": "Unknown", "smiles": "CCO"}],
                provider_mode="demo",
            )
        molecule = result["molecules"][0]
        self.assertEqual(molecule["standardization_state"], "unavailable")
        self.assertFalse(molecule["screen_eligible"])

    def test_live_request_without_key_falls_back_explicitly(self):
        result = workflow.run_workflow("A2A evidence", provider_mode="live")
        self.assertEqual(result["workflow_state"], "cached_demo")
        self.assertIn("DEEPSEEK_API_KEY", result["fallback_reason"])
        self.assertFalse(result["provider"]["api_key_exposed"])
        capabilities = workflow.capability_status()
        self.assertEqual(capabilities["live_provider_name"], "deepseek_evidence_extraction")
        self.assertEqual(capabilities["live_provider"], "unavailable")

    def test_deepseek_provider_structures_deterministically_retrieved_sources(self):
        europe_payload = {"resultList": {"result": [{
            "source": "MED", "id": "1", "pmid": "1", "title": "Primary source",
            "doi": "unresolved", "abstractText": "Human ADORA2A assay context.", "isOpenAccess": "N",
        }]}}
        deepseek_payload = {"choices": [{"message": {"content": json.dumps({
            "extractions": [{
                "source_id": "PMID:1", "target": "ADORA2A", "assay_context": "unresolved",
                "molecule_mentions": [], "evidence_quality": "review", "reason": "Exact context unresolved.",
                "citation_url": "https://europepmc.org/article/MED/1",
            }],
        })}}]}

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        captured = {}

        def fake_urlopen(req, timeout):
            if isinstance(req, str):
                return FakeResponse(europe_payload)
            captured["payload"] = json.loads(req.data)
            captured["authorization"] = req.headers.get("Authorization")
            return FakeResponse(deepseek_payload)

        with mock.patch.object(workflow.request, "urlopen", side_effect=fake_urlopen):
            result = workflow.DeepSeekEvidenceProvider("server-secret").discover("A2A evidence")
        self.assertEqual(captured["payload"]["model"], "deepseek-chat")
        self.assertIn("messages", captured["payload"])
        self.assertEqual(captured["authorization"], "Bearer server-secret")
        self.assertEqual(result["state"], "live")
        self.assertEqual(result["sources"][0]["retrieval_state"], "live")

    def test_auto_mode_fails_closed_to_cached_demo_on_live_timeout(self):
        with mock.patch.object(workflow, "DEEPSEEK_API_KEY", "server-secret"), mock.patch.object(
            workflow.DeepSeekEvidenceProvider,
            "discover",
            side_effect=RuntimeError("DeepSeek discovery request timed out."),
        ):
            result = workflow.run_workflow("A2A evidence", provider_mode="auto")
        self.assertEqual(result["workflow_state"], "cached_demo")
        self.assertIn("failed closed", result["fallback_reason"])
        self.assertIn("timed out", result["fallback_reason"])
        self.assertFalse(result["governance"]["model_promotion_enabled"])

    def test_explicit_live_mode_surfaces_provider_timeout(self):
        with mock.patch.object(workflow, "DEEPSEEK_API_KEY", "server-secret"), mock.patch.object(
            workflow.DeepSeekEvidenceProvider,
            "discover",
            side_effect=RuntimeError("DeepSeek discovery request timed out."),
        ):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                workflow.run_workflow("A2A evidence", provider_mode="live")

    def test_missing_upstream_contract_is_reported_unavailable(self):
        contracts = dict(workflow.CONTRACT_INPUTS)
        contracts["future_workstream"] = Path(self.temp_dir.name) / "missing.json"
        with mock.patch.object(workflow, "CONTRACT_INPUTS", contracts):
            status = workflow.contract_status()
        self.assertEqual(status["future_workstream"]["state"], "unavailable")
        self.assertIsNone(status["future_workstream"]["sha256"])

    def test_http_endpoints_run_demo_and_record_disposition(self):
        captured = []
        handler = object.__new__(Handler)
        handler.path = "/api/discovery/run"
        handler._origin_allowed = lambda: True
        handler._is_authorized = lambda: True
        handler._enforce_rate_limit = lambda *args: True
        handler._read_json_body = lambda: {"query": "A2A primary evidence", "provider_mode": "demo", "molecules": []}
        handler._send_json = lambda payload, **kwargs: captured.append(payload)
        handler._send_error_json = lambda *args, **kwargs: self.fail(f"Unexpected API error: {args}")
        Handler.do_POST(handler)
        self.assertTrue(captured[-1]["ok"])
        run_id = captured[-1]["run"]["run_id"]

        handler.path = "/api/discovery/disposition"
        handler._read_json_body = lambda: {"run_id": run_id, "status": "retain_for_review", "reviewer": "QA reviewer"}
        Handler.do_POST(handler)
        self.assertEqual(captured[-1]["run"]["human_disposition"]["status"], "retain_for_review")


if __name__ == "__main__":
    unittest.main()
