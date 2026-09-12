import csv
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"
MANIFEST = A2A / "data" / "curated" / "chembl251_inverse_agonist_exclusions_v1.3.csv"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class A2AInverseAgonistManifestV13Tests(unittest.TestCase):
    def test_manifest_exactly_reconciles_214_to_203(self):
        historical = read_csv(A2A / "outputs" / "v1.2" / "docking_clean.csv")
        corrected = read_csv(A2A / "outputs" / "v1.3" / "docking_clean_computational.csv")
        manifest = read_csv(MANIFEST)

        historical_ids = {row["molecule_id"] for row in historical}
        corrected_ids = {row["molecule_id"] for row in corrected}
        removed_ids = {row["chembl_id"] for row in manifest}

        self.assertEqual(len(historical), 214)
        self.assertEqual(len(corrected), 203)
        self.assertEqual(len(manifest), 11)
        self.assertEqual(historical_ids - corrected_ids, removed_ids)
        self.assertEqual(historical_ids - removed_ids, corrected_ids)
        self.assertFalse(corrected_ids & removed_ids)

    def test_manifest_matches_the_versioned_curation_audit(self):
        manifest = {row["chembl_id"]: row for row in read_csv(MANIFEST)}
        audit = json.loads(
            (A2A / "data" / "curated" / "chembl251_computational_audit_v1.3.json").read_text(
                encoding="utf-8"
            )
        )
        audited = {
            row["chembl_id"]: row
            for row in audit["records"]
            if "inverse_agonist" in row.get("excluded_functional_classes", [])
        }
        self.assertEqual(set(manifest), set(audited))
        for chembl_id, row in manifest.items():
            manifest_activity_ids = {int(value) for value in row["activity_ids"].split("|")}
            audited_activity_ids = {
                int(item["activity_id"])
                for item in audited[chembl_id]["excluded_function_evidence"]
            }
            self.assertEqual(manifest_activity_ids, audited_activity_ids)
            self.assertEqual(int(row["total_inverse_flag_rows"]), len(audited_activity_ids))

    def test_evidence_strength_and_partition_counts_are_explicit(self):
        rows = read_csv(MANIFEST)
        self.assertEqual(
            Counter(row["evidence_status"] for row in rows),
            {
                "primary_functional_inverse_agonist_evidence": 7,
                "binding_only_inverse_annotation_requires_review": 4,
            },
        )
        self.assertEqual(
            Counter(row["former_partition"] for row in rows),
            {"provisional_development": 8, "provisional_locked_holdout": 3},
        )
        self.assertTrue(all(row["former_binary_label"] == "antagonist" for row in rows))
        for row in rows:
            primary_rows = int(row["primary_functional_rows"])
            if row["evidence_status"] == "primary_functional_inverse_agonist_evidence":
                self.assertGreater(primary_rows, 0)
            else:
                self.assertEqual(primary_rows, 0)
                self.assertEqual(int(row["binding_annotation_rows"]), 1)

    def test_public_reconciliation_audit_matches_manifest(self):
        rows = read_csv(MANIFEST)
        audit = json.loads(
            (A2A / "outputs" / "v1.3" / "inverse_agonist_exclusion_audit_v1.3.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(audit["set_reconciliation_passed"])
        self.assertEqual(audit["removed_record_count"], len(rows))
        self.assertEqual(set(audit["removed_ids"]), {row["chembl_id"] for row in rows})
        sources = {
            "inverse_agonist_manifest": MANIFEST,
            "historical_214_matrix": A2A / "outputs" / "v1.2" / "docking_clean.csv",
            "corrected_203_matrix": A2A / "outputs" / "v1.3" / "docking_clean_computational.csv",
            "computational_curation_audit": A2A
            / "data"
            / "curated"
            / "chembl251_computational_audit_v1.3.json",
        }
        for name, path in sources.items():
            self.assertEqual(audit["source_hashes"][name], sha256(path))


if __name__ == "__main__":
    unittest.main()
