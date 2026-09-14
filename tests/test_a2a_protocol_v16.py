import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class A2AProtocolV16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((A2A / "config" / "protocol.v1.6.json").read_text())

    def test_endpoint_and_models_are_unambiguous(self):
        self.assertEqual(self.protocol["endpoints"]["primary"]["name"], "pBind_Ki")
        self.assertEqual(self.protocol["models"]["primary_external_predictor"]["name"], "AB_Ridge")
        params = self.protocol["models"]["chemistry_rf_comparator"]["parameters"]
        self.assertEqual((params["n_estimators"], params["max_features"], params["min_samples_leaf"]), (500, "sqrt", 1))

    def test_external_gate_is_computational_and_outcome_blind(self):
        external = self.protocol["external_confirmation"]
        gate = external["computational_evidence_gate"]
        self.assertFalse(gate["human_approval_required"])
        self.assertFalse(gate["human_validation_claimed"])
        self.assertTrue(external["membership_freeze_before_outcome_join"])
        self.assertTrue(external["one_time_outcome_join"])
        self.assertGreaterEqual(self.protocol["endpoints"]["primary"]["minimum_records_for_external_evaluation"], 60)

    def test_md_route_and_tier_lock_are_frozen(self):
        md = self.protocol["md_v1_6"]
        self.assertEqual(md["ligand_force_field"], "GAFF2")
        self.assertEqual(md["ligand_charge_method"], "AM1-BCC")
        self.assertEqual(md["gdp_policy"]["decision"], "omit_GDP_from_selected_BD_control")
        self.assertEqual(md["tier_b"]["unlock_rule"], "Both Tier A controls pass.")
        self.assertEqual(md["best_replica_selection"], "prohibited")

    def test_protocol_freeze_hashes_reconcile(self):
        manifest = json.loads((A2A / "outputs" / "v1.6" / "protocol_freeze_manifest.json").read_text())
        for relative, expected in manifest["files"].items():
            self.assertEqual(expected, sha256(A2A / relative))
        self.assertFalse(manifest["external_outcomes_joined"])
        self.assertFalse(manifest["md_trajectory_production_started"])

    def test_all_six_ligand_bundles_pass(self):
        campaign = json.loads((A2A / "outputs" / "v1.6" / "md" / "ligand_bundles" / "campaign_manifest.json").read_text())
        self.assertEqual(campaign["accepted_count"], 6)
        self.assertEqual(campaign["status"], "complete")
        self.assertFalse(campaign["candidate_labels_loaded"])
        for entry in campaign["entries"]:
            audit_path = A2A / entry["audit"]
            self.assertEqual(entry["audit_sha256"], sha256(audit_path))
            audit = json.loads(audit_path.read_text())
            self.assertEqual(audit["status"], "accepted_for_system_building")

    def test_development_reproduction_keeps_ridge_primary(self):
        report = json.loads((A2A / "outputs" / "v1.6" / "model_reproduction" / "development_results.json").read_text())
        metrics = report["result"]["metrics"]
        self.assertGreater(metrics["AB_Ridge"]["r2"], metrics["AB_RF"]["r2"])
        self.assertGreater(metrics["AB_RF"]["r2"], metrics["E_RF"]["r2"])
        self.assertFalse(report["external_outcomes_loaded"])


if __name__ == "__main__":
    unittest.main()
