import unittest

from track3_a2a.freeze_provisional_partitions_v12 import HOLDOUT_TARGET, choose_holdout_groups


class A2AProvisionalPartitionTests(unittest.TestCase):
    def test_exact_class_target_without_scaffold_splitting(self):
        groups = {}
        for index in range(HOLDOUT_TARGET["agonist"] + 2):
            groups[f"a{index}"] = [{"functional_class": "agonist"}]
        for index in range(HOLDOUT_TARGET["antagonist"] + 2):
            groups[f"n{index}"] = [{"functional_class": "antagonist"}]
        selected = choose_holdout_groups(groups)
        selected_rows = [row for key in selected for row in groups[key]]
        self.assertEqual(sum(row["functional_class"] == "agonist" for row in selected_rows), HOLDOUT_TARGET["agonist"])
        self.assertEqual(sum(row["functional_class"] == "antagonist" for row in selected_rows), HOLDOUT_TARGET["antagonist"])


if __name__ == "__main__":
    unittest.main()
