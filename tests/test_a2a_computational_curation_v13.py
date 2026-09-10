import json
import unittest
from pathlib import Path

from track3_a2a.run_computational_curation_v13 import adjudicate_record, is_primary_source


ROOT = Path(__file__).resolve().parents[1]


def evidence(description="Agonist activity assessed by cAMP production", functional_class="agonist"):
    return {
        "activity_id": 1,
        "assay_chembl_id": "A1",
        "document_chembl_id": "D1",
        "description": description,
        "proposed_functional_class": functional_class,
    }


class A2AComputationalCurationV13Tests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "track3_a2a/config/computational_curation.v1.3.json").read_text())
        self.plan = {"chembl_id": "CHEMBL1", "molecule_name": "Example", "curation_batch": "1", "proposed_class": "agonist"}
        self.assays = {"A1": {"assay_chembl_id": "A1", "target_chembl_id": "CHEMBL251", "organism": "Homo sapiens", "confidence_score": 9, "chembl_url": "https://example/assay"}}
        self.documents = {"D1": {"document_chembl_id": "D1", "document_type": "PUBLICATION", "doi": "10.1/example", "pubmed_id": None, "title": "Experimental A2A study", "doi_url": "https://doi.org/10.1/example", "pubmed_url": None, "chembl_url": "https://example/doc"}}

    def test_direct_functional_primary_evidence_is_admitted(self):
        result = adjudicate_record(self.plan, {"functional_evidence": [evidence()]}, self.assays, self.documents, self.config)
        self.assertEqual(result["decision"], "accept_agonist")
        self.assertEqual(result["evidence_tier"], "tier_1")
        self.assertFalse(result["human_validation_claimed"])
        self.assertFalse(result["training_eligible"])

    def test_review_article_cannot_admit(self):
        documents = {"D1": {**self.documents["D1"], "title": "A review and perspective"}}
        result = adjudicate_record(self.plan, {"functional_evidence": [evidence()]}, self.assays, documents, self.config)
        self.assertEqual(result["decision"], "needs_full_text")

    def test_wrong_organism_is_rejected_from_binary_endpoint(self):
        assays = {"A1": {**self.assays["A1"], "organism": "Rattus norvegicus"}}
        result = adjudicate_record(self.plan, {"functional_evidence": [evidence()]}, assays, self.documents, self.config)
        self.assertEqual(result["decision"], "reject_context")

    def test_conflicting_class_is_quarantined(self):
        packet = {"functional_evidence": [evidence(), evidence(functional_class="antagonist")]}
        result = adjudicate_record(self.plan, packet, self.assays, self.documents, self.config)
        self.assertEqual(result["decision"], "quarantine_conflict")

    def test_raw_inverse_agonist_evidence_overrides_binary_admission(self):
        excluded = [{
            "functional_class": "inverse_agonist",
            "classification_rule": "assay_description_rule",
            "activity_id": 2,
            "assay_chembl_id": "A2",
            "document_chembl_id": "D2",
        }]
        result = adjudicate_record(
            self.plan,
            {"functional_evidence": [evidence()]},
            self.assays,
            self.documents,
            self.config,
            excluded,
        )
        self.assertEqual(result["decision"], "quarantine_excluded_function")
        self.assertFalse(result["dataset_admission_eligible"])
        self.assertEqual(result["excluded_functional_classes"], ["inverse_agonist"])

    def test_llm_or_model_confidence_is_not_an_admission_input(self):
        self.assertTrue(self.config["separation_of_gates"]["auc_must_not_validate_labels"])
        self.assertIn("cannot admit", self.config["curation_mode"]["llm_role"])

    def test_primary_source_requires_identifier(self):
        self.assertFalse(is_primary_source({"document_type": "PUBLICATION", "title": "Study"}))


if __name__ == "__main__":
    unittest.main()
