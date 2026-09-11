import unittest

from track3_a2a.triage_gtopdb_primary_evidence_v14 import (
    action_is_mentioned,
    candidate_context,
    candidate_is_mentioned,
    triage_record,
)


class A2APrimaryEvidenceTriageV14Tests(unittest.TestCase):
    def test_candidate_matching_normalizes_punctuation_and_case(self):
        self.assertTrue(candidate_is_mentioned("ZM-241385", "The effects of zm 241385 were measured."))

    def test_action_matching_does_not_map_partial_agonist_to_antagonist(self):
        self.assertTrue(action_is_mentioned("agonist", "a partial agonist response"))
        self.assertFalse(action_is_mentioned("antagonist", "a partial agonist response"))

    def test_candidate_context_does_not_borrow_distant_functional_evidence(self):
        abstract = (
            "TEST-1 was measured in a binding assay. Another compound was discussed. "
            "A third compound increased cAMP in human A2A cells."
        )
        context = candidate_context("TEST-1", "Study", abstract)
        self.assertNotIn("increased cAMP", context)

    def test_abstract_triage_never_admits_a_label(self):
        record = {
            "record_id": "EXT-1",
            "molecule_name": "TEST-1",
            "proposed_functional_class": "agonist",
            "evidence_rows": [{"primary_references": [{"pmid": "1"}]}],
        }
        articles = {"1": {
            "pmid": "1",
            "doi": "10.1/test",
            "pmcid": "PMC1",
            "title": "TEST-1 is a human A2A agonist",
            "abstract": "TEST-1 increased cAMP in human A2A-expressing cells.",
        }}
        result = triage_record(record, articles)
        self.assertEqual(result["abstract_triage_status"], "high_priority_full_text_review")
        self.assertFalse(result["dataset_admission_eligible"])
        self.assertFalse(result["training_eligible"])


if __name__ == "__main__":
    unittest.main()
