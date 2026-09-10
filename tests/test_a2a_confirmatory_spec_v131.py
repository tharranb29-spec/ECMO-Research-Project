import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class A2AConfirmatorySpecV131Tests(unittest.TestCase):
    def test_computational_curation_replaces_human_gate_prospectively(self):
        spec = json.loads((ROOT / "track3_a2a/config/confirmatory_spec.v1.3.1.json").read_text())
        self.assertFalse(spec["population"]["human_approval_required"])
        self.assertFalse(spec["population"]["human_validation_claimed"])
        self.assertTrue(spec["holdout_rules"]["rebuild_after_computational_curation"])

    def test_label_and_model_gates_are_separate(self):
        spec = json.loads((ROOT / "track3_a2a/config/confirmatory_spec.v1.3.1.json").read_text())
        self.assertTrue(spec["gate_separation"]["auc_cannot_admit_or_reject_individual_labels"])
        self.assertTrue(spec["holdout_rules"]["evaluate_once"])


if __name__ == "__main__":
    unittest.main()
