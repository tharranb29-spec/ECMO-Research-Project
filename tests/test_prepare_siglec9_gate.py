import tempfile
import unittest
from pathlib import Path

from prepare_siglec9_gate import crop_v_set, dihedral


class Siglec9GateTests(unittest.TestCase):
    def test_dihedral_identifies_cis_geometry(self):
        angle = dihedral((0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0))
        self.assertAlmostEqual(abs(angle), 0.0, places=6)

    def test_crop_rejects_missing_domain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.pdb"
            output = Path(temp_dir) / "output.pdb"
            source.write_text("END\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "No chain A residues"):
                crop_v_set(source, output)


if __name__ == "__main__":
    unittest.main()
