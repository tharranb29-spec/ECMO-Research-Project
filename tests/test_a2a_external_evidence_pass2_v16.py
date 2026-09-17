import unittest

from track3_a2a.extract_external_evidence_pass2_v16 import (
    AGREEMENT_FIELDS,
    assess_record,
    categorical_source_fields,
)


class A2AExternalEvidencePass2V16Tests(unittest.TestCase):
    def record(self):
        return {
            "queue_rank": 1,
            "candidate_id": "BDB-1",
            "bindingdb_monomer_id": "1001",
            "standardized_smiles": "C[C@H](O)N",
            "standardized_inchikey": "TEST-INCHIKEY",
            "generic_murcko_scaffold_smiles": "C1CC1",
            "pass_1_status": "metadata_pass_fulltext_ready",
        }

    def document(self, include_identity=True):
        identity = " TEST-INCHIKEY" if include_identity else ""
        return {
            "pmcid": "PMC1",
            "source_url": "https://example.test/PMC1",
            "raw_xml_sha256": "a" * 64,
            "body_text": (
                "Wild-type human adenosine A2A receptor radioligand binding assay. "
                "The endpoint table reports Ki (nM)." + identity
            ),
        }

    def test_all_frozen_fields_can_resolve_without_numeric_outcome(self):
        fields = categorical_source_fields(self.record(), self.document())
        self.assertTrue(all(fields[name]["resolved"] for name in AGREEMENT_FIELDS))
        self.assertEqual(fields["stereochemistry"]["value"], "defined_as_queued")

    def test_admission_still_requires_exact_pass1_field_agreement(self):
        record = self.record()
        record["pmcids"] = "PMC1"
        fields = categorical_source_fields(record, self.document())
        record["pass_1_extracted_fields"] = {name: fields[name]["value"] for name in AGREEMENT_FIELDS}
        result = assess_record(record, {"PMC1": self.document()})
        self.assertEqual(result["pass_2_status"], "accept")
        self.assertTrue(result["pass_1_pass_2_exact_agreement"])
        self.assertEqual(result["final_membership_decision"], "admit")

    def test_missing_structure_identifier_quarantines(self):
        record = self.record()
        record["pmcids"] = "PMC1"
        result = assess_record(record, {"PMC1": self.document(include_identity=False)})
        self.assertEqual(result["pass_2_status"], "quarantine")
        self.assertIn("unresolved_molecule_identity", result["quarantine_reasons"])
        self.assertIn("unresolved_stereochemistry", result["quarantine_reasons"])
        self.assertFalse(result["numeric_ki_extracted"])
        self.assertFalse(result["outcome_fields_loaded"])

    def test_missing_full_text_quarantines(self):
        record = self.record()
        record["pmcids"] = ""
        result = assess_record(record, {})
        self.assertEqual(result["pass_2_status"], "quarantine")
        self.assertEqual(result["quarantine_reasons"], ["retrieved_primary_full_text_unavailable"])

    def test_pass1_rejection_cannot_be_repaired(self):
        record = self.record()
        record["pass_1_status"] = "quarantine_nonprimary_source"
        record["pmcids"] = "PMC1"
        result = assess_record(record, {"PMC1": self.document()})
        self.assertEqual(result["final_membership_decision"], "quarantine")
        self.assertIn("pass_1_rejected", result["quarantine_reasons"])


if __name__ == "__main__":
    unittest.main()
