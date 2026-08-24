import unittest

from gnina_pipeline import (
    assign_uncertainty_ranks,
    candidate_dockability,
    experimental_pkd,
    run_docking_pipeline,
    spearman_with_exact_p,
)


class GninaPipelineTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {
            "id": "auto_demo_siglec9",
            "candidate_name": "Demo glycomimetic",
            "target_receptor": "Siglec-9",
            "modality": "glycomimetic",
            "source_batch": "test-batch",
        }

    def test_prototype_is_deterministic_and_explicitly_simulated(self):
        first = run_docking_pipeline([self.candidate], mode="prototype", run_count=5, persist=False)
        second = run_docking_pipeline([self.candidate], mode="prototype", run_count=5, persist=False)
        self.assertTrue(first["simulated"])
        self.assertEqual(first["scientific_status"], "workflow_demonstration_only")
        self.assertEqual(first["results"], second["results"])
        self.assertEqual(first["completed_count"], 1)
        self.assertEqual(first["results"][0]["run_count"], 5)

    def test_protein_is_not_forced_through_small_molecule_docking(self):
        protein = {**self.candidate, "id": "protein", "modality": "protein"}
        payload = run_docking_pipeline([protein], mode="prototype", persist=False)
        self.assertEqual(payload["completed_count"], 0)
        self.assertEqual(payload["results"][0]["status"], "unsupported_modality")

    def test_experimental_kd_is_normalized_to_pkd(self):
        self.assertAlmostEqual(experimental_pkd({"experimental_kd_value": 100, "experimental_kd_unit": "nM"}), 7.0)
        self.assertIsNone(experimental_pkd({"experimental_kd_value": 100, "experimental_kd_unit": ""}))

    def test_spearman_reports_perfect_rank_agreement(self):
        rho, p_value = spearman_with_exact_p([1, 2, 3, 4, 5], [10, 20, 30, 40, 50])
        self.assertAlmostEqual(rho, 1.0)
        self.assertAlmostEqual(p_value, 2 / 120)

    def test_simulated_results_are_excluded_from_experimental_validation(self):
        payload = run_docking_pipeline(
            [{**self.candidate, "experimental_kd_value": 100, "experimental_kd_unit": "nM"}],
            mode="prototype",
            persist=False,
        )
        validation = payload["experimental_validation"]
        self.assertEqual(validation["matched_candidate_count"], 0)
        self.assertEqual(validation["status"], "awaiting_matched_experimental_data")

    def test_unapproved_manifest_candidate_is_blocked(self):
        status, reason = candidate_dockability(
            {**self.candidate, "ligand_sdf_path": "candidate.sdf", "approved_for_docking": False},
            mode="local",
        )
        self.assertEqual(status, "review_required")
        self.assertIn("not approved", reason)

    def test_real_mode_requires_verified_prepared_structure(self):
        status, reason = candidate_dockability(self.candidate, mode="local")
        self.assertEqual(status, "awaiting_structure")
        self.assertIn("SDF", reason)

    def test_comparative_order_is_retained_when_pose_gate_blocks_validated_rank(self):
        results = [
            {
                "candidate_name": "weaker",
                "target_receptor": "Siglec-9",
                "status": "completed",
                "pose_quality_status": "review",
                "minimized_affinity_mean_kcal_mol": -6.1,
                "cnn_score_mean": 0.4,
                "run_count": 5,
            },
            {
                "candidate_name": "stronger",
                "target_receptor": "Siglec-9",
                "status": "completed",
                "pose_quality_status": "review",
                "minimized_affinity_mean_kcal_mol": -7.0,
                "cnn_score_mean": 0.3,
                "run_count": 5,
            },
        ]

        assign_uncertainty_ranks(results)

        stronger = next(item for item in results if item["candidate_name"] == "stronger")
        weaker = next(item for item in results if item["candidate_name"] == "weaker")
        self.assertEqual(stronger["comparative_affinity_rank"], 1)
        self.assertEqual(weaker["comparative_affinity_rank"], 2)
        self.assertNotIn("gnina_rank", stronger)
        self.assertNotIn("gnina_rank", weaker)


if __name__ == "__main__":
    unittest.main()
