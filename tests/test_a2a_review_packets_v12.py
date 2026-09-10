import unittest

from track3_a2a.prepare_dual_review_packets_v12 import FIELDS, REVIEWERS


class A2AReviewPacketTests(unittest.TestCase):
    def test_two_distinct_named_reviewers(self):
        self.assertEqual(REVIEWERS, ("Tharran", "Lucky"))
        self.assertEqual(len({name.casefold() for name in REVIEWERS}), 2)

    def test_packet_requires_personal_decision_fields(self):
        for field in ("decision", "evidence_tier", "source_checked", "reviewed_at_utc"):
            self.assertIn(field, FIELDS)


if __name__ == "__main__":
    unittest.main()
