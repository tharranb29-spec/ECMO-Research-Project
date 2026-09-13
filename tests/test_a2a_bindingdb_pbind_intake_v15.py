import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "track3_a2a" / "outputs" / "v1.5" / "external_pbind_intake"


class TestA2ABindingDBPBindIntakeV15(unittest.TestCase):
    def test_public_intake_is_label_blind_and_not_frozen(self):
        audit = json.loads((OUTPUT / "intake_audit.json").read_text())
        with (OUTPUT / "eligible_for_primary_review.csv").open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            first = next(reader)
        self.assertFalse(audit["outcomes_exposed_to_public_workspace"])
        self.assertFalse(audit["outcomes_unmasked"])
        self.assertFalse(audit["membership_frozen"])
        self.assertNotIn("affinity", fields)
        self.assertNotIn("pbind", [field.lower() for field in fields])
        self.assertEqual(first["primary_evidence_review_status"], "pending_dual_review")
        self.assertTrue(audit["floor_status_before_primary_review"]["molecules"])
        self.assertTrue(audit["floor_status_before_primary_review"]["generic_scaffolds"])


if __name__ == "__main__":
    unittest.main()
