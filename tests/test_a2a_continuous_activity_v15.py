import unittest

from track3_a2a.build_continuous_activity_v15 import (
    admission_reasons,
    endpoint_for,
    functional_mode,
)


class A2AContinuousActivityV15Tests(unittest.TestCase):
    def test_endpoints_remain_separate(self):
        self.assertEqual(endpoint_for({"assay_type": "B", "standard_type": "Ki"}, None), "pBind_Ki")
        self.assertIsNone(endpoint_for({"assay_type": "B", "standard_type": "Kd"}, None))
        self.assertEqual(endpoint_for({"assay_type": "F", "standard_type": "EC50"}, "agonist"), "pFunc_agonism")
        self.assertEqual(endpoint_for({"assay_type": "F", "standard_type": "IC50"}, "antagonist"), "pFunc_inhibition")
        self.assertIsNone(endpoint_for({"assay_type": "F", "standard_type": "IC50"}, "agonist"))

    def test_inhibition_of_agonist_stimulated_response_is_antagonism(self):
        activity = {
            "action_type": None,
            "assay_description": "Inhibition of CGS21680-stimulated cAMP accumulation",
            "activity_comment": None,
        }
        mode, source = functional_mode(activity, {})
        self.assertEqual(mode, "antagonist")
        self.assertEqual(source, "assay_text_rule")

    def test_inverse_and_partial_agonism_are_not_pooled(self):
        inverse, _ = functional_mode({"assay_description": "inverse agonist at human A2A"}, {})
        partial, _ = functional_mode({"assay_description": "partial agonist at human A2A"}, {})
        self.assertEqual(inverse, "inverse_agonist")
        self.assertEqual(partial, "partial_agonist")
        self.assertEqual(
            endpoint_for({"assay_type": "F", "standard_type": "IC50"}, inverse),
            "pFunc_inverse_agonism",
        )
        self.assertIsNone(endpoint_for({"assay_type": "F", "standard_type": "EC50"}, partial))

    def test_admission_gate_accepts_complete_primary_measurement(self):
        activity = {
            "target_chembl_id": "CHEMBL251",
            "target_organism": "Homo sapiens",
            "standard_relation": "=",
            "standard_units": "nM",
            "standard_value": "100",
            "pchembl_value": "7.00",
            "data_validity_comment": None,
            "assay_variant_mutation": None,
        }
        assay = {
            "target_chembl_id": "CHEMBL251",
            "assay_organism": "Homo sapiens",
            "confidence_score": 9,
            "variant_sequence": None,
        }
        document = {"doc_type": "PUBLICATION", "doi": "10.1/example", "pubmed_id": None}
        target = {"target_type": "SINGLE PROTEIN"}
        molecule = {
            "standardized_inchikey": "RYYVLZVUVIJVGH-UHFFFAOYSA-N",
            "standardized_smiles": "Cn1c(=O)c2c(ncn2C)n(C)c1=O",
        }
        self.assertEqual(
            admission_reasons(activity, assay, document, target, molecule, "pBind_Ki", 7.0),
            [],
        )

    def test_admission_gate_rejects_censored_mutant_review(self):
        activity = {
            "target_chembl_id": "CHEMBL251",
            "target_organism": "Homo sapiens",
            "standard_relation": ">",
            "standard_units": "nM",
            "standard_value": "100",
            "pchembl_value": "7.00",
            "data_validity_comment": None,
            "assay_variant_mutation": "A63G",
        }
        reasons = admission_reasons(
            activity,
            {"target_chembl_id": "CHEMBL251", "assay_organism": "Homo sapiens", "confidence_score": 9},
            {"doc_type": "REVIEW", "doi": "10.1/review"},
            {"target_type": "SINGLE PROTEIN"},
            {"standardized_inchikey": "RYYVLZVUVIJVGH-UHFFFAOYSA-N", "standardized_smiles": "Cn1c(=O)c2c(ncn2C)n(C)c1=O"},
            "pBind_Ki",
            7.0,
        )
        self.assertIn("non_exact_relation", reasons)
        self.assertIn("mutant_or_variant_assay", reasons)
        self.assertIn("not_primary_publication", reasons)


if __name__ == "__main__":
    unittest.main()
