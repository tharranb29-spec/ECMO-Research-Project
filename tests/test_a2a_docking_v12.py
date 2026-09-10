import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from track3_a2a import run_provisional_docking_v12 as docking
from track3_a2a.run_provisional_docking_v12 import aggregate_runs, select_ligands


class A2AProvisionalDockingTests(unittest.TestCase):
    def test_selection_uses_only_primary_protomers(self):
        rows = [
            {"chembl_id": "B", "primary_protomer": False},
            {"chembl_id": "A", "primary_protomer": True},
            {"chembl_id": "B", "primary_protomer": True},
        ]
        selected = select_ligands(rows, 2)
        self.assertEqual(len(selected), 2)
        self.assertTrue(all(row["primary_protomer"] for row in selected))

    def test_median_aggregation_requires_two_valid_seeds(self):
        runs = [
            {"status": "valid", "minimized_affinity_kcal_mol": -8.0, "cnn_score": 0.8, "cnnscore_flag": False},
            {"status": "valid", "minimized_affinity_kcal_mol": -7.0, "cnn_score": 0.7, "cnnscore_flag": False},
            {"status": "failed"},
        ]
        result = aggregate_runs(runs, 2)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["median_affinity_kcal_mol"], -7.5)

    def test_zero_valid_runs_fail(self):
        self.assertEqual(aggregate_runs([{"status": "failed"}], 2)["status"], "failed")

    def test_timeout_is_quarantined_and_cached(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            root = project_root / "track3_a2a"
            output_root = root / "outputs" / "v1.2" / "docking-full"
            receptor = root / "receptors" / "test.pdb"
            ligand = {"chembl_id": "CHEMBL_TEST", "path": "ligands/test.sdf"}
            config = {
                "gnina": {"exhaustiveness": 8, "cnn_scoring": "rescore", "num_modes": 1},
                "pose_quality": {"cnnscore_flag_threshold": 0.5},
            }
            box = {"center": [0, 0, 0], "size": [20, 20, 20]}
            with (
                mock.patch.object(docking, "ROOT", root),
                mock.patch.object(docking, "PROJECT_ROOT", project_root),
                mock.patch.object(docking, "GNINA", project_root / "scripts" / "gnina-docker"),
                mock.patch.object(
                    docking.subprocess,
                    "run",
                    side_effect=[
                        subprocess.TimeoutExpired("gnina", 1),
                        subprocess.CompletedProcess(["docker", "stop"], 0),
                    ],
                ) as run_mock,
            ):
                first = docking.run_seed(
                    ligand, "inactive", receptor, box, config, output_root, 42, 1
                )
                self.assertEqual(first["status"], "timed_out")
                marker = output_root / "CHEMBL_TEST" / "inactive" / "seed-42.timeout.json"
                self.assertTrue(marker.exists())

                second = docking.run_seed(
                    ligand, "inactive", receptor, box, config, output_root, 42, 1
                )
                self.assertEqual(second["status"], "timed_out")
                self.assertTrue(second["cached"])
                self.assertEqual(run_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
