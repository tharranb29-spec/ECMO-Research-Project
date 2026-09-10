import unittest

from track3_a2a.build_feature_matrix_v12 import build_feature_row, hard_filter_sensitivity


def receptor(affinity, cnnscore, cnnaffinity, flags=0):
    scores = [cnnscore, cnnscore, cnnscore]
    for index in range(flags):
        scores[index] = 0.3
    return {
        "status": "valid",
        "valid_seed_count": 3,
        "failed_seed_count": 0,
        "median_affinity_kcal_mol": affinity,
        "affinity_sd": 0.2,
        "median_cnn_score": sorted(scores)[1],
        "cnnscore_flagged_seed_count": flags,
        "runs": [
            {"status": "valid", "cnn_score": score, "cnn_affinity_pk": cnnaffinity + index / 10}
            for index, score in enumerate(scores)
        ],
    }


class A2AFeatureMatrixV12Tests(unittest.TestCase):
    def setUp(self):
        self.molecule = {
            "chembl_id": "CHEMBL_TEST",
            "receptors": {
                "inactive_5NM4": receptor(-8.0, 0.8, 7.0, flags=1),
                "active_like_2YDO": receptor(-9.0, 0.7, 7.4),
            },
        }
        self.partition = {
            "molecule_name": "Test",
            "functional_class": "agonist",
            "primary_binary_label": 1,
            "partition": "provisional_development",
            "standardized_smiles": "CCO",
            "standardized_inchikey": "TEST",
            "generic_murcko_scaffold_smiles": "ACYCLIC",
        }
        self.evidence = {"recommended_evidence_tier": "tier_1"}
        self.chemistry = {
            "murcko_scaffold_smiles": "",
            "descriptors": {
                "molecular_weight": 46.1,
                "clogp": -0.1,
                "h_bond_donors": 1,
                "h_bond_acceptors": 1,
                "rotatable_bonds": 0,
                "tpsa": 20.2,
                "heavy_atom_count": 3,
                "qed": 0.4,
            },
        }
        self.config = {
            "pose_quality": {"cnnscore_flag_threshold": 0.3},
            "label_status": "provisional_ai_assisted_human_review_required",
        }

    def test_orthogonal_features_use_active_minus_inactive(self):
        row = build_feature_row(
            self.molecule, self.partition, self.evidence, self.chemistry, self.config
        )
        self.assertEqual(row["m_affinity_kcal_mol"], -8.5)
        self.assertEqual(row["d_affinity_kcal_mol"], -1.0)
        self.assertEqual(row["d_affinity_per_heavy_atom"], -0.333333)

    def test_cnn_threshold_is_inclusive_soft_flag(self):
        row = build_feature_row(
            self.molecule, self.partition, self.evidence, self.chemistry, self.config
        )
        self.assertEqual(row["inactive_5NM4_cnnscore_flagged_seeds"], 1)
        self.assertTrue(row["cnnscore_soft_flag_any"])
        self.assertEqual(row["pose_quality_status"], "retain_with_soft_flag")

    def test_hard_filter_diagnostic_does_not_remove_primary_rows(self):
        row = build_feature_row(
            self.molecule, self.partition, self.evidence, self.chemistry, self.config
        )
        summary = hard_filter_sensitivity([row])
        self.assertEqual(summary["agonist"]["unfiltered"], 1)
        self.assertEqual(summary["agonist"]["all_six_seeds_pass"], 0)
        self.assertEqual(summary["agonist"]["at_least_two_passing_seeds_per_receptor"], 1)


if __name__ == "__main__":
    unittest.main()
