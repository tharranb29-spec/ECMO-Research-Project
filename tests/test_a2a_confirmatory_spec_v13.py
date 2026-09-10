import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class A2AConfirmatorySpecV13Tests(unittest.TestCase):
    def test_holdout_is_single_use_and_requires_review(self):
        spec = json.loads((ROOT / "track3_a2a/config/confirmatory_spec.v1.3.json").read_text())
        self.assertTrue(spec["holdout_rules"]["evaluate_once"])
        self.assertTrue(spec["holdout_rules"]["rebuild_after_formal_review"])
        self.assertEqual(spec["population"]["minimum_distinct_reviewers_per_record"], 2)

    def test_claim_is_limited(self):
        spec = json.loads((ROOT / "track3_a2a/config/confirmatory_spec.v1.3.json").read_text())
        self.assertIn("improved agonist-versus-antagonist prediction", spec["not_claimed"])
        self.assertIn("d_cnnscore", spec["mandatory_sensitivity"]["joint_model"])


if __name__ == "__main__":
    unittest.main()
