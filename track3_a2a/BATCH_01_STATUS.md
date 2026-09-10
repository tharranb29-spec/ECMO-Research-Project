# Batch 1 evidence-review status, specification v1.2

## Purpose

Batch 1 contains the 19 highest-priority records from the provisional A2A
agonist/antagonist queue. It is an evidence-curation batch, not a validated
training set and not a GNINA screening result.

## Automated provenance checks completed

- 19 molecules: 5 proposed agonists and 14 proposed antagonists.
- 16 generic scaffolds represented.
- 30 unique ChEMBL publications, all with DOI links; 29 have PubMed IDs.
- 49 unique ChEMBL assays.
- All 49 assays identify target `CHEMBL251`, organism `Homo sapiens`, and carry
  ChEMBL target-confidence score 9.
- Training-eligible records: 0 pending independent dual review.

The machine-readable dossier is
`data/curated/chembl251_batch_01_evidence_dossier.json`. It preserves assay
descriptions, activity rows, publication metadata, DOI/PubMed links, and review
questions for every Batch 1 molecule.

## Review risks requiring human judgment

Two supporting titles appear review- or perspective-oriented. Evidence traced
only to a review must be confirmed in a primary experimental source before it
can support an evidence tier.

Four assay descriptions contain radiolabeled terminology but describe signaling
readouts: three measure cAMP and one measures `[35S]GTPgammaS`. Do not classify
these as binding-only from keywords; inspect whether the measured endpoint is
signaling or ligand occupancy.

Some publications focus on A1, A3, glaucoma, or broad adenosine-receptor
programs even though the linked assay identifies human A2A. Reviewers must
confirm that the specific compound and A2A functional result appear in the
source.

## Required action

Two different reviewers independently complete Batch 1 in
`data/curated/chembl251_curation_plan_220_v1.2.csv`. Each reviewer records both
the functional-class decision and `tier_1` or `tier_2` evidence. Disagreements
require a third adjudicator.

After decisions are entered, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m track3_a2a.admit_reviewed_benchmark_v12
```

Accepted records remain blocked from training until scaffold-grouped development
and locked-holdout partitions are frozen and hashed.
