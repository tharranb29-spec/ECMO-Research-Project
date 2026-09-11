import unittest

from track3_a2a.screen_pubchem_assays_v14 import (
    action_direction,
    direct_human_a2a_target,
    publication_identifiers,
    screen_assay,
)


class A2APubchemScreenV14Tests(unittest.TestCase):
    def base_assay(self):
        return {
            "AID": 1,
            "SourceName": "Independent",
            "SourceID": "X",
            "Name": "Antagonist activity at human A2A receptor",
            "Description": ["cAMP assay. PMID: 12345 DOI: 10.1000/test"],
            "Target": [{"Accession": "P29274", "Name": "Adenosine receptor A2a"}],
            "CIDCountAll": 2,
        }

    def test_direct_target_requires_one_exact_accession(self):
        row = self.base_assay()
        self.assertTrue(direct_human_a2a_target(row))
        row["Target"].append({"Accession": "OTHER"})
        self.assertFalse(direct_human_a2a_target(row))

    def test_action_direction_prioritizes_antagonist(self):
        self.assertEqual(action_direction({"Name": "A2A antagonist assay"}), "antagonist")
        self.assertEqual(action_direction({"Name": "A2A agonist activity"}), "agonist")

    def test_publication_identifiers_are_extracted(self):
        result = publication_identifiers("PMID: 12345 DOI: 10.1000/test.")
        self.assertEqual(result["pmids"], ["12345"])
        self.assertEqual(result["dois"], ["10.1000/test"])

    def test_complete_independent_functional_assay_is_eligible(self):
        result = screen_assay(self.base_assay())
        self.assertTrue(result["evidence_eligible"])

    def test_chembl_mirror_and_patent_without_publication_are_rejected(self):
        row = self.base_assay()
        row.update({
            "SourceName": "ChEMBL",
            "Name": "A2A antagonist cAMP assay from US Patent 123",
            "Description": [],
        })
        result = screen_assay(row)
        self.assertFalse(result["evidence_eligible"])
        self.assertIn("chembl_mirror", result["screening_reasons"])
        self.assertIn("patent_only_evidence", result["screening_reasons"])


if __name__ == "__main__":
    unittest.main()
