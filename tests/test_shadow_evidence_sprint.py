import copy
import json
import unittest
from pathlib import Path

from track3_a2a import build_shadow_evidence_sprint_v161 as sprint


class ShadowEvidenceSprintTests(unittest.TestCase):
    def test_frozen_inputs_and_metadata_snapshot_preserve_outcome_firewall(self):
        pass1 = json.loads(sprint.PASS1.read_text())
        pass2 = json.loads(sprint.PASS2.read_text())
        snapshot = json.loads(sprint.SNAPSHOT.read_text())
        release = sprint.build_release(pass1, pass2, snapshot)
        self.assertEqual(release["counts"]["frozen_candidate_records"], 240)
        self.assertEqual(release["counts"]["publication_groups_checked"], sprint.LIMIT)
        self.assertEqual(release["counts"]["other_receptor_title_flags"], 3)
        self.assertEqual(release["counts"]["source_grounded_unresolved_candidates"], 29)
        self.assertTrue(all("molecule_identity" in row["unresolved_fields"] for row in release["source_grounded_review"]))
        self.assertFalse(any(release["firewall"].values()))
        self.assertEqual(len({row["candidate_id"] for row in release["candidate_worklist"]}), 240)
        self.assertNotIn("standardized_smiles", release["candidate_worklist"][0])
        tampered = copy.deepcopy(pass2)
        tampered["outcome_fields_loaded"] = True
        with self.assertRaisesRegex(RuntimeError, "Outcome firewall"):
            sprint.build_release(pass1, tampered, snapshot)


if __name__ == "__main__":
    unittest.main()
