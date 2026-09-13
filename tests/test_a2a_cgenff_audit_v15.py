import subprocess
import tempfile
import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "track3_a2a" / "audit_cgenff_parameters_v15.py"


class TestA2ACGenFFAuditV15(unittest.TestCase):
    def test_request_manifest_freezes_compatible_cgenff_version(self):
        manifest = json.loads(
            (ROOT / "track3_a2a" / "outputs" / "v1.5" / "md" / "cgenff_requests" / "request_manifest.json").read_text()
        )
        self.assertEqual(manifest["requested_cgenff_version"], "4.6")
        self.assertIn("July 2024", manifest["version_rationale"])

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
