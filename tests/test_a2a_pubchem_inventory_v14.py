import unittest

from track3_a2a.acquire_pubchem_assay_inventory_v14 import parse_summary_payload


class A2APubchemInventoryV14Tests(unittest.TestCase):
    def test_summary_parser_returns_empty_for_missing_payload(self):
        self.assertEqual(parse_summary_payload({}), [])

    def test_summary_parser_extracts_assays(self):
        payload = {"AssaySummaries": {"AssaySummary": [{"AID": 1}, {"AID": 2}]}}
        self.assertEqual([row["AID"] for row in parse_summary_payload(payload)], [1, 2])


if __name__ == "__main__":
    unittest.main()
