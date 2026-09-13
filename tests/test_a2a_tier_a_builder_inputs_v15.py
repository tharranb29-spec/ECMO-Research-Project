import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestA2ATierABuilderInputsV15(unittest.TestCase):
    def test_builder_inputs_preserve_gate_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "track3_a2a" / "prepare_tier_a_builder_inputs_v15.py"),
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            audit = json.loads((output / "builder_input_audit.json").read_text())

        systems = {system["system_id"]: system for system in audit["systems"]}
        inactive = systems["5NM4_ZMA_native"]
        active = systems["5G53_NECA_miniGs_native"]
        self.assertEqual(inactive["zma_atom_count"], 40)
        self.assertEqual(inactive["sodium_atom_count"], 1)
        self.assertGreater(inactive["retained_water_atom_count"], 0)
        self.assertEqual(len(inactive["deposited_mutation_inventory_verified"]), 9)
        self.assertTrue(active["gdp_transfer"]["alignment_passed"])
        self.assertFalse(active["gdp_transfer"]["clash_passed"])
        self.assertEqual(active["status"], "builder_input_generated_geometric_review_failed")
        self.assertFalse(audit["trajectory_production_started"])


if __name__ == "__main__":
    unittest.main()
