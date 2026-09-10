import unittest

import numpy as np

from track3_a2a.run_confirmatory_holdout_v131 import one_sided_permutation, transformed_design


class A2AConfirmatoryHoldoutV131Tests(unittest.TestCase):
    def rows(self, count, offset=0):
        rows = []
        for index in range(count):
            value = float(index + offset + 1)
            rows.append({
                "a": value,
                "b": value ** 2,
                "c": value % 3,
                "m": value / 3,
                "d": (-1 if index % 2 else 1) * value / 10,
            })
        return rows

    def test_development_fitted_transform_has_expected_shape(self):
        development = self.rows(12)
        holdout = self.rows(5, offset=20)
        dev, test, variance = transformed_design(development, holdout, ["a", "b", "c"], ["m", "d"])
        self.assertEqual(dev.shape, (12, 5))
        self.assertEqual(test.shape, (5, 5))
        self.assertGreater(variance, 0)
        self.assertTrue(np.allclose(dev.mean(axis=0), 0, atol=1e-10))

    def test_one_sided_permutation_is_reproducible(self):
        design = np.column_stack([np.arange(20), np.linspace(-1, 1, 20)])
        labels = np.asarray([0] * 10 + [1] * 10)
        first = one_sided_permutation(design, labels, 1, 100, 7)
        second = one_sided_permutation(design, labels, 1, 100, 7)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first["one_sided_p_value"], 0)
        self.assertLessEqual(first["one_sided_p_value"], 1)


if __name__ == "__main__":
    unittest.main()
