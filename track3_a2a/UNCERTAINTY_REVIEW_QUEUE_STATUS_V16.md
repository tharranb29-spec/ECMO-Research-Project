# Uncertainty-aware review queue status v1.6

Status date: 2026-09-19

## Decision

The claimed 335-candidate prediction analysis, proposed 276-candidate screen-eligible subset, and derivation of the `pBind_Ki` threshold `6.7412` are not present on GitHub `main`, the available remote workstream branches, or the local source repository. The claims are therefore unverified and are not used to select, order, or characterize any molecule.

The intake fails closed. The dashboard-ready queue projects all 240 records in the existing audited, outcome-blind evidence ledger without an ordinal rank. Every record is blocked at `validated_prediction_and_interval_unavailable`; no record is called screen-eligible, robust, certified, or a hit.

Because the current audited ledger contains 240 candidates, a 335-row prediction file cannot be admitted by itself. The additional 95 identities would first require a committed, outcome-blind candidate ledger with the same structure, scaffold, evidence, and provenance controls; prediction rows that are absent from the audited ledger are rejected.

## Interval semantics

The source artifact must state how its 90% intervals were built and provide hashed model, code, calibration, and threshold-derivation artifacts. Once those gates pass:

- `upper_90 >= 6.7412` means only **screen-eligible / not ruled out**;
- `lower_90 >= 6.7412` is required for **robust threshold support**;
- `upper_90 < 6.7412` means ruled out by that interval rule.

The teammate's original upper-versus-lower rule cannot be determined because the source artifact is absent. Neither permitted label is a per-molecule hit probability or experimental validation.

## Queue contract

`config/uncertainty_review_queue_input.v1.json` lists every required source column. Any missing column, unknown or duplicate candidate, structure mismatch, non-finite interval, interval that excludes its point prediction, provenance hash mismatch, unverified threshold, external-outcome access, or docking-based selection rejects the entire prediction artifact.

The queue exposes deterministic eligibility, generic Murcko scaffold composition, evidence quality, applicability status, 90% intervals, and empty human-disposition fields. It contains no ordinal rank, per-position result, docking feature, or per-molecule hit probability. Set-level proportions use 95% Wilson score intervals; zero-denominator quantities are explicitly not estimable.

## Non-conflation rule

A review shipment of at least 60 records is an operational human-review workload only. It does not satisfy the frozen external-confirmation gate. External confirmation separately requires at least 60 evidence-admitted molecules, at least 20 independent generic Murcko scaffolds, independent sealed outcomes, membership frozen before the one-time join, and the predeclared external evaluation gates.
