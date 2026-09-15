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


if __name__ == "__main__":
    unittest.main()
