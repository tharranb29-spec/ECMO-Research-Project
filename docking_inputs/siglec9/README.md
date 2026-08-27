# Siglec-9 GNINA bridge batch

## Scope

This directory contains a seven-ligand comparative docking bridge for the ECMO dashboard. Five controls use reviewed experimental coordinates from RCSB. BTCNeu5Ac and MTTSNeu5Ac are literature-defined reconstructions documented in `LIGAND_RECONSTRUCTION_NOTES.md`; they are not deposited author SDFs. The receptor is a provisional AlphaFold-derived Siglec-9 V-set reconstruction. Results are computational triage evidence and must not be reported as measured affinity.

## Ligand structures

| Dashboard name | File | Coordinate provenance | Intended role |
| --- | --- | --- | --- |
| Neu5Ac | `Neu5Ac.sdf` | [RCSB CCD SIA](https://www.rcsb.org/ligand/SIA) | Minimal sialic-acid control |
| 3SLN | `3SLN.sdf` | [RCSB BIRD PRD_900067 / PDB 5BNP](https://www.rcsb.org/ligand/PRD_900067) | Natural Siglec-9 ligand |
| 6SLN | `6SLN.sdf` | [RCSB BIRD PRD_900046 / PDB 5BNO](https://www.rcsb.org/ligand/PRD_900046) | Natural Siglec-9 ligand |
| sLeX | `sLeX.sdf` | [RCSB BIRD PRD_900122 / PDB 5AJC](https://www.rcsb.org/ligand/PRD_900122) | Natural Siglec-9 ligand |
| 6-prime-sulfo-sLeX | `6prime_sulfo_sLeX.sdf` | [RCSB PDB 2N7B, model 1](https://www.rcsb.org/structure/2N7B) | Related-Siglec specificity control |
| BTCNeu5Ac | `BTCNeu5Ac.sdf` | Literature-defined reconstruction; chemistry review pending | Published high-affinity glycomimetic |
| MTTSNeu5Ac | `MTTSNeu5Ac.sdf` | Literature-defined reconstruction; chemistry review pending | Published high-affinity glycomimetic |

Exact paths, checksums, experimental Kd values, receptor box, and caveats are in `five_ligand_batch.json` and `structure_registry.json`.

## Reproducible protocol

The current dashboard combines the existing five-run controls (seeds 42-46) with the teammate-specified seed-42 cross-check for the two reconstructed glycomimetics. Every run uses GNINA 1.3.x, exhaustiveness 64, `cnn_scoring=rescore`, and one output pose. A future full repeat can run all candidates through the same multi-seed protocol after chemistry review.

## Current comparative output

| Raw affinity order | Ligand | Runs | Minimized affinity (kcal/mol) | CNNscore | CNNaffinity (pK) | Pose gate |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | BTCNeu5Ac | 1 | -7.502 | 0.2714 | 5.005 | Review |
| 2 | MTTSNeu5Ac | 1 | -7.475 | 0.6195 | 6.253 | Pass |
| 3 | sLeX | 5 | -7.051 | 0.3035 | 4.593 | Review |
| 4 | 6-prime-sulfo-sLeX | 5 | -6.973 | 0.1927 | 4.653 | Review |
| 5 | 6SLN | 5 | -6.907 | 0.4947 | 4.743 | Review |
| 6 | 3SLN | 5 | -6.825 | 0.3062 | 3.868 | Review |
| 7 | Neu5Ac | 5 | -5.857 | 0.4594 | 3.856 | Review |

The raw order uses minimized affinity only. BTCNeu5Ac is first by raw affinity but fails the predefined CNNscore 0.50 pose-quality gate. MTTSNeu5Ac is the only pose-gated candidate and therefore receives target-specific GNINA rank 1. This is not evidence of Siglec-9 agonism.

## Experimental cross-check

Published Siglec-9 ITC values are 19.5 +/- 1.3 uM for BTCNeu5Ac (pKd 4.710) and 9.6 +/- 0.8 uM for MTTSNeu5Ac (pKd 5.018). The CNNaffinity errors are +0.295 pK (1.97-fold Kd error) and +1.235 pK (17.19-fold Kd error), respectively. With only two matched compounds, Spearman correlation is intentionally left pending; at least three matched values are required even for an exploratory coefficient.

## Autonomous handoff

`docking_inputs/ligand_structure_catalog.json` maps reviewed aliases to these files. Autonomous literature leads only become GNINA-ready when they resolve to a catalog entry with receptor, pocket, checksum, and provenance. Unknown names and unverified LLM-supplied structures remain blocked for manual review.
