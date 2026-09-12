import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class A2AProtocolV15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activity = json.loads(
            (A2A / "config" / "continuous_activity.v1.5.json").read_text(encoding="utf-8")
        )
        cls.md = json.loads(
            (A2A / "config" / "md_validation.v1.5.json").read_text(encoding="utf-8")
        )

    def test_historical_results_cannot_be_recast_as_confirmatory(self):
        boundary = self.activity["historical_boundary"]
        self.assertTrue(boundary["historical_214_activity_results_already_seen"])
        self.assertTrue(boundary["corrected_203_activity_results_already_seen"])
        self.assertFalse(boundary["use_current_activity_results_for_confirmatory_claim"])
        self.assertTrue(boundary["locked_v1_3_1_holdout_must_not_be_reused_for_model_selection"])

    def test_binding_and_functional_endpoints_are_separate(self):
        endpoints = self.activity["endpoints"]
        self.assertEqual(endpoints["primary_pbind"]["allowed_standard_types"], ["Ki"])
        self.assertFalse(endpoints["primary_pbind"]["pool_with_other_endpoints"])
        self.assertFalse(endpoints["secondary_pfunc_agonism"]["pool_with_other_endpoints"])
        self.assertFalse(endpoints["secondary_pfunc_inhibition"]["pool_with_other_endpoints"])
        self.assertFalse(endpoints["inverse_agonism"]["pool_with_antagonist_inhibition"])

    def test_llm_docking_and_md_cannot_create_labels_or_rescue_failure(self):
        self.assertFalse(self.activity["measurement_admission"]["llm_can_admit_measurement"])
        self.assertFalse(self.activity["applicability_domain"]["docking_is_automatic_fallback"])
        self.assertFalse(self.activity["md_linkage"]["can_create_activity_labels"])
        self.assertFalse(self.activity["md_linkage"]["can_rescue_failed_external_qsar_gate"])
        self.assertFalse(self.md["can_create_activity_labels"])
        self.assertFalse(self.md["can_rescue_failed_qsar_gate"])

    def test_external_confirmation_requires_independence_and_minimum_coverage(self):
        external = self.activity["external_confirmation"]
        self.assertGreaterEqual(external["minimum_primary_pbind_molecules"], 60)
        self.assertGreaterEqual(external["minimum_primary_pbind_generic_scaffolds"], 20)
        self.assertTrue(external["no_exact_or_generic_scaffold_overlap_with_model_selection_data"])
        self.assertTrue(external["one_time_unmask"])

    def test_md_plan_is_bounded_blinded_and_replicated(self):
        candidates = self.md["tiers"]["tier_b_blinded_candidates"]
        self.assertEqual(len(candidates["candidate_ids"]), 4)
        self.assertEqual(set(candidates["receptor_structures"]), {"5NM4", "2YDO"})
        self.assertEqual(self.md["simulation"]["replicas"], 3)
        self.assertGreaterEqual(self.md["simulation"]["production_ns_per_replica"], 100)
        self.assertEqual(len(self.md["simulation"]["replica_seeds"]), 3)
        self.assertEqual(self.md["simulation"]["best_replica_selection"], "prohibited")
        self.assertEqual(len(self.md["tiers"]["tier_a_controls"]), 2)

    def test_activity_templates_are_empty_and_have_required_provenance_fields(self):
        measurement_path = A2A / "data" / "curated" / "activity_measurements_v15_template.csv"
        summary_path = A2A / "data" / "curated" / "activity_molecule_summary_v15_template.csv"
        with measurement_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(list(reader), [])
            fields = set(reader.fieldnames or [])
        self.assertTrue(
            {
                "measurement_id",
                "standardized_inchikey",
                "endpoint_name",
                "assay_chembl_id",
                "document_chembl_id",
                "doi",
                "pmid",
                "review_status",
            }.issubset(fields)
        )
        with summary_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(list(reader), [])
            summary_fields = set(reader.fieldnames or [])
        self.assertTrue(
            {"aggregated_pactivity", "interassay_sd", "external_eligibility"}.issubset(
                summary_fields
            )
        )

    def test_protocol_status_hashes_reconcile(self):
        status = json.loads(
            (A2A / "outputs" / "v1.5" / "protocol_status.json").read_text(encoding="utf-8")
        )
        paths = {
            "continuous_activity_config": A2A / "config" / "continuous_activity.v1.5.json",
            "continuous_activity_protocol": A2A / "CONTINUOUS_ACTIVITY_PROTOCOL_V15.md",
            "md_config": A2A / "config" / "md_validation.v1.5.json",
            "md_plan": A2A / "MD_VALIDATION_PLAN_V15.md",
            "measurement_template": A2A
            / "data"
            / "curated"
            / "activity_measurements_v15_template.csv",
            "molecule_summary_template": A2A
            / "data"
            / "curated"
            / "activity_molecule_summary_v15_template.csv",
        }
        for name, path in paths.items():
            self.assertEqual(status["protocol_hashes"][name], sha256(path))
        self.assertFalse(status["new_confirmatory_potency_labels_loaded"])
        self.assertFalse(status["md_candidate_trajectories_started"])


if __name__ == "__main__":
    unittest.main()
