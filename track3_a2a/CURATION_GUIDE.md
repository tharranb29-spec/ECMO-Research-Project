# Functional evidence curation gate, version 1.2

## Active review artifact

Use `data/curated/chembl251_curation_plan_220_v1.2.csv`. The unversioned CSV is
preserved as its hashed source and must not be edited after review begins.

The target is 220 accepted benchmark molecules, not merely 220 docked records:

- 65 proposed agonists and 155 proposed antagonists.
- 216 generic scaffolds in the planned review set.
- Batch 1: 19 records with an enriched dossier covering 30 publications and 49
  human A2A assays.
- Batches 2-5: 201 additional records reviewed only after Batch 1 is audited.

All records remain training-ineligible until dual review and scaffold partitioning.

## Evidence tiers

- `tier_1`: direct human A2A functional assay with an interpretable agonist or
  antagonist direction. Eligible for the primary analysis after partitioning.
- `tier_2`: unambiguous functional assignment in a primary source, but direct
  machine-readable assay details are incomplete. Sensitivity analysis only.
- Binding-only, partial agonist, inverse agonist, ambiguous, wrong-context, and
  unresolved evidence is rejected from the binary benchmark.

Do not infer function from Ki, Kd, GNINA scores, receptor occupancy, chemical
similarity, or an LLM summary. Prospective MW/QED filters do not determine
retrospective benchmark eligibility.

## Independent dual review

Two different people independently fill:

- `reviewer_1`, `decision_1`, and `evidence_tier_1`
- `reviewer_2`, `decision_2`, and `evidence_tier_2`
- `tier_rationale` and `review_notes`

If class or tier differs, a third person fills `adjudicator`, `final_decision`,
and `final_evidence_tier`.

Allowed decisions:

- `accept_agonist`
- `accept_antagonist`
- `reject_binding_only`
- `reject_context`
- `reject_conflict`
- `needs_full_text`

Reviewers use `chembl251_batch_01_evidence_dossier.json` and the linked DOI,
PubMed, ChEMBL document, and ChEMBL assay pages. A review article alone cannot
establish Tier 1; trace the claim to primary experimental evidence.

## Validate decisions

After saving review decisions, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m track3_a2a.admit_reviewed_benchmark_v12
```

The validator requires two distinct reviewers, checks class and tier agreement,
requires adjudication for disagreement, hashes the plan, and writes a
reviewed-but-unpartitioned snapshot. Accepted records remain blocked from model
training until the scaffold partitions and locked holdout are frozen.

## Gate after Batch 1

1. Calculate class agreement and tier agreement between reviewers.
2. Resolve disagreements without reference to future docking/model results.
3. Confirm the Tier 1 agonist yield before opening Batch 2.
4. Continue balanced batches and replace rejected records as needed.
5. Freeze and hash scaffold-grouped development and locked-holdout partitions.
6. Only then begin production GNINA docking and model fitting.
