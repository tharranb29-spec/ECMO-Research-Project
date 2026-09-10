import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORRECTION = ROOT / "track3_a2a" / "config" / "protocol.v1.1.1-correction.json"


class A2AProtocolV111Tests(unittest.TestCase):
    def test_box_correction_is_narrow_and_preserves_previous_result(self):
        correction = json.loads(CORRECTION.read_text(encoding="utf-8"))
        self.assertEqual(correction["correction"]["corrected_behavior"], "heavy atoms only")
        self.assertFalse(correction["acceptance_rule_changed"])
        self.assertFalse(correction["seeds_changed"])
        self.assertIn("v1.1/redocking_report.json", correction["preserved_failed_run"])


if __name__ == "__main__":
    unittest.main()

