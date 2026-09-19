import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"
FIXTURE = ROOT / "tests" / "fixtures" / "tier_a_production" / "run_status_5NM4_replica1_5.92ns.json"
OUTPUT = A2A / "outputs" / "v1.6" / "md" / "tier_a_production_cutoff" / "cutoff_status.json"
MARKDOWN = A2A / "outputs" / "v1.6" / "md" / "tier_a_production_cutoff" / "CUTOFF_STATUS.md"
SCHEMA = A2A / "dashboard_contracts" / "v1" / "md-production-cutoff.schema.json"
sys.path.insert(0, str(A2A))


def import_script(name):
    path = A2A / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestA2AMDCutoffStatusV16(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = import_script("ingest_tier_a_production_status_v16")

    def write_payload(self, directory, payload, name="run_status.json"):
        path = Path(directory) / name
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def fixture_payload(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_live_example_validates_all_provenance_and_checkpoint_semantics(self):
        row = self.module.validate_run_status(FIXTURE)
        self.assertEqual(row["system_id"], "5NM4_ZMA_native")
        self.assertEqual((row["replica"], row["seed"]), (1, 20260914))
        self.assertEqual(row["reported_completed_ns"], 5.92)
        self.assertEqual(row["last_scheduled_checkpoint_ns"], 5.9)
        self.assertFalse(row["checkpoint_file_observed"])
        self.assertEqual(row["source_sha256"], "9ae68e14b58645a619c18f5693b79be98ab45a45f4bbe8130112ffdbc2927c51")
        self.assertEqual(row["platform"], "CUDA")
        self.assertFalse(row["tier_b_unlocked"])

    def test_cutoff_totals_are_exact_and_separate_from_model_training(self):
        report = self.module.build_cutoff([FIXTURE], [])
        production = report["tier_a_production"]
        self.assertEqual(report["equilibration"]["passed_runs"], 6)
        self.assertEqual(report["equilibration"]["required_runs"], 6)
        self.assertEqual(production["status"], "started_campaign_incomplete")
        self.assertEqual(production["completed_replicas"], 0)
        self.assertEqual(production["required_replicas"], 6)
        self.assertEqual(production["running_replicas"], 1)
        self.assertEqual(production["aggregate_reported_ns"], 5.92)
        self.assertEqual(production["required_ns"], 300.0)
        self.assertEqual(report["tier_b"], {
            "status": "not_executed_locked", "executed_replicas": 0, "tier_b_unlocked": False,
        })
        interpretation = report["model_training_interpretation"]
        self.assertEqual(interpretation["status"], "not_assessed_by_md_cutoff")
        self.assertTrue(interpretation["md_campaign_incomplete_does_not_imply_model_training_incomplete"])

    def test_provenance_platform_identity_and_lock_tampering_are_rejected(self):
        mutations = [
            ("production_config_sha256", "0" * 64),
            ("seed", 20260915),
            ("platform", "CPU"),
            ("tier_b_unlocked", True),
            ("current_step", 5920001),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for index, (field, value) in enumerate(mutations):
                payload = self.fixture_payload()
                payload[field] = value
                path = self.write_payload(directory, payload, f"tampered-{index}.json")
                with self.subTest(field=field), self.assertRaises(self.module.SnapshotError):
                    self.module.validate_run_status(path)

    def test_progress_must_be_monotonic(self):
        with tempfile.TemporaryDirectory() as directory:
            later = self.fixture_payload()
            later["current_step"] = 6000000
            later["completed_ns"] = 6.0
            later["updated_at_utc"] = "2026-09-17T14:30:00+00:00"
            later_path = self.write_payload(directory, later, "later.json")
            report = self.module.build_cutoff([FIXTURE, later_path], [])
            self.assertEqual(report["tier_a_production"]["aggregate_reported_ns"], 6.0)

            regressed = self.fixture_payload()
            regressed["current_step"] = 5000000
            regressed["completed_ns"] = 5.0
            regressed["updated_at_utc"] = "2026-09-17T14:40:00+00:00"
            regressed_path = self.write_payload(directory, regressed, "regressed.json")
            with self.assertRaisesRegex(self.module.SnapshotError, "regressed"):
                self.module.build_cutoff([FIXTURE, regressed_path], [])

    def test_complete_and_failure_artifact_semantics_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            complete = self.fixture_payload()
            complete.update({
                "status": "complete", "current_step": 50000000, "completed_ns": 50.0,
                "updated_at_utc": "2026-09-18T00:00:00+00:00",
                "files": {
                    "trajectory.dcd": "a" * 64, "state.csv": "b" * 64,
                    "final_state.xml": "c" * 64, "restart.chk": "d" * 64,
                },
            })
            complete_path = self.write_payload(directory, complete, "complete.json")
            report = self.module.build_cutoff([complete_path], [])
            self.assertEqual(report["tier_a_production"]["completed_replicas"], 1)
            self.assertEqual(report["tier_a_production"]["aggregate_completed_replica_ns"], 50.0)

            failure = self.fixture_payload()
            failure.update({
                "status": "technical_failure", "updated_at_utc": "2026-09-17T15:00:00+00:00",
                "current_step": 5920001,
                "error_type": "RuntimeError", "error": "synthetic test failure",
                "failed_replica_may_not_be_omitted": True,
            })
            failure.pop("completed_ns")
            failure_path = self.write_payload(directory, failure, "failure_audit.json")
            failed_report = self.module.build_cutoff([], [failure_path])
            self.assertEqual(failed_report["tier_a_production"]["failed_replicas"], 1)
            with self.assertRaisesRegex(self.module.SnapshotError, "terminal"):
                self.module.build_cutoff([complete_path], [failure_path])

    def test_previous_report_is_revalidated_before_monotonic_update(self):
        with tempfile.TemporaryDirectory() as directory:
            previous_path = Path(directory) / "previous.json"
            previous = self.module.build_cutoff([FIXTURE], [])
            previous_path.write_text(json.dumps(previous), encoding="utf-8")
            later = self.fixture_payload()
            later.update({
                "current_step": 6000000, "completed_ns": 6.0,
                "updated_at_utc": "2026-09-17T14:30:00+00:00",
            })
            later_path = self.write_payload(directory, later, "later.json")
            updated = self.module.build_cutoff([later_path], [], previous_path)
            self.assertEqual(updated["tier_a_production"]["aggregate_reported_ns"], 6.0)
            previous["snapshots"][0]["production_config_sha256"] = "0" * 64
            previous_path.write_text(json.dumps(previous), encoding="utf-8")
            with self.assertRaisesRegex(self.module.SnapshotError, "production_config_sha256"):
                self.module.build_cutoff([later_path], [], previous_path)

    def test_committed_machine_and_human_reports_match_fixture(self):
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expected = self.module.build_cutoff([FIXTURE], [])
        self.assertEqual(report, expected)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        contract = report["dashboard_contract"]
        self.assertEqual(contract["schema_id"], schema["properties"]["schema_id"]["const"])
        record = contract["records"][0]
        self.assertTrue(set(schema["properties"]["records"]["items"]["required"]).issubset(record))
        self.assertEqual(record["tier_b_status"], "not_executed_locked")
        self.assertFalse(record["tier_b_unlocked"])
        markdown = MARKDOWN.read_text(encoding="utf-8")
        self.assertIn("Completed production replicas: 0/6", markdown)
        self.assertIn("Aggregate reported production: 5.92/300.00 ns", markdown)
        self.assertIn("Tier B:** not executed; locked", markdown)
        self.assertIn("does not assess model-training status", markdown)


if __name__ == "__main__":
    unittest.main()
