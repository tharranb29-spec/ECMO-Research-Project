import unittest

from track3_a2a.freeze_computational_partitions_v13 import reconcile_partitions


class A2AComputationalPartitionsV13Tests(unittest.TestCase):
    def test_membership_is_preserved_and_training_excludes_holdout(self):
        curated = [
            {"chembl_id": "A", "molecule_name": "A", "functional_class": "agonist", "primary_binary_label": 1, "evidence_tier": "tier_1", "standardized_smiles": "C", "standardized_inchikey": "A", "generic_murcko_scaffold_smiles": "s1"},
            {"chembl_id": "B", "molecule_name": "B", "functional_class": "antagonist", "primary_binary_label": 0, "evidence_tier": "tier_1", "standardized_smiles": "CC", "standardized_inchikey": "B", "generic_murcko_scaffold_smiles": "s2"},
        ]
        frozen = [
            {"chembl_id": "A", "partition": "provisional_development"},
            {"chembl_id": "B", "partition": "provisional_locked_holdout"},
        ]
        rows = reconcile_partitions(curated, frozen, {"A", "B"})
        by_id = {row["chembl_id"]: row for row in rows}
        self.assertTrue(by_id["A"]["training_eligible"])
        self.assertFalse(by_id["B"]["training_eligible"])
        self.assertTrue(by_id["B"]["holdout_evaluation_eligible"])

    def test_population_change_cannot_silently_reselect_holdout(self):
        with self.assertRaises(ValueError):
            reconcile_partitions([{"chembl_id": "A"}], [{"chembl_id": "B"}], set())

    def test_subtractive_exclusion_preserves_surviving_membership(self):
        curated = [
            {"chembl_id": "A", "molecule_name": "A", "functional_class": "agonist", "primary_binary_label": 1, "evidence_tier": "tier_1", "standardized_smiles": "C", "standardized_inchikey": "A", "generic_murcko_scaffold_smiles": "s1"},
        ]
        frozen = [
            {"chembl_id": "A", "partition": "provisional_development"},
            {"chembl_id": "B", "partition": "provisional_locked_holdout"},
        ]
        rows = reconcile_partitions(curated, frozen, {"A"})
        self.assertEqual([row["chembl_id"] for row in rows], ["A"])
        self.assertEqual(rows[0]["partition"], "development")


if __name__ == "__main__":
    unittest.main()
