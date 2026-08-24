import unittest

from research_autoupdater import build_candidate_from_lead, resolve_verified_structure


class ResearchAutoupdaterStructureTests(unittest.TestCase):
    def test_verified_alias_resolves_to_reviewed_structure(self):
        structure = resolve_verified_structure("sialyl Lewis X", "Siglec-9")

        self.assertIsNotNone(structure)
        self.assertEqual(structure["candidate_name"], "sLeX")
        self.assertTrue(structure["approved_for_docking"])
        self.assertTrue(structure["ligand_sdf_path"].endswith("sLeX.sdf"))

    def test_unknown_lead_is_not_approved_for_docking(self):
        self.assertIsNone(resolve_verified_structure("invented glycan", "Siglec-9"))

    def test_autonomous_lead_receives_reviewed_docking_handoff(self):
        lead = {
            "candidate_name": "3'-sialyl-N-acetyllactosamine",
            "target_receptor": "Siglec-9",
            "modality_guess": "glycan",
            "lead_score": 78,
            "source_title": "Reviewed Siglec-9 ligand report",
            "rationale": "Named Siglec-9 ligand with reviewed coordinates.",
            "source_url": "https://example.org/reviewed-source",
            "source_method": "test",
            "article_id": "test-article",
            "publication_date": "2026-01-01",
            "is_new": True,
            "functional_direction": "binding_only",
        }

        candidate = build_candidate_from_lead(lead, [])

        self.assertTrue(candidate["approved_for_docking"])
        self.assertEqual(candidate["structure_status"], "verified_experimental_coordinates")
        self.assertEqual(candidate["receptor_path"], "docking_inputs/siglec9/siglec9_vset_18-144_ph7.4.pdb")
        self.assertEqual(candidate["box_center"], [22.5, 9.8, -36.0])
        self.assertTrue(candidate["ligand_sdf_path"].endswith("3SLN.sdf"))
        self.assertTrue(candidate["structure_sha256"])


if __name__ == "__main__":
    unittest.main()
