import unittest

from gnina_pipeline import candidate_dockability, run_docking_pipeline


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

    def test_real_mode_requires_verified_prepared_structure(self):
        status, reason = candidate_dockability(self.candidate, mode="local")
        self.assertEqual(status, "awaiting_structure")
        self.assertIn("SDF", reason)


if __name__ == "__main__":
    unittest.main()
