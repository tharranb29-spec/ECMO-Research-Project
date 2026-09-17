import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"
sys.path.insert(0, str(A2A))


def import_script(name):
    path = A2A / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestA2AMDProductionReadinessV16(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readiness = import_script("md_readiness_v16")
        cls.tier_a_runner = import_script("run_tier_a_production_v16")
        cls.tier_b = import_script("preflight_tier_b_build_v16")
        cls.production = json.loads((A2A / "config" / "md_production.v1.6.json").read_text())

    def test_tier_a_contract_is_the_frozen_50_ns_three_replica_pilot(self):
        tier_a = self.production["tier_a"]
        self.assertEqual(tier_a["pilot_ns_per_replica"], 50.0)
        self.assertEqual(tier_a["replica_seeds"], [20260914, 20260915, 20260916])
        self.assertEqual(len(tier_a["systems"]), 2)
        self.assertTrue(tier_a["all_replicas_must_be_reported"])
        self.assertEqual(tier_a["best_replica_selection"], "prohibited")
        self.assertEqual(tier_a["start_gate"]["required_equilibration_pass_count"], 6)

    def test_incomplete_equilibration_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "equilibration_gate_report.json").write_text(json.dumps({
                "specification_id": "a2a-tier-a-equilibration-gate-v1.6.4",
                "status": "tier_a_equilibration_gate_locked",
                "expected_run_count": 6,
                "observed_run_count": 5,
                "passed_run_count": 5,
                "missing_audits": ["missing/equilibration_audit.json"],
            }))
            with self.assertRaisesRegex(self.readiness.GateError, "locked|six"):
                self.readiness.verify_equilibration_gate(equilibration_root=root, require_states=False)

    def test_exact_six_run_equilibration_gate_can_pass(self):
        equil_config_hash = self.readiness.sha256(self.readiness.EQUILIBRATION_CONFIG)
        runs = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for system_id in self.readiness.tier_a_systems(self.production):
                release = self.readiness.verify_release_bundle(system_id)
                for seed in self.production["tier_a"]["replica_seeds"]:
                    run = root / system_id / f"seed-{seed}"
                    run.mkdir(parents=True)
                    state = run / "equilibrated_state.xml"
                    state.write_text(f"verified-state:{system_id}:{seed}\n")
                    audit = {
                        "specification_id": "a2a-tier-a-equilibration-v1.6.4",
                        "system_id": system_id,
                        "seed": seed,
                        "status": "equilibration_gate_passed",
                        "scale": 1.0,
                        "config_sha256": equil_config_hash,
                        "source_system_sha256": release["members_sha256"]["system.xml"],
                        "source_smoke_state_sha256": release["members_sha256"]["smoke_final_state.xml"],
                        "files": {"equilibrated_state.xml": self.readiness.sha256(state)},
                    }
                    audit_path = run / "equilibration_audit.json"
                    audit_path.write_text(json.dumps(audit))
                    relative = audit_path.relative_to(root)
                    runs.append({
                        "system_id": system_id,
                        "seed": seed,
                        "path": str(relative),
                        "sha256": self.readiness.sha256(audit_path),
                        "status": "equilibration_gate_passed",
                        "config_sha256": equil_config_hash,
                    })
            gate = {
                "specification_id": "a2a-tier-a-equilibration-gate-v1.6.4",
                "status": "tier_a_equilibration_gate_passed",
                "tier_a_production_unlocked": True,
                "tier_b_unlocked": False,
                "expected_run_count": 6,
                "observed_run_count": 6,
                "passed_run_count": 6,
                "missing_audits": [],
                "config_sha256": equil_config_hash,
                "runs": runs,
            }
            (root / "equilibration_gate_report.json").write_text(json.dumps(gate))
            result = self.readiness.verify_equilibration_gate(equilibration_root=root)
            self.assertEqual(result["status"], "tier_a_production_preflight_passed")
            self.assertEqual(len(result["verified_runs"]), 6)
            args = type("Args", (), {
                "system": "5NM4_ZMA_native",
                "replica": 1,
                "equilibration_root": root,
                "release_root": self.readiness.DEFAULT_RELEASE_ROOT,
            })()
            preflight = self.tier_a_runner.preflight(args)
            self.assertEqual(preflight["status"], "tier_a_replica_preflight_passed")
            self.assertFalse(preflight["trajectory_started"])

    def test_repository_aggregate_gate_accepts_all_six_audits(self):
        result = self.readiness.verify_equilibration_gate(require_states=False)
        self.assertEqual(result["status"], "tier_a_production_preflight_passed")
        self.assertEqual(len(result["verified_runs"]), 6)

    def test_both_controls_need_two_of_three_and_all_replicas_reported(self):
        systems = []
        for system_id in self.readiness.tier_a_systems(self.production):
            systems.append({
                "system_id": system_id,
                "passed_replica_count": 2,
                "passed": True,
                "replicas": [
                    {"replica": 1, "passed": True},
                    {"replica": 2, "passed": True},
                    {"replica": 3, "passed": False},
                ],
            })
        gate = {
            "specification_id": self.production["specification_id"],
            "status": "both_tier_a_controls_passed",
            "tier_b_unlocked": True,
            "candidate_labels_loaded": False,
            "systems": systems,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gate.json"
            path.write_text(json.dumps(gate))
            self.assertEqual(self.readiness.verify_tier_a_control_gate(path)["status"], "both_tier_a_controls_passed")
            gate["systems"][0]["replicas"] = gate["systems"][0]["replicas"][:2]
            path.write_text(json.dumps(gate))
            with self.assertRaisesRegex(self.readiness.GateError, "all three replicas"):
                self.readiness.verify_tier_a_control_gate(path)

    def test_tier_b_preflight_is_label_blind_and_creates_nothing(self):
        report = self.tier_b.build_preflight()
        self.assertFalse(report["candidate_labels_loaded"])
        self.assertEqual(report["system_count"], 8)
        self.assertTrue(report["tier_a_equilibration_gate_passed"])
        self.assertEqual(report["bundles_created"], 0)
        self.assertEqual(report["trajectories_started"], 0)
        self.assertFalse(report["tier_b_bundle_construction_authorized"])
        self.assertFalse(report["tier_b_trajectory_unlocked"])
        self.assertTrue(all(row["functional_label_blinded"] for row in report["systems"]))
        self.assertTrue(all(row["bundle_created"] is False for row in report["systems"]))
        self.assertTrue(all(row["trajectory_started"] is False for row in report["systems"]))
        active_like = [row for row in report["systems"] if row["receptor_id"] == "2YDO"]
        self.assertEqual(len(active_like), 4)
        self.assertTrue(all("accepted_receptor_construct_missing" in row["blockers"] for row in active_like))

    def test_release_archives_and_embedded_manifests_verify(self):
        for system_id in self.readiness.tier_a_systems(self.production):
            manifest = self.readiness.verify_release_bundle(system_id)
            self.assertEqual(manifest["system_id"], system_id)
            with tempfile.TemporaryDirectory() as directory:
                materialized = self.readiness.materialize_release_bundle(system_id, Path(directory))
                self.assertTrue((materialized / "system.xml").is_file())
                self.assertTrue((materialized / "smoke_final_state.xml").is_file())

    def test_tier_b_runner_requires_a_passed_control_gate_before_bundle(self):
        runner = import_script("run_tier_b_production_v16")
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-control-gate.json"
            args = type("Args", (), {
                "system": "LIT25-RL-C5_5NM4",
                "replica": 1,
                "control_gate": missing,
                "bundles_root": Path(directory) / "bundles",
            })()
            with self.assertRaisesRegex(RuntimeError, "control-gate report is missing"):
                runner.preflight(args)


if __name__ == "__main__":
    unittest.main()
