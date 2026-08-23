# GNINA validation protocol

## Purpose

Validate the docking engine and pose-recovery workflow before GNINA scores are allowed to influence ECMO candidate ranking. This protocol separates software validation, Siglec-family structural validation, and direct Siglec-9 target validation.

## Fixed protocol

- GNINA version: 1.3.3, pinned Docker image
- Execution: CPU-only on Apple Silicon through linux/amd64 emulation
- Receptor preparation: PDB2PQR 3.6.2, AMBER force field, PROPKA titration states at pH 7.4, hydrogen-bond optimization
- Ligand coordinates and chemistry: instance-specific SDF from RCSB ModelServer
- Sampling: five fixed seeds, exhaustiveness 8, CNN rescore
- Primary pose criterion: top-pose symmetry-aware heavy-atom RMSD below 2.0 A
- Score reporting: minimized affinity in kcal/mol, CNNscore, and CNNaffinity pK are kept separate

## Benchmark results

### 2G5R / NXD - passed

Human Siglec-7 N-terminal domain complexed with oxamido-Neu5Ac. This is a Siglec-family engine and pose-recovery benchmark, not direct Siglec-9 validation.

- Seed RMSDs: 1.148, 1.388, 0.534, 1.893, 1.384 A
- Passes: 5 of 5
- Mean RMSD: 1.270 +/- 0.493 A
- Mean minimized affinity: -4.842 +/- 0.573 kcal/mol
- Mean CNNscore: 0.725 +/- 0.128
- Mean CNNaffinity: 3.448 +/- 0.211 pK

### 7QUI / F9I - protocol review required

Human Siglec-8 N-terminal domain with a large sulfonamide sialoside analogue. Baseline and tighter-box trials did not meet the predefined full-ligand RMSD threshold. Best observed RMSD was 2.669 A. This remains a flexible-glycomimetic challenge benchmark and must not be retrospectively tuned to claim success.

## Current decision

GNINA execution and a simpler Siglec-family pose-recovery case are validated. Direct Siglec-9 candidate ranking remains locked because no experimental Siglec-9/MTTSNeu5Ac or Siglec-9/BTCNeu5Ac crystal structure is available and the published work used modeled complexes.

## Direct Siglec-9 asset audit

- Canonical identity: reviewed human SIGLEC9 UniProt Q9Y336.
- Reconstruction source: AlphaFold DB `AF-Q9Y336-F1-model_v6`, model date 2025-08-01.
- Domain extracted: residues 18-144, matching the reported V-set construct span.
- Structural audit: mean pLDDT 90.83; P53 peptide state is cis (omega -6.12 degrees), matching the major NMR-supported conformer.
- Receptor preparation: PDB2PQR 3.6.2, AMBER naming, PROPKA pH 7.4, hydrogen-bond optimization.
- Important mismatch: the reconstruction is canonical WT C36, while the supporting information reports a C36S NMR construct. It is therefore a provisional biological reconstruction, not an author-identical study model.
- Ligand audit: exact stereochemically complete BTCNeu5Ac and MTTSNeu5Ac 3D coordinates were not deposited with the article and were not found in curated public chemical records. Names or LLM-generated SMILES are not acceptable substitutes.
- Published affinity anchors: MTTSNeu5Ac ITC Kd 9.6 +/- 0.8 micromolar; BTCNeu5Ac ITC Kd 19.5 +/- 1.3 micromolar.
- Published placement was NMR-guided manual docking against PDB 7QUI followed by five independent 500 ns AMBER MD trajectories. A blind GNINA result is not a reproduction of that workflow.

## Next scientific gate

1. Obtain the authors' model coordinates, or approve a separately labeled WT and C36S reconstruction pair.
2. Obtain author-supplied BTCNeu5Ac and MTTSNeu5Ac structure files, or have a carbohydrate chemist reconstruct and sign off the complete stereochemistry.
3. Reproduce the published R120, W128, and N129 interaction constraints before redocking.
4. Run five seeds and report uncertainty without combining unlike GNINA outputs.
5. Compare predictions with published affinity evidence.
6. Only then set the dashboard target-validation flag to ready.

Primary references:

- GNINA: https://github.com/gnina/gnina
- GNINA validation paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC8191141/
- Siglec-9 NMR/MD study: https://pmc.ncbi.nlm.nih.gov/articles/PMC10877568/
- RCSB 2G5R: https://www.rcsb.org/structure/2G5R
- RCSB 7QUI: https://www.rcsb.org/structure/7QUI
