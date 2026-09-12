import json
import unittest
from pathlib import Path

from track3_a2a.run_external_docking_v14 import retained_run


ROOT = Path(__file__).resolve().parents[1]


class A2AExternalDockingV14Tests(unittest.TestCase):
    def test_retained_pose_is_median_nearest_not_best_score(self):
        runs = [
            {"seed": 42, "status": "valid", "minimized_affinity_kcal_mol": -10.0},
            {"seed": 43, "status": "valid", "minimized_affinity_kcal_mol": -8.0},
            {"seed": 44, "status": "valid", "minimized_affinity_kcal_mol": -7.0},
        ]
        self.assertEqual(retained_run(runs)["seed"], 43)

    def test_two_seed_tie_uses_lower_seed(self):
        runs = [
            {"seed": 44, "status": "valid", "minimized_affinity_kcal_mol": -9.0},
            {"seed": 42, "status": "valid", "minimized_affinity_kcal_mol": -7.0},
            {"seed": 43, "status": "failed"},
        ]
        self.assertEqual(retained_run(runs)["seed"], 42)

    def test_pose_rule_is_frozen_and_label_blind(self):
        config = json.loads(
            (ROOT / "track3_a2a" / "config" / "md_pose_selection.v1.5.json").read_text()
        )
        self.assertTrue(config["best_score_selection_prohibited"])
        self.assertFalse(config["functional_labels_available_to_selection"])
        self.assertTrue(config["change_after_docking_requires_versioned_amendment"])


if __name__ == "__main__":
    unittest.main()
