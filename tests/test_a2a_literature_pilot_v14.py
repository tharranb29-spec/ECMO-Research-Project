import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "track3_a2a" / "data" / "raw" / "external" / "literature_pilot_2025"
OUTPUT = ROOT / "track3_a2a" / "outputs" / "v1.4"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class A2ALiteraturePilotV14Tests(unittest.TestCase):
    def test_registry_and_candidate_snapshot_are_label_free(self):
        registry = json.loads((RAW / "source_registry.json").read_text(encoding="utf-8"))
        self.assertFalse(registry["functional_labels_in_registry"])
        self.assertFalse(registry["activity_values_in_registry"])
        with (RAW / "external_candidates_literature_pilot_2025.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        self.assertEqual(len(rows), 6)
        prohibited = {"functional_class", "primary_binary_label", "label", "assay_readout"}
        self.assertTrue(prohibited.isdisjoint(reader.fieldnames or []))

    def test_screening_counts_and_public_hashes_reconcile(self):
        cohort = OUTPUT / "external_cohort" / "literature_pilot_2025"
        evidence = OUTPUT / "evidence_review" / "literature_pilot_2025"
        audit = json.loads((cohort / "screening_audit.json").read_text(encoding="utf-8"))
        status = json.loads((evidence / "source_screening_status.json").read_text(encoding="utf-8"))
        self.assertEqual((audit["input_count"], audit["eligible_count"], audit["quarantined_count"]), (6, 4, 2))
        self.assertEqual(status["evidence_admitted_count"], 0)
        self.assertFalse(status["labels_written_to_repository"])
        paths = {
            "source_registry": RAW / "source_registry.json",
            "candidate_snapshot": RAW / "external_candidates_literature_pilot_2025.csv",
            "eligible_candidates": cohort / "eligible_candidates.csv",
            "quarantined_candidates": cohort / "quarantined_candidates.csv",
        }
        for key, path in paths.items():
            self.assertEqual(status["source_hashes"][key], sha256(path))

        self.assertEqual(status["deferred_unresolved_stereoisomer_count"], 2)

    def test_compound_5_is_structurally_eligible_but_remains_label_free(self):
        cohort = OUTPUT / "external_cohort" / "literature_pilot_2025"
        with (cohort / "eligible_candidates.csv").open(newline="", encoding="utf-8") as handle:
            rows = {row["record_id"]: row for row in csv.DictReader(handle)}
        self.assertIn("LIT25-RL-C5", rows)
        self.assertEqual(rows["LIT25-RL-C5"]["standardized_inchikey"], "NMTSCZDEWYHEMT-UHFFFAOYSA-N")
        self.assertNotIn("functional_class", rows["LIT25-RL-C5"])

    def test_only_declared_scaffold_overlaps_are_quarantined(self):
        cohort = OUTPUT / "external_cohort" / "literature_pilot_2025"
        with (cohort / "quarantined_candidates.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["record_id"] for row in rows}, {"LIT25-MET-SAH", "LIT25-MET-DA"})
        self.assertTrue(all(row["screening_reasons"] == "historical_generic_murcko_scaffold_overlap" for row in rows))


if __name__ == "__main__":
    unittest.main()
