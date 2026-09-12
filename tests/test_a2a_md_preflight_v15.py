import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"


class A2AMDPreflightV15Tests(unittest.TestCase):
    def test_preflight_is_label_blind_and_does_not_start_trajectories(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            subprocess.run(
                [sys.executable, str(A2A / "prepare_md_validation_v15.py"), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            status = json.loads((output / "preflight_status.json").read_text())
            with (output / "system_input_manifest.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
        self.assertFalse(status["candidate_labels_loaded"])
        self.assertFalse(status["trajectory_production_started"])
        self.assertEqual(status["tier_a_system_count"], 2)
        self.assertEqual(status["tier_b_system_count"], 8)
        self.assertEqual(len(rows), 10)
        self.assertNotIn("functional_label", rows[0])


if __name__ == "__main__":
    unittest.main()
