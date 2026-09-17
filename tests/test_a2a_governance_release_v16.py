import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from track3_a2a.build_v16_governance_release import build_release, evaluate_invariants, freeze_signature


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"


class A2AGovernanceReleaseV16Tests(unittest.TestCase):
    def test_repository_governance_invariants_pass(self):
        checks, context = evaluate_invariants(A2A)
        failures = [item for item in checks if item["status"] != "pass"]
        self.assertEqual(failures, [])
        self.assertGreaterEqual(len(checks), 30)
        self.assertTrue(context["equilibration"]["tier_a_production_unlocked"])
        self.assertFalse(context["equilibration"]["tier_b_unlocked"])

    def test_release_is_deterministic_and_self_reconciling(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            manifest_a = build_release(A2A, Path(first))
            manifest_b = build_release(A2A, Path(second))
            self.assertEqual(manifest_a, manifest_b)
            for name, expected in manifest_a["release_artifacts"].items():
                actual = hashlib.sha256((Path(first) / name).read_bytes()).hexdigest()
                self.assertEqual(actual, expected)

    def test_endpoint_drift_is_detected(self):
        original = json.loads((A2A / "config" / "protocol.v1.6.json").read_text())
        drifted = copy.deepcopy(original)
        drifted["endpoints"]["primary"]["name"] = "pBind_Kd"
        real_loader = json.loads

        def load_with_drift(root, key):
            if key == "protocol":
                return drifted
            path = A2A / {
                "freeze": "outputs/v1.6/protocol_freeze_manifest.json",
                "model": "outputs/v1.6/model_reproduction/development_results.json",
                "pass1": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
                "implementation": "outputs/v1.6/implementation_status.json",
                "equilibration": "outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json",
            }[key]
            return real_loader(path.read_text())

        with patch("track3_a2a.build_v16_governance_release.load_json", side_effect=load_with_drift):
            checks, _ = evaluate_invariants(A2A)
        by_id = {item["check_id"]: item for item in checks}
        self.assertEqual(by_id["primary_endpoint_frozen"]["status"], "fail")

    def test_freeze_signature_recomputes_exactly(self):
        manifest = json.loads((A2A / "outputs/v1.6/protocol_freeze_manifest.json").read_text())
        self.assertEqual(freeze_signature(manifest), manifest["computational_release_signature_sha256"])


if __name__ == "__main__":
    unittest.main()
