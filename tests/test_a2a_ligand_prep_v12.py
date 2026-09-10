import unittest

from track3_a2a.prepare_provisional_ligands_v12 import canonical_variants, embed_variant, seed_for


class A2ALigandPreparationTests(unittest.TestCase):
    CONFIG = {"protonation": {"ph_min": 7.4, "ph_max": 7.4, "precision": 0.1, "max_variants": 16}}

    def test_carboxylic_acid_is_deprotonated_at_ph_7_4(self):
        self.assertEqual(canonical_variants("CC(=O)O", self.CONFIG), ["CC(=O)[O-]"])

    def test_seed_is_deterministic_and_positive(self):
        self.assertEqual(seed_for("CHEMBL1", 1), seed_for("CHEMBL1", 1))
        self.assertGreater(seed_for("CHEMBL1", 1), 0)

    def test_embedding_produces_one_conformer(self):
        molecule, optimization, _ = embed_variant("c1ccncc1", 42)
        self.assertEqual(molecule.GetNumConformers(), 1)
        self.assertIn(optimization, {"MMFF94", "UFF"})


if __name__ == "__main__":
    unittest.main()
