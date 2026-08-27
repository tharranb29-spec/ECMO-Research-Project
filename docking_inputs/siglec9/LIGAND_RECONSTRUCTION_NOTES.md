# BTCNeu5Ac and MTTSNeu5Ac reconstruction record

## Evidence status

No deposited, curated SDF for either complete glycomimetic was identified in the searched public chemical and glycan repositories as of 2026-08-27. The files in this directory are literature-defined 3D reconstructions for computational triage, not author-deposited coordinates and not experimental Siglec-9 poses.

## Chemical definitions

- **BTCNeu5Ac:** 5-N-[(1-benzhydryl-1H-1,2,3-triazol-4-yl)methyl carbamate]-Neu5Ac alpha(2-6)Gal beta(1-4)GlcNAc. Published Siglec-9 ITC Kd: 19.5 +/- 1.3 uM.
- **MTTSNeu5Ac:** 9N-[5-(2-methylthiazol-4-yl)thiophene-2-sulfonamide]-Neu5Ac alpha(2-6)Gal beta(1-4)GlcNAc. Published Siglec-9 ITC Kd: 9.6 +/- 0.8 uM.

Primary affinity source: Atxabal et al., ACS Chemical Biology (2024), DOI 10.1021/acschembio.3c00664.

## Reconstruction method

The experimentally sourced 6SLN scaffold from RCSB PDB 5BNO / BIRD PRD_900046 was used to preserve the alpha(2-6)Neu5Ac-Gal-GlcNAc stereochemical framework. The literature-defined C5 BTC carbamate or C9 MTTS sulfonamide substituent was added, then a 3D conformer was generated with the Open Babel build pinned inside `gnina/gnina:v1.3.3`. Isomeric-SMILES round-trip checks matched the intended connection table.

| File | Formula | Molecular weight | SHA-256 |
| --- | --- | ---: | --- |
| `BTCNeu5Ac.sdf` | C40H53N5O20 | 923.870 | `e5503c295aee25b04371b4fc98495bdc7d0689e555ded921efd60f0a969bf475` |
| `MTTSNeu5Ac.sdf` | C33H48N4O20S3 | 916.944 | `ae2a08dee2595552e1e88e0812181242e752dc61580f94f43c42631f8c49a5d3` |

## Required review gate

A chemist must independently review atom connectivity, stereochemistry, protonation, charge state, and conformer preparation. GNINA results from these files may be displayed as provisional computational cross-checks, but must not unlock the validated-affinity ranking gate or be described as measured binding affinity.
