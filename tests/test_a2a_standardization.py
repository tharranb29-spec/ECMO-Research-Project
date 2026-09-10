import importlib.util
import unittest


RDKIT_AVAILABLE = importlib.util.find_spec("rdkit") is not None


@unittest.skipUnless(RDKIT_AVAILABLE, "RDKit is installed in the isolated Track 3 environment")
class A2AStandardizationTests(unittest.TestCase):
    def test_salts_are_reduced_to_a_parent_structure(self):
        from track3_a2a.standardize_quarantine import standardize_smiles

        result = standardize_smiles("CC(=O)O.[Na+]")
        self.assertNotIn(".", result["standardized_smiles"])
        self.assertEqual(result["descriptors"]["heavy_atom_count"], 4)

    def test_scaffold_and_descriptor_fields_are_created(self):
        from track3_a2a.standardize_quarantine import standardize_smiles

        result = standardize_smiles("c1ccccc1CCN")
        self.assertTrue(result["murcko_scaffold_smiles"])
        self.assertGreater(result["descriptors"]["molecular_weight"], 0)
        self.assertIn("qed_above_0_3", result["property_filters"])


if __name__ == "__main__":
    unittest.main()

