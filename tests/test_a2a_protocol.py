import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"


class A2AProtocolTests(unittest.TestCase):
    def test_protocol_keeps_update_loop_in_shadow_mode(self):
        protocol = json.loads((A2A / "config" / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["autonomous_update_mode"], "shadow_quarantine_only")
        self.assertFalse(protocol["production_screening_unlocked"])

    def test_protocol_uses_five_seeds_and_median_aggregation(self):
        protocol = json.loads((A2A / "config" / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["gnina"]["seeds"], [42, 43, 44, 45, 46])
        self.assertEqual(protocol["gnina"]["primary_seed_aggregation"], "median_valid_runs")
        self.assertEqual(protocol["gnina"]["zero_affinity_policy"], "failed_run_not_binding_measurement")

    def test_primary_endpoint_is_the_incremental_state_feature_comparison(self):
        protocol = json.loads((A2A / "config" / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["primary_endpoint"], "paired_scaffold_split_auc_model_D_minus_model_C")


if __name__ == "__main__":
    unittest.main()

