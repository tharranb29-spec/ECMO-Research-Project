import csv
import unittest
from pathlib import Path

from track3_a2a.admit_reviewed_benchmark import decision_status
from track3_a2a.build_curation_plan import TARGET_COUNTS, build_plan


ROOT = Path(__file__).resolve().parents[1]


class A2ACurationTests(unittest.TestCase):
    def test_plan_has_frozen_size_and_class_targets(self):
        with (ROOT / "track3_a2a/data/curated/chembl251_functional_review_queue.csv").open(newline="") as handle:
            plan = build_plan(list(csv.DictReader(handle)))
        self.assertEqual(len(plan), 220)
        for label, target in TARGET_COUNTS.items():
            self.assertEqual(sum(row["proposed_class"] == label for row in plan), target)
        self.assertEqual(sum(row["curation_batch"] == 1 for row in plan), 19)

    def test_matching_dual_acceptance_is_admitted(self):
        row = {
            "reviewer_1": "A", "decision_1": "accept_agonist",
            "reviewer_2": "B", "decision_2": "accept_agonist",
            "adjudicator": "", "final_decision": "",
        }
        self.assertEqual(decision_status(row), ("accepted", "accept_agonist"))

    def test_disagreement_requires_adjudication(self):
        row = {
            "reviewer_1": "A", "decision_1": "accept_agonist",
            "reviewer_2": "B", "decision_2": "reject_context",
            "adjudicator": "", "final_decision": "",
        }
        self.assertEqual(decision_status(row)[0], "needs_adjudication")

    def test_single_reviewer_cannot_admit(self):
        row = {
            "reviewer_1": "A", "decision_1": "accept_antagonist",
            "reviewer_2": "", "decision_2": "",
            "adjudicator": "", "final_decision": "",
        }
        self.assertEqual(decision_status(row)[0], "pending")


if __name__ == "__main__":
    unittest.main()
