import unittest

import numpy as np

from track3_a2a.run_model_evaluation_v12 import metric_set, percentile_interval


class A2AModelEvaluationV12Tests(unittest.TestCase):
    def test_metrics_use_agonist_as_positive_class(self):
        metrics = metric_set(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]), 0.5)
        self.assertEqual(metrics["roc_auc"], 1.0)
        self.assertEqual(metrics["sensitivity"], 1.0)
        self.assertEqual(metrics["specificity"], 1.0)

    def test_percentile_interval_is_ordered(self):
        interval = percentile_interval([0.1, 0.2, 0.3, 0.4], 0.95)
        self.assertLessEqual(interval["lower"], interval["estimate"])
        self.assertLessEqual(interval["estimate"], interval["upper"])


if __name__ == "__main__":
    unittest.main()
