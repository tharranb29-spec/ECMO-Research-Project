import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from track3_a2a.build_v161_scope_release import (
    build_claim_matrix,
    build_dashboard_contract,
    build_release,
    canonical_hash,
    validate_sources,
)


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"


class A2AScopeAmendmentV161Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((A2A / "config/competition_scope.v1.6.1.json").read_text())

    def test_frozen_science_and_firewall_reconcile(self):
        context = validate_sources(A2A)
        self.assertEqual(context["scope"]["scientific_freeze"]["endpoint"]["name"], "pBind_Ki")
        self.assertFalse(context["external"]["one_time_outcome_join_authorized"])
        self.assertFalse(context["model"]["external_outcomes_loaded"])

    def test_candidate_claim_boundary_is_fail_closed(self):
        queue = self.scope["candidate_review_scope"]
        self.assertFalse(queue["per_position_candidate_ranking_defensible"])
        self.assertFalse(queue["per_candidate_hit_probability_defensible"])
        self.assertEqual(queue["allowed_candidate_status"], "screen_eligible_not_ruled_out")
        self.assertEqual(queue["prohibited_candidate_status"], "certified_hit")
        self.assertIsNone(queue["queue_count"]["authorized_count"])
        self.assertIsNone(queue["interval_bound_selection_rule"])

    def test_unlabeled_queue_cannot_claim_external_floor(self):
        floor = self.scope["external_confirmation_floor"]
        self.assertEqual((floor["minimum_molecules"], floor["minimum_generic_murcko_scaffolds"]), (60, 20))
        self.assertFalse(floor["unlabeled_review_queue_satisfies_floor"])
        self.assertFalse(floor["current_frozen_external_cohort"]["confirmation_floor_passed"])

    def test_md_cutoff_and_dashboard_autonomy_are_narrow(self):
        self.assertFalse(self.scope["md_cutoff_policy"]["tier_a"]["completion_claim_allowed"])
        self.assertEqual(self.scope["md_cutoff_policy"]["tier_b"]["status"], "locked")
        self.assertFalse(self.scope["md_cutoff_policy"]["tier_b"]["submission_critical"])
        autonomy = self.scope["dashboard_autonomy"]
        self.assertEqual(autonomy["mode"], "shadow_only_evidence_orchestration")
        self.assertIn("promote or replace a model", autonomy["may_not"])
        self.assertIn("unseal or join outcomes", autonomy["may_not"])

    def test_claim_matrix_and_dashboard_contract_are_exact(self):
        matrix = build_claim_matrix(self.scope)
        claims = {row["claim_id"]: row for row in matrix["claims"]}
        self.assertEqual(claims["per_position_candidate_ranking"]["disposition"], "prohibited")
        self.assertEqual(claims["tier_b"]["disposition"], "locked_not_submission_critical")
        contract = build_dashboard_contract(self.scope, "0" * 64)
        self.assertFalse(contract["candidate_review"]["scientific_rank_allowed"])
        self.assertFalse(contract["candidate_review"]["candidate_probability_allowed"])
        self.assertIsNone(contract["candidate_review"]["fixed_queue_count"])
        self.assertFalse(any(contract["autonomy"][field] for field in (
            "automatic_scientific_validation", "protocol_change", "model_promotion", "outcome_unsealing", "md_unlock"
        )))

    def test_release_is_deterministic_and_hashes_reconcile(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            left = build_release(A2A, Path(first))
            right = build_release(A2A, Path(second))
            self.assertEqual(left, right)
            for name, expected in left["release_artifacts"].items():
                actual = hashlib.sha256((Path(first) / name).read_bytes()).hexdigest()
                self.assertEqual(actual, expected)
            signature = left["release_signature_sha256"]
            unsigned = {key: value for key, value in left.items() if key != "release_signature_sha256"}
            self.assertEqual(signature, canonical_hash(unsigned))
            for relative, expected in left["source_artifacts"].items():
                self.assertEqual(expected, hashlib.sha256((A2A / relative).read_bytes()).hexdigest())

    def test_model_drift_blocks_release(self):
        drifted = copy.deepcopy(self.scope)
        drifted["scientific_freeze"]["estimators"]["AB_Ridge"]["parameters"]["alpha"] = 2.0

        from track3_a2a import build_v161_scope_release as release
        original_loader = release.load_json

        def load_with_drift(root, key):
            return drifted if key == "scope" else original_loader(root, key)

        with patch("track3_a2a.build_v161_scope_release.load_json", side_effect=load_with_drift):
            with self.assertRaisesRegex(RuntimeError, "Ridge parameters drifted"):
                validate_sources(A2A)


if __name__ == "__main__":
    unittest.main()
