import unittest

import numpy as np

from track3_a2a.run_mechanistic_analysis_v12 import fit_coefficient


class A2AMechanisticAnalysisV12Tests(unittest.TestCase):
    def test_positive_last_feature_has_positive_coefficient(self):
        labels = np.asarray([0, 0, 0, 1, 1, 1])
        design = np.column_stack([np.zeros(6), np.asarray([-3, -2, -1, 1, 2, 3])])
        self.assertGreater(fit_coefficient(design, labels, -1), 0)

    def test_coefficient_index_selects_requested_feature(self):
        labels = np.asarray([0, 0, 0, 1, 1, 1])
        design = np.column_stack([np.asarray([-3, -2, -1, 1, 2, 3]), np.zeros(6)])
        self.assertGreater(fit_coefficient(design, labels, 0), 0)


if __name__ == "__main__":
    unittest.main()
