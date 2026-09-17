import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "track3_a2a"


class A2AExecutionV16Tests(unittest.TestCase):
    def load(self, relative):
        return json.loads((ROOT / relative).read_text())

    def test_external_pass1_preserves_outcome_firewall(self):
        audit = self.load("outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json")
        self.assertEqual(audit["candidate_count"], 240)
        self.assertEqual(audit["external_cohort_admitted_count"], 0)
        self.assertFalse(audit["outcome_fields_loaded"])
        self.assertGreaterEqual(audit["pass_2_required_count"], 60)

    def test_external_pass2_freezes_floor_failure_without_outcome_join(self):
        audit = self.load("outputs/v1.6/external_evidence/pass2_source_extraction/pass2_source_extraction_audit.json")
        freeze = self.load("outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json")
        self.assertEqual(audit["candidate_count"], 240)
        self.assertEqual(audit["pass_1_eligible_source_grounded_candidate_count"], 24)
        self.assertEqual(audit["admitted_count"], 0)
        self.assertTrue(audit["membership_frozen"])
        self.assertFalse(audit["numeric_ki_extracted"])
        self.assertFalse(audit["outcome_fields_loaded"])
        self.assertFalse(freeze["minimum_floors_passed"])
        self.assertFalse(freeze["external_outcomes_joined"])
        self.assertFalse(freeze["one_time_outcome_join_authorized"])
        self.assertGreaterEqual(freeze["minimum_molecule_floor"], 60)
        self.assertGreaterEqual(freeze["minimum_generic_murcko_scaffold_floor"], 20)

    def test_implementation_status_records_dashboard_as_shadow_only(self):
        status = self.load("outputs/v1.6/implementation_status.json")
        dashboard = status["workstreams"]["D_dashboard"]
        self.assertEqual(dashboard["status"], "static_v1_contract_dashboard_implemented")
        self.assertEqual(dashboard["contract_version"], "1.0.0")
        self.assertEqual(dashboard["autonomous_mode"], "shadow_only")
        self.assertIsNone(dashboard["served_track3_model"])

    def test_native_control_pose_mappings_pass(self):
        audit = self.load("outputs/v1.6/md/native_control_ligands/native_pose_mapping_audit.json")
        self.assertEqual(audit["accepted_count"], 2)
        self.assertEqual(audit["status"], "all_native_pose_mappings_accepted")
        for system in audit["systems"]:
            self.assertEqual(system["post_transfer_native_heavy_rmsd_angstrom"], 0.0)
            self.assertGreaterEqual(system["minimum_ligand_protein_heavy_distance_angstrom"], 1.0)

    def test_lipid21_patch_passes_composition_and_geometry(self):
        audit = self.load("outputs/v1.6/md/membrane_patch/patch_audit.json")
        self.assertEqual(audit["status"], "mixed_membrane_patch_computationally_accepted")
        self.assertLessEqual(abs(audit["cholesterol_mole_fraction"] - 0.30), 0.01)
        self.assertEqual(audit["cross_residue_nonwater_heavy_clash_count_below_1_angstrom"], 0)
        self.assertTrue(audit["all_lipid21_templates_resolved"])

    def test_minimized_constructs_pass_before_periodic_assembly(self):
        audit = self.load("outputs/v1.6/md/tier_a_constructs/minimized/minimization_audit.json")
        self.assertEqual(audit["passed_count"], 2)
        self.assertFalse(audit["trajectory_production_started"])
        for system in audit["systems"]:
            self.assertTrue(system["energy_decreased"])
            self.assertTrue(system["geometry_reaudit"]["geometry_gate_passed"])

    def test_unsolvated_tier_a_complexes_pass_parameter_preflight(self):
        audit = self.load("outputs/v1.6/md/tier_a_complex_preflight/complex_preflight_audit.json")
        self.assertEqual(audit["accepted_count"], 2)
        self.assertEqual(audit["status"], "all_unsolvated_complex_preflights_accepted")
        for system in audit["systems"]:
            self.assertTrue(system["finite_initial_energy"])
            self.assertFalse(system["tleap_severe_tokens"])
            self.assertTrue(system["geometry"]["passed"])

    def test_relaxed_membrane_patch_is_finite_and_clash_free(self):
        audit = self.load("outputs/v1.6/md/membrane_patch/patch_relaxation_audit.json")
        self.assertEqual(audit["status"], "relaxed_membrane_patch_accepted")
        self.assertTrue(audit["energy_decreased"])
        self.assertEqual(audit["cross_residue_nonwater_all_atom_pair_count_below_1_angstrom"], 0)
        self.assertEqual(audit["cross_residue_nonwater_heavy_pair_count_below_1_angstrom"], 0)

    def test_periodic_tier_a_assemblies_pass_without_starting_trajectories(self):
        audit = self.load("outputs/v1.6/md/tier_a_periodic_systems/periodic_assembly_audit.json")
        self.assertEqual(audit["status"], "all_periodic_assembly_gates_passed")
        self.assertEqual(audit["passed_count"], 2)
        self.assertFalse(audit["trajectory_production_started"])
        for system in audit["systems"]:
            self.assertTrue(system["finite_initial_energy"])
            self.assertEqual(system["severe_nonwater_heavy_clash_count_below_1_angstrom"], 0)
            self.assertGreaterEqual(system["native_contact_count"], 70)
            self.assertTrue(system["coordinate_export_ids_normalized"])

    def test_tier_a_smoke_and_release_gates_pass_but_production_stays_locked(self):
        smoke = self.load("outputs/v1.6/md/tier_a_smoke_tests/smoke_campaign_audit.json")
        release = self.load("outputs/v1.6/md/tier_a_release_bundles/campaign_manifest.json")
        self.assertEqual(smoke["status"], "all_tier_a_smoke_gates_passed")
        self.assertEqual(smoke["passed_count"], 2)
        self.assertFalse(smoke["trajectory_production_started"])
        self.assertEqual(release["status"], "all_tier_a_release_bundles_accepted")
        self.assertEqual(release["accepted_count"], 2)
        for bundle in release["systems"]:
            self.assertFalse(bundle["production_trajectory_started"])
            self.assertEqual(bundle["status"], "accepted_for_staged_equilibration")
            archive = ROOT / bundle["archive"]["path"]
            self.assertTrue(archive.is_file())
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), bundle["archive"]["sha256"])

    def test_equilibration_protocol_preserves_all_replicas_and_locks_tier_b(self):
        config = self.load("config/tier_a_equilibration.v1.6.4.json")
        self.assertEqual(config["supersedes"], "a2a-tier-a-equilibration-v1.6.3")
        self.assertEqual(config["minimization"]["restraint_distance"], "periodicdistance")
        runner = (ROOT / "run_tier_a_equilibration_v16.py").read_text()
        self.assertIn("periodicdistance(x,y,z,x0,y0,z0)^2", runner)
        self.assertNotIn("(x-x0)^2+(y-y0)^2+(z-z0)^2", runner)
        self.assertEqual(len(config["systems"]), 2)
        self.assertEqual(config["replica_seeds"], [20260914, 20260915, 20260916])
        self.assertEqual(config["best_replica_selection"], "prohibited")
        self.assertTrue(config["production_remains_locked_until_gate_report_passes"])
        self.assertTrue(config["tier_b_remains_locked_until_tier_a_production_passes"])
        self.assertAlmostEqual(sum(stage["duration_ps"] for stage in config["stages"]), 2140.0)
        self.assertLessEqual(max(stage["timestep_femtoseconds"] for stage in config["stages"]), 1.0)
        gate = self.load("outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json")
        self.assertEqual(gate["status"], "tier_a_equilibration_gate_passed")
        self.assertEqual(gate["passed_run_count"], 6)
        self.assertTrue(gate["tier_a_production_unlocked"])
        self.assertFalse(gate["tier_b_unlocked"])


if __name__ == "__main__":
    unittest.main()
