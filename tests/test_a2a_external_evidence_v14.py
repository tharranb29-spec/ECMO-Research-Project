import unittest

from track3_a2a.build_gtopdb_evidence_packet_v14 import adjudicate_candidate, normalized_class


class A2AExternalEvidenceV14Tests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"record_id": "EXT-1", "molecule_name": "Test", "source_id": "1"}
        self.primary_ref = {
            "referenceId": 1,
            "pmid": 12345,
            "type": "Journal",
            "title": "J Med Chem",
            "articleTitle": "Primary study",
            "year": 2025,
        }

    def interaction(self, action="Agonist", description="", refs=None):
        return {
            "interactionId": 10,
            "action": action,
            "assayDescription": description,
            "refs": refs or [],
        }

    def test_action_mapping_excludes_nonbinary_classes(self):
        self.assertEqual(normalized_class("Full agonist"), "agonist")
        self.assertEqual(normalized_class("Antagonist"), "antagonist")
        self.assertIsNone(normalized_class("Partial agonist"))

    def test_functional_description_and_primary_reference_still_needs_human_review(self):
        row = self.interaction(
            description="cAMP accumulation in cells expressing human A2A receptor",
            refs=[self.primary_ref],
        )
        result = adjudicate_candidate(self.candidate, [row])
        self.assertEqual(result["evidence_decision"], "provisional_functional_support_pending_dual_review")
        self.assertFalse(result["dataset_admission_eligible"])
        self.assertFalse(result["training_eligible"])

    def test_binding_only_description_is_rejected(self):
        row = self.interaction(
            action="Antagonist",
            description="Radioligand displacement binding assay",
            refs=[self.primary_ref],
        )
        result = adjudicate_candidate(self.candidate, [row])
        self.assertEqual(result["evidence_decision"], "reject_database_description_binding_only")

    def test_missing_description_routes_to_primary_paper_review(self):
        row = self.interaction(action="Antagonist", refs=[self.primary_ref])
        result = adjudicate_candidate(self.candidate, [row])
        self.assertEqual(result["evidence_decision"], "needs_primary_paper_review")

    def test_conflicting_actions_are_quarantined(self):
        rows = [self.interaction("Agonist"), self.interaction("Antagonist")]
        result = adjudicate_candidate(self.candidate, rows)
        self.assertEqual(result["evidence_decision"], "quarantine_action_conflict_or_unclassified")


if __name__ == "__main__":
    unittest.main()
