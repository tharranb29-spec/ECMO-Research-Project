import unittest

from track3_a2a.triage_external_evidence_v16 import (
    assess_candidate,
    document_flags,
    normalize_doi,
    publication_is_primary,
)


class A2AExternalEvidenceTriageV16Tests(unittest.TestCase):
    def row(self):
        return {
            "candidate_id": "BDB-1", "bindingdb_monomer_id": "1", "standardized_smiles": "CC",
            "standardized_inchikey": "TEST", "generic_murcko_scaffold_smiles": "",
            "queue_rank": "1", "pmid": "123", "doi": "https://doi.org/10.1/test",
            # An outcome-like field must be ignored by assess_candidate.
            "sealed_exact_ki_measurement_count": "999",
        }

    def article(self):
        return {
            "pmid": "123", "doi": "10.1/TEST", "pmcid": "PMC1", "title": "Human A2A study",
            "abstract": "Binding affinity was measured as Ki.", "publication_types": ["Journal Article"],
        }

    def test_doi_normalization(self):
        self.assertEqual(normalize_doi("https://doi.org/10.1/TEST."), "10.1/test")

    def test_review_is_not_primary(self):
        self.assertFalse(publication_is_primary(["Journal Article", "Review"]))

    def test_document_flags_require_explicit_context(self):
        flags = document_flags("Human adenosine A2A receptor binding Ki")
        self.assertTrue(all(flags.values()))

    def test_abstract_never_admits(self):
        result = assess_candidate(self.row(), {"123": self.article()}, {})
        self.assertEqual(result["pass_1_status"], "metadata_pass_needs_fulltext")
        self.assertFalse(result["external_cohort_admitted"])
        self.assertNotIn("sealed_exact_ki_measurement_count", result)

    def test_identifier_disagreement_quarantines(self):
        article = self.article()
        article["doi"] = "10.1/different"
        result = assess_candidate(self.row(), {"123": article}, {})
        self.assertEqual(result["pass_1_status"], "quarantine_identifier_disagreement")
        self.assertFalse(result["pass_2_required"])

    def test_fulltext_ready_still_does_not_admit(self):
        fulltexts = {"PMC1": {"pmcid": "PMC1", "body_text": "Human A2A binding inhibition constant Ki."}}
        result = assess_candidate(self.row(), {"123": self.article()}, fulltexts)
        self.assertEqual(result["pass_1_status"], "metadata_pass_fulltext_ready")
        self.assertFalse(result["external_cohort_admitted"])

    def test_multiple_pmids_are_assessed_independently(self):
        row = self.row()
        row["pmid"] = "999|123"
        row["doi"] = "10.1/other|10.1/test"
        result = assess_candidate(row, {"123": self.article()}, {})
        self.assertEqual(result["pass_1_status"], "metadata_pass_needs_fulltext")
        self.assertEqual(result["missing_pmids"], ["999"])
        self.assertTrue(result["pass_2_required"])


if __name__ == "__main__":
    unittest.main()
