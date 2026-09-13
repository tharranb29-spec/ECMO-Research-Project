import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestA2AOpenMMBenchmarkV15(unittest.TestCase):
    def test_benchmark_did_not_start_a_project_trajectory(self):
        path = ROOT / "track3_a2a" / "outputs" / "v1.5" / "md" / "openmm_cpu_benchmark.json"
        report = json.loads(path.read_text())
        self.assertEqual(report["platform"], "CPU")
        self.assertGreater(report["atom_count"], 20000)
        self.assertGreater(report["throughput_ns_per_day"], 0)
        self.assertFalse(report["trajectory_production_started"])


if __name__ == "__main__":
    unittest.main()
