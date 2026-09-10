import unittest

from track3_a2a.build_evidence_review_queue import classify_readout


class A2AEvidenceGateTests(unittest.TestCase):
    def test_radioligand_assay_is_binding_only(self):
        text = "Antagonist activity assessed in a [3H] radioligand displacement assay"
        self.assertEqual(classify_readout(text), "binding_only")

    def test_camp_assay_is_functional(self):
        text = "Agonist activity assessed as increase in intracellular cAMP"
        self.assertEqual(classify_readout(text), "functional")

    def test_functional_readout_wins_when_binding_is_context_only(self):
        text = "Inhibition of forskolin-stimulated cAMP in the presence of radioligand"
        self.assertEqual(classify_readout(text), "functional")

    def test_unresolved_description_is_not_promoted(self):
        self.assertEqual(classify_readout("Activity at human A2A receptor"), "unresolved")


if __name__ == "__main__":
    unittest.main()
