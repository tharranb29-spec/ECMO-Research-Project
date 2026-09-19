import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from track3_a2a.build_uncertainty_review_queue_v16 import (
    CLAIMED_THRESHOLD,
    REQUIRED_PREDICTION_COLUMNS,
    record_for_dashboard,
    validate_predictions,
    wilson_rate,
)


class A2AUncertaintyReviewQueueV16Tests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / "track3_a2a"

    def ledger(self):
        return {
            "candidate_id": "BDB-1",
            "standardized_inchikey": "TEST-INCHIKEY",
            "generic_murcko_scaffold_smiles": "C1CC1",
            "pass_1_status": "metadata_pass_fulltext_ready",
        }

    def write_prediction_fixture(self, root, *, lower=6.5, upper=7.1, outcomes=False, docking=False):
        artifact = root / "artifact.txt"
        artifact.write_text("frozen provenance\n")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        path = root / "predictions.csv"
        row = {name: "" for name in REQUIRED_PREDICTION_COLUMNS}
        row.update({
            "candidate_id": "BDB-1",
            "standardized_inchikey": "TEST-INCHIKEY",
            "model_id": "AB_Ridge",
            "model_artifact_path": "artifact.txt",
            "model_artifact_sha256": digest,
            "prediction_code_path": "artifact.txt",
            "prediction_code_sha256": digest,
            "prediction_pbind_ki": "6.8",
            "interval_lower_90": str(lower),
            "interval_upper_90": str(upper),
            "interval_level": "0.90",
            "interval_method": "split_conformal",
            "interval_calibration_source_path": "artifact.txt",
            "interval_calibration_source_sha256": digest,
            "applicability_status": "inside_domain",
            "nearest_neighbor_similarity": "0.4",
            "descriptor_distance": "1.2",
            "threshold_pbind_ki": str(CLAIMED_THRESHOLD),
            "threshold_operator": ">=",
            "threshold_source_path": "artifact.txt",
            "threshold_source_sha256": digest,
            "threshold_derivation": "prospectively frozen training-only rule",
            "external_outcomes_loaded": str(outcomes).lower(),
            "docking_used_for_selection": str(docking).lower(),
        })
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=REQUIRED_PREDICTION_COLUMNS)
            writer.writeheader()
            writer.writerow(row)
        return path

    def test_missing_artifact_fails_closed(self):
        missing = Path("/definitely/missing/predictions.csv")
        predictions, status = validate_predictions(missing, {"BDB-1": self.ledger()}, Path("/tmp"), expected_source_count=1)
        self.assertEqual(predictions, {})
        self.assertFalse(status["accepted"])
        self.assertIn("source_predictions_missing", status["errors"])

    def test_upper_bound_means_not_ruled_out_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_prediction_fixture(root, lower=6.5, upper=7.1)
            predictions, status = validate_predictions(path, {"BDB-1": self.ledger()}, root, expected_source_count=1)
        self.assertTrue(status["accepted"])
        self.assertEqual(predictions["BDB-1"]["interval_eligibility"], "screen_eligible_not_ruled_out")

    def test_lower_bound_is_required_for_robust_language(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_prediction_fixture(root, lower=6.75, upper=7.1)
            predictions, status = validate_predictions(path, {"BDB-1": self.ledger()}, root, expected_source_count=1)
        self.assertTrue(status["accepted"])
        self.assertEqual(predictions["BDB-1"]["interval_eligibility"], "robust_threshold_support")

    def test_outcome_or_docking_use_rejects_entire_artifact(self):
        for field in ("outcomes", "docking"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = self.write_prediction_fixture(root, **{field: True})
                predictions, status = validate_predictions(path, {"BDB-1": self.ledger()}, root, expected_source_count=1)
                self.assertEqual(predictions, {})
                self.assertFalse(status["accepted"])

    def test_missing_prediction_produces_non_ranked_blocked_record(self):
        record = record_for_dashboard(self.ledger(), None, 1, "a" * 64)
        self.assertEqual(record["interval_eligibility"], "not_assessed")
        self.assertEqual(record["deterministic_review_eligibility"], "blocked_missing_validated_prediction")
        self.assertNotIn("rank", record)
        self.assertNotIn("hit_probability", record)

    def test_set_rate_uses_wilson_interval(self):
        interval = wilson_rate(24, 240)
        self.assertEqual(interval["method"], "Wilson score interval")
        self.assertLess(interval["lower"], interval["estimate"])
        self.assertGreater(interval["upper"], interval["estimate"])
        self.assertEqual(wilson_rate(0, 0)["status"], "not_estimable_zero_denominator")

    def test_committed_fail_closed_queue_has_no_ranking_or_hit_probabilities(self):
        output = json.loads((self.ROOT / "outputs/v1.6/uncertainty_review_queue/uncertainty_review_queue.json").read_text())
        audit = json.loads((self.ROOT / "outputs/v1.6/uncertainty_review_queue/uncertainty_review_queue_audit.json").read_text())
        self.assertEqual(output["status"], "fail_closed_prediction_intake")
        self.assertEqual(len(output["records"]), 240)
        self.assertTrue(output["ranking_prohibited"])
        self.assertFalse(output["per_molecule_hit_probabilities_present"])
        self.assertTrue(all("rank" not in record and "hit_probability" not in record for record in output["records"]))
        self.assertTrue(all(record["interval_eligibility"] == "not_assessed" for record in output["records"]))
        self.assertFalse(audit["unverified_teammate_claims"]["verified"])
        self.assertTrue(audit["external_confirmation_floor"]["not_satisfied_by_review_shipment"])
        self.assertFalse(audit["governance"]["external_outcomes_loaded"])
        self.assertFalse(audit["governance"]["docking_used_for_selection"])
        status = json.loads((self.ROOT / "outputs/v1.6/implementation_status.json").read_text())
        queue_status = status["workstreams"]["B_external_confirmation"]["uncertainty_review_queue"]
        self.assertFalse(queue_status["claimed_335_and_276_verified"])
        self.assertTrue(queue_status["not_equivalent_to_external_confirmation"])

    def test_input_contract_columns_match_builder(self):
        contract = json.loads((self.ROOT / "config/uncertainty_review_queue_input.v1.json").read_text())
        self.assertEqual(contract["required_columns"], REQUIRED_PREDICTION_COLUMNS)

    def test_dashboard_payload_exposes_every_required_schema_field(self):
        schema = json.loads((self.ROOT / "dashboard_contracts/v1/uncertainty-review-queue.schema.json").read_text())
        output = json.loads((self.ROOT / "outputs/v1.6/uncertainty_review_queue/uncertainty_review_queue.json").read_text())
        self.assertTrue(set(schema["required"]).issubset(output))
        record_schema = schema["properties"]["records"]["items"]
        for record in output["records"]:
            self.assertEqual(set(record), set(record_schema["properties"]))
            self.assertTrue(set(record_schema["required"]).issubset(record))


if __name__ == "__main__":
    unittest.main()
