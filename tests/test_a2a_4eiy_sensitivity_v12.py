import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class A2A4EIYSensitivityTests(unittest.TestCase):
    def test_protocol_preserves_failed_gate_and_requires_sensitivity(self):
        protocol = json.loads((ROOT / "track3_a2a/config/protocol.v1.1.json").read_text())
        self.assertEqual(protocol["change_control"]["required_sensitivity_structure"], "4EIY")
        self.assertEqual(protocol["structures"]["inactive_sensitivity"]["registered_v1_0_gate_status"], "failed")


if __name__ == "__main__":
    unittest.main()
