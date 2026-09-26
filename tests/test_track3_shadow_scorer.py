import csv
import json
import math
import unittest
from pathlib import Path
from unittest import mock

import track3_ab_ridge_shadow as shadow
import track3_discovery_workflow as workflow


class ShadowRidgeTests(unittest.TestCase):
    def test_artifact_declares_development_only_and_source_hashes(self):
        artifact = json.loads(shadow.ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(artifact["training_n"], 78)
        self.assertEqual(artifact["training_distinct_molecules"], 69)
        self.assertEqual(artifact["training_partition"], "development_only")
        self.assertFalse(artifact["external_outcomes_loaded"])
        self.assertFalse(artifact["promotion_allowed"])
        self.assertEqual(len(artifact["weights"]), 2056)
        for name, path in shadow.SOURCES.items():
            self.assertEqual(artifact["source_sha256"][name], shadow.sha256(path))

    def test_source_drift_disables_capability(self):
        shadow.load_scorer.cache_clear()
        with mock.patch.dict(shadow.SOURCES, {"summary": Path("/nonexistent/shadow-summary.csv")}):
            self.assertEqual(shadow.capability(), "unavailable")
        shadow.load_scorer.cache_clear()

    def test_rdkit_shadow_prediction_is_non_admitting(self):
        if shadow.capability() != "development_only":
            self.skipTest("RDKit is not installed in this test interpreter")
        result = shadow.score_smiles("Cn1c(=O)c2c(ncn2C)n(C)c1=O")
        self.assertTrue(math.isfinite(result["pbind_ki"]))
        self.assertEqual(len(result["artifact_sha256"]), 64)
        run = workflow.run_workflow(
            "human A2A ligand evidence",
            molecules=[{"name": "Caffeine", "smiles": "Cn1c(=O)c2c(ncn2C)n(C)c1=O"}],
            provider_mode="demo", persist=False,
        )
        record = run["molecules"][0]
        self.assertAlmostEqual(record["provisional_score"], result["pbind_ki"], places=10)
        self.assertEqual(record["model_provenance_status"], "development_only_not_externally_validated")
        self.assertIsNone(record["interval_90"])
        self.assertFalse(record["screen_eligible"])
        self.assertEqual(run["screen_eligible_queue"]["count"], 0)

    def test_export_matches_frozen_sklearn_pipeline(self):
        if shadow.capability() != "development_only":
            self.skipTest("RDKit is not installed in this test interpreter")
        import numpy as np
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from track3_a2a.run_continuous_activity_v15 import DESCRIPTORS, fingerprint_data, numeric_matrix

        with shadow.SOURCES["features"].open(newline="", encoding="utf-8") as stream:
            features = {row["molecule_id"]: row for row in csv.DictReader(stream)}
        with shadow.SOURCES["summary"].open(newline="", encoding="utf-8") as stream:
            rows = [{**features[row["molecule_id"]], **row} for row in csv.DictReader(stream)
                    if row["endpoint_name"] == "pBind_Ki"
                    and row["review_status"] == "admitted_exploratory"
                    and row["development_partition"] == "development"]
        fingerprints, _ = fingerprint_data(rows)
        matrix = np.hstack([fingerprints, SimpleImputer(strategy="median").fit_transform(numeric_matrix(rows, DESCRIPTORS))])
        y = np.asarray([float(row["aggregated_pactivity"]) for row in rows])
        pipeline = Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]).fit(matrix, y)
        sample = rows[0]
        expected = float(pipeline.predict(matrix[:1])[0])
        actual = shadow.score_smiles(sample["standardized_smiles"])["pbind_ki"]
        self.assertAlmostEqual(actual, expected, places=6)


if __name__ == "__main__":
    unittest.main()
