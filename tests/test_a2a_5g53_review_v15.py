import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestA2A5G53ReviewV15(unittest.TestCase):
    def test_chirality_review_selects_unaffected_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "review.json"
            subprocess.run(
                [sys.executable, str(ROOT / "track3_a2a" / "review_5g53_chirality_v15.py"), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(output.read_text())
            self.assertEqual(report["decision"]["status"], "resolved_by_copy_selection")
            self.assertEqual(report["decision"]["selected_receptor_chain"], "B")
            self.assertEqual(report["decision"]["selected_mini_gs_chain"], "D")
            self.assertFalse(report["chirality_check"]["C"]["matches_dominant_chain_sign"])
            self.assertTrue(report["chirality_check"]["D"]["matches_dominant_chain_sign"])
            self.assertFalse(report["decision"]["deposited_coordinate_edit_performed"])


if __name__ == "__main__":
    unittest.main()
