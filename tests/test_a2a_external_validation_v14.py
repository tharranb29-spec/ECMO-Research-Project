import csv
import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RDKIT_AVAILABLE = importlib.util.find_spec("rdkit") is not None


class A2AExternalValidationV14Tests(unittest.TestCase):
    def setUp(self):
        self.external = json.loads(
            (ROOT / "track3_a2a/config/external_validation.v1.4.json").read_text()
        )
        self.shadow = json.loads(
            (ROOT / "track3_a2a/config/shadow_update.v1.4.json").read_text()
        )
        self.status = json.loads(
            (ROOT / "track3_a2a/outputs/v1.4/shadow_update_status.json").read_text()
        )

    def test_historical_holdout_is_preserved_and_not_reused(self):
        boundary = self.external["existing_evidence_boundary"]
        self.assertTrue(boundary["historical_holdout_accessed"])
        self.assertFalse(boundary["historical_holdout_gate_passed"])
        self.assertFalse(boundary["use_for_external_evaluation"])
        self.assertIn("must never be rerun", self.external["preservation_rule"])

    def test_external_cohort_requires_structure_and_scaffold_independence(self):
        rules = self.external["external_cohort"]["required_independence"]
        self.assertTrue(any("InChIKey" in rule for rule in rules))
        self.assertTrue(any("Murcko scaffold" in rule for rule in rules))

    def test_production_docking_matches_frozen_v12_execution(self):
        docking = self.external["docking"]
        self.assertEqual(docking["production_seeds"], [42, 43, 44])
        self.assertEqual(docking["aggregation"], "median of valid seeds")
        self.assertEqual(docking["inactive_receptor"], "5NM4")
        self.assertEqual(docking["active_like_receptor"], "2YDO")
        self.assertEqual(docking["cnnscore_behavior"], "soft flag only; report by class and receptor")

    def test_llm_cannot_create_ground_truth_or_promote(self):
        permissions = self.shadow["llm_permissions"]
        self.assertTrue(permissions["discover_literature"])
        self.assertTrue(permissions["propose_novel_molecules"])
        self.assertFalse(permissions["assign_training_labels"])
        self.assertFalse(permissions["promote_model"])
        self.assertFalse(permissions["publish_candidates_as_validated_hits"])

    def test_classifier_cannot_train_on_its_predictions(self):
        permissions = self.shadow["classifier_permissions"]
        self.assertTrue(permissions["score_unlabeled_candidates"])
        self.assertFalse(permissions["use_predictions_as_evidence_labels"])
        self.assertFalse(permissions["self_retrain_on_predictions"])

    def test_initial_state_is_shadow_only_with_no_promoted_model(self):
        self.assertEqual(self.status["mode"], "shadow_only")
        self.assertIsNone(self.status["served_track3_model"])
        self.assertFalse(self.status["automatic_model_replacement_enabled"])
        self.assertTrue(self.status["historical_holdout_locked"])

    def test_power_plan_is_frozen_and_requires_balanced_minimum(self):
        power = json.loads(
            (ROOT / "track3_a2a/config/external_power.v1.4.json").read_text()
        )
        self.assertEqual(power["status"], "frozen_before_external_candidate_admission")
        self.assertEqual(power["minimum_expected_per_class"], 60)
        self.assertEqual(power["planning_effect"], 0.75)

    def test_logistic_power_helper_detects_strong_positive_signal(self):
        from track3_a2a.plan_external_power_v14 import fit_logistic_wald

        rng = np.random.default_rng(7)
        signal = rng.normal(size=1500)
        design = np.column_stack([rng.normal(size=(1500, 4)), signal])
        labels = (signal + rng.normal(scale=0.5, size=1500) > 0).astype(int)
        fitted = fit_logistic_wald(design, labels)
        self.assertIsNotNone(fitted)
        coefficient, p_value = fitted
        self.assertGreater(coefficient, 0)
        self.assertLess(p_value, 0.05)

    def test_prefreeze_pool_is_not_declared_external(self):
        from track3_a2a.audit_prefreeze_pool_v14 import build_report

        report = build_report()
        self.assertEqual(report["answer"], "no")
        self.assertEqual(report["definitive_external_eligible_count"], 0)
        self.assertGreater(report["retrospective_stress_test_candidate_count"], 0)

    @unittest.skipUnless(RDKIT_AVAILABLE, "RDKit is installed in the isolated Track 3 environment")
    def test_candidate_screen_rejects_historical_scaffold_and_prior_visibility(self):
        from track3_a2a.screen_external_candidates_v14 import parse_timestamp, screen_rows
        from track3_a2a.standardize_quarantine import standardize_smiles

        historical_chemistry = standardize_smiles("c1ccccc1")
        historical = [{
            "standardized_inchikey": historical_chemistry["standardized_inchikey"],
            "standardized_smiles": historical_chemistry["standardized_smiles"],
            "generic_murcko_scaffold_smiles": historical_chemistry["generic_murcko_scaffold_smiles"],
        }]
        base = {
            "record_id": "EXT-1",
            "external_identifier": "NEW-1",
            "canonical_smiles": "C1CC1",
            "source_id": "SOURCE-1",
            "source_url": "https://example.test/source/1",
            "source_snapshot_id": "snapshot-1",
            "source_retrieved_at": "2026-09-11T00:00:00+00:00",
            "prior_project_visibility": "false",
        }
        accepted, quarantined = screen_rows(
            [base], historical, set(), parse_timestamp("2026-09-10T13:08:35+00:00"), set()
        )
        self.assertEqual(len(accepted), 1)
        self.assertFalse(quarantined)

        overlapping = {**base, "record_id": "EXT-2", "canonical_smiles": "c1ccccc1"}
        prior_visible = {**base, "record_id": "EXT-3", "prior_project_visibility": "true"}
        accepted, quarantined = screen_rows(
            [overlapping, prior_visible], historical, set(),
            datetime(2026, 9, 10, 13, 8, 35, tzinfo=timezone.utc),
            set(),
        )
        self.assertFalse(accepted)
        reasons = " ".join(row["screening_reasons"] for row in quarantined)
        self.assertIn("historical_generic_murcko_scaffold_overlap", reasons)
        self.assertIn("prior_project_visibility_not_false", reasons)

        accepted, quarantined = screen_rows(
            [base], historical, set(), parse_timestamp("2026-09-10T13:08:35+00:00"),
            {standardize_smiles(base["canonical_smiles"])["standardized_inchikey"]},
        )
        self.assertFalse(accepted)
        self.assertIn("structure_present_in_prefreeze_source_pool", quarantined[0]["screening_reasons"])

    @unittest.skipUnless(RDKIT_AVAILABLE, "RDKit is installed in the isolated Track 3 environment")
    def test_candidate_screen_rejects_label_leakage(self):
        from track3_a2a.screen_external_candidates_v14 import parse_timestamp, screen_rows

        row = {
            "record_id": "EXT-LABEL",
            "external_identifier": "NEW-LABEL",
            "canonical_smiles": "C1CC1",
            "source_id": "SOURCE-LABEL",
            "source_url": "https://example.test/source/label",
            "source_snapshot_id": "snapshot-label",
            "source_retrieved_at": "2026-09-11T00:00:00+00:00",
            "prior_project_visibility": "false",
            "functional_class": "agonist",
        }
        accepted, quarantined = screen_rows(
            [row], [], set(), parse_timestamp("2026-09-10T13:08:35+00:00")
        )
        self.assertFalse(accepted)
        self.assertIn("label_fields_present:functional_class", quarantined[0]["screening_reasons"])

    def test_gtopdb_snapshot_is_label_free_and_screened(self):
        source = ROOT / "track3_a2a/data/raw/external/gtopdb_2026.2/external_candidates_gtopdb_2026.2.csv"
        with source.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            headers = set(reader.fieldnames or [])
            rows = list(reader)
        self.assertEqual(len(rows), 96)
        self.assertTrue(headers.isdisjoint({"functional_class", "primary_binary_label", "label", "assay_readout"}))
        audit = json.loads((
            ROOT / "track3_a2a/outputs/v1.4/external_cohort/gtopdb_2026.2/screening_audit.json"
        ).read_text())
        self.assertEqual(audit["eligible_count"], 42)
        self.assertEqual(audit["quarantined_count"], 54)
        self.assertFalse(audit["labels_loaded"])

if __name__ == "__main__":
    unittest.main()
