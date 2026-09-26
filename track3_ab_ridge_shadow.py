"""Read-only development-fit AB Ridge inference for the Track 3 shadow UI."""

from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "track3_a2a/outputs/v1.6/model_reproduction/ab_ridge_shadow_scorer.json"
SOURCES = {
    "protocol": ROOT / "track3_a2a/config/protocol.v1.6.json",
    "summary": ROOT / "track3_a2a/data/curated/activity_molecule_summary_v15_exploratory.csv",
    "features": ROOT / "track3_a2a/outputs/v1.3/docking_clean_computational.csv",
}
DESCRIPTORS = [
    "molecular_weight", "clogp", "h_bond_donors", "h_bond_acceptors",
    "rotatable_bonds", "tpsa", "heavy_atom_count", "qed",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def load_scorer() -> dict:
    try:
        import rdkit
    except ImportError as exc:
        raise RuntimeError("RDKit is not installed.") from exc
    if not ARTIFACT.is_file():
        raise RuntimeError("AB Ridge shadow artifact is missing.")
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    if (artifact.get("schema_id") != "a2a-ab-ridge-shadow.v1"
            or artifact.get("status") != "development_fit_only_not_external_confirmation"
            or artifact.get("promotion_allowed") is not False
            or artifact.get("external_outcomes_loaded") is not False
            or artifact.get("training_partition") != "development_only"
            or artifact.get("training_n") != 78
            or artifact.get("training_distinct_molecules") != 69
            or artifact.get("model_id") != "AB_Ridge(alpha=1.0)"
            or artifact.get("endpoint") != "pBind_Ki"
            or artifact.get("fingerprint") != {"type": "Morgan", "radius": 2, "size": 2048}
            or artifact.get("descriptors") != DESCRIPTORS
            or artifact.get("software", {}).get("rdkit") != rdkit.__version__
            or len(artifact.get("weights", [])) != 2048 + len(DESCRIPTORS)
            or len(artifact.get("descriptor_medians", [])) != len(DESCRIPTORS)):
        raise RuntimeError("AB Ridge shadow artifact is incompatible or untrusted.")
    for name, path in SOURCES.items():
        if not path.is_file() or artifact["source_sha256"].get(name) != sha256(path):
            raise RuntimeError(f"AB Ridge source {name} is missing or has changed.")
    if not all(math.isfinite(float(value)) for value in [artifact["intercept"], *artifact["weights"], *artifact["descriptor_medians"]]):
        raise RuntimeError("AB Ridge artifact contains non-finite coefficients.")
    artifact["artifact_sha256"] = sha256(ARTIFACT)
    return artifact


def score_smiles(smiles: str) -> dict:
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator
    from track3_a2a.standardize_quarantine import standardize_smiles

    artifact = load_scorer()
    chemistry = standardize_smiles(smiles)
    mol = Chem.MolFromSmiles(chemistry["standardized_smiles"])
    if mol is None:
        raise ValueError("Standardized SMILES is invalid.")
    fp = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048).GetFingerprint(mol)
    weights = artifact["weights"]
    prediction = artifact["intercept"] + sum(weights[index] for index in fp.GetOnBits())
    for offset, name in enumerate(DESCRIPTORS):
        value = chemistry["descriptors"].get(name)
        if value is None or not math.isfinite(float(value)):
            value = artifact["descriptor_medians"][offset]
        prediction += weights[2048 + offset] * float(value)
    if not math.isfinite(prediction):
        raise RuntimeError("AB Ridge shadow prediction is non-finite.")
    return {
        "pbind_ki": float(prediction),
        "standardization": chemistry,
        "artifact_sha256": artifact["artifact_sha256"],
        "model_id": artifact["model_id"],
        "claim_limit": artifact["claim_limit"],
    }


def capability() -> str:
    try:
        load_scorer()
    except (ImportError, OSError, ValueError, KeyError, RuntimeError, TypeError):
        return "unavailable"
    return "development_only"
