import unittest

from track3_a2a.ai_assisted_review_v12 import assess_record, is_primary_source_candidate


class A2AAIReviewV12Tests(unittest.TestCase):
    def test_review_title_is_not_treated_as_primary_evidence(self):
        document = {"document_type": "PUBLICATION", "doi": "10.1/x", "title": "Recent advances and perspective"}
        self.assertFalse(is_primary_source_candidate(document))

    def test_direct_human_a2a_functional_evidence_is_provisionally_tier_1(self):
        plan = {"chembl_id": "CHEMBL1", "molecule_name": "Example", "curation_batch": "1", "proposed_class": "agonist"}
        packet = {"functional_evidence": [{
            "activity_id": 1, "assay_chembl_id": "A1", "document_chembl_id": "D1",
            "description": "Agonist activity assessed by intracellular cAMP accumulation",
            "proposed_functional_class": "agonist"
        }]}
        docs = {"D1": {"document_chembl_id": "D1", "document_type": "PUBLICATION", "doi": "10.1/x", "title": "Experimental study"}}
        assays = {"A1": {"assay_chembl_id": "A1", "target_chembl_id": "CHEMBL251", "organism": "Homo sapiens", "confidence_score": 9}}
        result = assess_record(plan, packet, docs, assays)
        self.assertEqual(result["recommended_evidence_tier"], "tier_1")
        self.assertFalse(result["training_eligible"])


if __name__ == "__main__":
    unittest.main()
