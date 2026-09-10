import unittest

from track3_a2a.ingest_chembl_functional import activity_class, infer_description_class


class A2AChEMBLIngestTests(unittest.TestCase):
    def test_explicit_action_type_is_preferred(self):
        label, reason = activity_class({"action_type": "AGONIST", "assay_description": "Functional response"})
        self.assertEqual((label, reason), ("agonist", "chembl_action_type"))

    def test_inverse_and_partial_agonists_remain_separate(self):
        self.assertEqual(activity_class({"action_type": "INVERSE AGONIST"})[0], "inverse_agonist")
        self.assertEqual(activity_class({"action_type": "PARTIAL AGONIST"})[0], "partial_agonist")

    def test_conflicting_action_and_description_is_not_admitted(self):
        label, reason = activity_class({"action_type": "AGONIST", "assay_description": "Antagonist activity"})
        self.assertIsNone(label)
        self.assertEqual(reason, "action_description_conflict")

    def test_ambiguous_description_has_no_class(self):
        self.assertIsNone(infer_description_class("Binding affinity measured by radioligand displacement"))


if __name__ == "__main__":
    unittest.main()

