import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "track3_a2a" / "config" / "protocol.v1.1.json"


class A2AProtocolV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_primary_pair_is_5nm4_and_2ydo(self):
        self.assertEqual(self.protocol["structures"]["inactive_primary"]["pdb_id"], "5NM4")
        self.assertEqual(self.protocol["structures"]["active_like_primary"]["pdb_id"], "2YDO")

    def test_4eiy_failure_is_preserved_as_sensitivity(self):
        sensitivity = self.protocol["structures"]["inactive_sensitivity"]
        self.assertEqual(sensitivity["pdb_id"], "4EIY")
        self.assertEqual(sensitivity["registered_v1_0_gate_status"], "failed")

    def test_screening_remains_locked_before_dataset_validation(self):
        self.assertFalse(self.protocol["model_training_unlocked"])
        self.assertFalse(self.protocol["production_screening_unlocked"])

    def test_exact_redocking_acceptance_rule_is_unchanged(self):
        gate = self.protocol["redocking_gate"]
        self.assertEqual(gate["rmsd_threshold_angstrom"], 2.0)
        self.assertEqual(gate["minimum_passing_seeds"], 4)
        self.assertTrue(gate["median_rmsd_must_pass"])


if __name__ == "__main__":
    unittest.main()

