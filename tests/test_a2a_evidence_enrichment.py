import unittest

from track3_a2a.enrich_batch1_evidence import assay_summary, document_summary


class A2AEvidenceEnrichmentTests(unittest.TestCase):
    def test_document_links_are_created(self):
        result = document_summary({
            "document_chembl_id": "CHEMBL1",
            "doi": "10.1000/example",
            "pubmed_id": 123,
        })
        self.assertEqual(result["doi_url"], "https://doi.org/10.1000/example")
        self.assertEqual(result["pubmed_url"], "https://pubmed.ncbi.nlm.nih.gov/123/")

    def test_assay_target_is_preserved(self):
        result = assay_summary({"assay_chembl_id": "CHEMBL2", "target_chembl_id": "CHEMBL251"})
        self.assertEqual(result["target_chembl_id"], "CHEMBL251")


if __name__ == "__main__":
    unittest.main()
