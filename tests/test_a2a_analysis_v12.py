import json
import unittest
from pathlib import Path

from track3_a2a.admit_reviewed_benchmark_v12 import review_status


ROOT = Path(__file__).resolve().parents[1]


class A2AAnalysisV12Tests(unittest.TestCase):
    def test_spec_uses_revised_structure_pair_and_orthogonal_features(self):
        spec = json.loads((ROOT / "track3_a2a/config/analysis_spec.v1.2.json").read_text())
        self.assertEqual(spec["structures"]["primary_inactive"], "5NM4")
        self.assertEqual(spec["structures"]["primary_active_like"], "2YDO")
        self.assertIn("x_active - x_inactive", spec["docking_features"]["d_affinity"])
        self.assertNotIn("biased_agonism", spec["endpoint"]["primary"])

    def test_distinct_reviewers_and_matching_tier_are_accepted(self):
        row = {
            "reviewer_1": "Cream", "decision_1": "accept_agonist", "evidence_tier_1": "tier_1",
            "reviewer_2": "Farida", "decision_2": "accept_agonist", "evidence_tier_2": "tier_1",
            "adjudicator": "", "final_decision": "", "final_evidence_tier": ""
        }
        status, detail = review_status(row)
        self.assertEqual(status, "accepted")
        self.assertEqual(detail["tier"], "tier_1")

    def test_same_person_cannot_supply_both_reviews(self):
        row = {
            "reviewer_1": "Cream", "decision_1": "accept_antagonist", "evidence_tier_1": "tier_1",
            "reviewer_2": "cream", "decision_2": "accept_antagonist", "evidence_tier_2": "tier_1",
            "adjudicator": "", "final_decision": "", "final_evidence_tier": ""
        }
        self.assertEqual(review_status(row)[0], "invalid")

    def test_tier_disagreement_requires_adjudication(self):
        row = {
            "reviewer_1": "Cream", "decision_1": "accept_agonist", "evidence_tier_1": "tier_1",
            "reviewer_2": "Farida", "decision_2": "accept_agonist", "evidence_tier_2": "tier_2",
            "adjudicator": "", "final_decision": "", "final_evidence_tier": ""
        }
        self.assertEqual(review_status(row)[0], "needs_adjudication")


if __name__ == "__main__":
    unittest.main()
