# Formal dual-review guide

## Files

- Tharran completes `outputs/v1.2/formal_review/tharran_blinded_review.csv`.
- Lucky completes `outputs/v1.2/formal_review/lucky_blinded_review.csv`.

Do not exchange decisions until both packets are complete. Proposed model labels
and docking outputs are intentionally absent.

## Required fields

For every row, each reviewer personally enters:

- `decision`: one allowed value listed below.
- `evidence_tier`: `tier_1` or `tier_2` for accepted records; blank for rejected
  or unresolved records.
- `source_checked`: `yes` only after checking the cited assay or publication.
- `review_notes`: a short reason, especially for exclusions or uncertainty.
- `reviewed_at_utc`: ISO 8601 time, for example `2026-09-10T12:00:00Z`.

## Decision vocabulary

- `accept_agonist`: direct evidence supports human A2A agonist activity.
- `accept_antagonist`: direct evidence supports human A2A antagonist activity.
- `reject_binding_only`: affinity/binding evidence without functional direction.
- `reject_context`: wrong receptor, species, assay context, or endpoint.
- `reject_conflict`: irreconcilable functional assignments.
- `needs_full_text`: evidence cannot be resolved from available records.

## Evidence tiers

- `tier_1`: direct human A2A functional assay with an interpretable agonist or
  antagonist direction. Eligible for primary analysis after agreement.
- `tier_2`: unambiguous functional assignment in a primary source, but direct
  machine-readable assay detail is incomplete. Sensitivity analysis only.

Partial agonists, inverse agonists, ambiguous compounds, and binding-only
records are not accepted into the primary binary endpoint.

## Reconciliation

Agreement on class and tier can be admitted after both files are complete.
Class or tier disagreements require a named third-person adjudicator. A program
may validate and merge the forms, but it may not create or sign human decisions.
