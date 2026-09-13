import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A2A = ROOT / "track3_a2a"


class TestA2AMDCampaignV15(unittest.TestCase):
    def test_colab_notebook_is_complete_and_label_blind(self):
        notebook = json.loads((A2A / "notebooks" / "A2A_FULL_TIER_A_B_COLAB.ipynb").read_text())
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        self.assertIn("run_tier_a_openmm_v15.py", source)
        self.assertIn("run_tier_b_openmm_v15.py", source)
        self.assertIn("analyze_md_campaign_v15.py", source)
        self.assertIn("tier_b_unlocked", source)
        self.assertNotIn("pBind_Ki", source)

    def test_md_acceptance_is_computational(self):
        policy = json.loads((A2A / "config" / "md_construct_policy.v1.5.json").read_text())
        self.assertIn("binding_site_computational_protonation_audit", policy["common_policy"])
        self.assertNotIn("binding_site_manual_review", policy["common_policy"])
        self.assertIn("does not require human validation", policy["tool_boundary"]["reason"])

    def test_failed_membrane_attempt_was_not_accepted(self):
        audit = json.loads((A2A / "outputs" / "v1.5" / "md" / "membrane_patch" / "rejected_attempt_audit.json").read_text())
        self.assertFalse(audit["accepted_as_custom_addmembrane_patch"])
        self.assertFalse(audit["trajectory_production_started"])
        self.assertIn("rejected", audit["status"])


if __name__ == "__main__":
    unittest.main()
