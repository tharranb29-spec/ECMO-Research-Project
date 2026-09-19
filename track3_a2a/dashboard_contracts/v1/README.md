# Track 3 dashboard contracts v1

These schemas define the read-only boundary between audited Track 3 artifacts and
the static dashboard. `build_track3_dashboard.py` is the only projector. It reads
declared repository artifacts, records each source path and SHA-256 digest, and
emits `outputs/dashboard/v1/contracts.json` plus the browser bundle.

The contracts never authorize label admission, model promotion, candidate release,
or Tier B MD. Autonomous updates are represented only as `shadow_proposal` records.
Any future breaking field change requires a new version directory.

`uncertainty-review-queue.schema.json` defines the non-ranked review-queue payload.
Its records expose evidence quality, scaffold composition, applicability, validated
90% intervals, deterministic eligibility, and human disposition. The contract
forbids outcome-loaded or docking-selected queue data and does not carry ordinal
positions or per-molecule hit probabilities.
