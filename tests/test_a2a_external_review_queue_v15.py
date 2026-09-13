import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "track3_a2a" / "outputs" / "v1.5" / "external_pbind_intake"


class TestA2AExternalReviewQueueV15(unittest.TestCase):
    def test_queue_is_label_blind_and_not_frozen_membership(self):
        audit = json.loads((INTAKE / "primary_evidence_review_queue_audit.json").read_text())
        self.assertFalse(audit["outcomes_loaded"])
        self.assertFalse(audit["membership_frozen"])
        self.assertEqual(audit["queue_candidate_count"], 240)
        self.assertEqual(audit["queue_generic_scaffold_count"], 240)

    def test_queue_contains_no_activity_outcome_column(self):
        with (INTAKE / "primary_evidence_review_queue.csv").open(newline="", encoding="utf-8") as stream:
            fieldnames = csv.DictReader(stream).fieldnames
        forbidden = {"ki", "pki", "pbind_ki", "affinity", "activity_value", "outcome"}
        self.assertTrue(fieldnames)
        self.assertFalse(forbidden.intersection({name.lower() for name in fieldnames}))


if __name__ == "__main__":
    unittest.main()
