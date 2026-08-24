# Siglec-9 GNINA bridge batch

## Scope

This directory contains a five-ligand comparative docking bridge for the ECMO
dashboard. The ligand coordinates have reviewed RCSB provenance, but they are
not experimental Siglec-9 co-crystal poses. The receptor is a provisional
AlphaFold-derived Siglec-9 V-set reconstruction. Results are computational
triage evidence and must not be reported as measured affinity.

## Reviewed ligand structures

| Dashboard name | File | Coordinate provenance | Intended role |
| --- | --- | --- | --- |
| Neu5Ac | `Neu5Ac.sdf` | [RCSB CCD SIA](https://www.rcsb.org/ligand/SIA) | Minimal sialic-acid control |
| 3SLN | `3SLN.sdf` | [RCSB BIRD PRD_900067 / PDB 5BNP](https://www.rcsb.org/ligand/PRD_900067) | Natural Siglec-9 ligand |
| 6SLN | `6SLN.sdf` | [RCSB BIRD PRD_900046 / PDB 5BNO](https://www.rcsb.org/ligand/PRD_900046) | Natural Siglec-9 ligand |
| sLeX | `sLeX.sdf` | [RCSB BIRD PRD_900122 / PDB 5AJC](https://www.rcsb.org/ligand/PRD_900122) | Natural Siglec-9 ligand |
| 6-prime-sulfo-sLeX | `6prime_sulfo_sLeX.sdf` | [RCSB PDB 2N7B, model 1](https://www.rcsb.org/structure/2N7B) | Related-Siglec specificity control |

The exact paths, SHA-256 checksums, receptor box, and scientific caveats are in
`five_ligand_batch.json`.

## Reproducible run

```bash
GNINA_BINARY=./scripts/gnina-docker \
GNINA_MODE=local \
GNINA_EXHAUSTIVENESS=64 \
GNINA_RUN_COUNT=5 \
GNINA_SEED_BASE=42 \
GNINA_TIMEOUT_SECONDS=1800 \
python3 gnina_pipeline.py \
  --manifest docking_inputs/siglec9/five_ligand_batch.json \
  --mode local

python3 build_dashboard_bundle.py
```

The batch runs seeds 42-46 with one output mode per ligand. The dashboard reads
`outputs/gnina_bridge_results.json`.

## Current comparative output

| Preliminary order | Ligand | Mean minimized affinity (kcal/mol) | Mean CNNscore | Mean CNNaffinity (pK) | Pose gate |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | sLeX | -7.051 | 0.3035 | 4.593 | Review |
| 2 | 6-prime-sulfo-sLeX | -6.973 | 0.1927 | 4.653 | Review |
| 3 | 6SLN | -6.907 | 0.4947 | 4.743 | Review |
| 4 | 3SLN | -6.825 | 0.3062 | 3.868 | Review |
| 5 | Neu5Ac | -5.857 | 0.4594 | 3.856 | Review |

All five mean CNNscores are below the predefined 0.50 pose-quality threshold.
Therefore this is a raw comparative affinity order, not a validated
target-specific GNINA rank and not evidence of Siglec-9 agonism.

## Autonomous handoff

`docking_inputs/ligand_structure_catalog.json` maps reviewed aliases to these
files. Autonomous literature leads only become GNINA-ready when they resolve to
a catalog entry with receptor, pocket, checksum, and provenance. Unknown names
and unverified LLM-supplied structures remain blocked for manual review.
