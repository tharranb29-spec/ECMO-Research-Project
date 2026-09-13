import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "track3_a2a" / "audit_cgenff_parameters_v15.py"


class TestA2ACGenFFAuditV15(unittest.TestCase):
    def test_missing_returns_remain_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "audit.json"
            result = subprocess.run(
                ["python3", str(SCRIPT), "--input-dir", directory, "--output", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('"status": "blocked_or_parameters_pending"', result.stdout)
            self.assertIn('"production_parameter_gate_passed": false', target.read_text())


if __name__ == "__main__":
    unittest.main()
