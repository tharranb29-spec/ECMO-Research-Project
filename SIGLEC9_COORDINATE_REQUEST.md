# Siglec-9 coordinate request and acceptance checklist

## Purpose

Request the exact structural assets needed to reproduce the published
Siglec-9/BTCNeu5Ac and Siglec-9/MTTSNeu5Ac modeling workflow before GNINA
scores influence candidate ranking.

## Ready-to-send request

Subject: Request for Siglec-9 glycomimetic model coordinates for academic validation

Dear Dr. Ereño-Orbea and colleagues,

We are conducting a non-commercial university project on immune-modulating
ECMO interfaces and are evaluating whether GNINA can support prioritization of
Siglec-9 ligands. We are using your ACS Chemical Biology study,
"Unraveling Molecular Recognition of Glycan Ligands by Siglec-9 via NMR
Spectroscopy and Molecular Dynamics Modeling" (DOI:
10.1021/acschembio.3c00664), as the primary experimental reference.

To avoid reconstructing stereochemistry or receptor states incorrectly, would
you be willing to share the following research files, if available?

1. The AlphaFold and/or RoseTTAFold Siglec-9 V-set coordinate model used in the study.
2. The starting and representative final coordinates for the Siglec-9-BTCNeu5Ac complex.
3. The starting and representative final coordinates for the Siglec-9-MTTSNeu5Ac complex.
4. Stereochemically complete BTCNeu5Ac and MTTSNeu5Ac structures in SDF, MOL2, or PDB format.
5. Any AMBER topology/parameter files or atom mappings used for the two glycomimetics.
6. Confirmation of whether the modeled receptor sequence was WT C36 or the reported C36S NMR construct.

The files would be used only for academic method validation. We will retain
the original provenance, clearly label modeled structures, and will not treat
docking scores as experimental binding affinity.

Thank you for considering this request.

Sincerely,

ECMO Interface Research Team
Zhejiang University International School of Medicine

## Acceptance checklist

Do not mark an asset as verified until all applicable items are recorded in
`docking_inputs/structure_registry.json`.

- Source person or repository and retrieval date are recorded.
- Original filename, format, and SHA-256 checksum are recorded.
- Receptor sequence accession, residue span, and C36/C36S state are confirmed.
- P53 cis/trans state and model-generation method are confirmed.
- Ligand atom identities, formal charge, glycosidic linkages, and all stereocenters are reviewed.
- Ligand protonation and tautomer choices at pH 7.4 are documented.
- Published R120, W128, and N129 contacts are reproduced before GNINA redocking.
- Five seeded runs are completed and uncertainty is reported.
- GNINA outputs remain separate from ITC Kd values and are labeled computational predictions.
