# Track 3 dashboard contracts v1

These schemas define the read-only boundary between audited Track 3 artifacts and
the static dashboard. `build_track3_dashboard.py` is the projector for the core
contract bundle. It reads declared repository artifacts, records each source path
and SHA-256 digest, and emits `outputs/dashboard/v1/contracts.json` plus the
browser bundle.

The contracts never authorize label admission, sealed-outcome access, model
promotion, candidate release, or Tier B MD. Autonomous work is represented in the
`shadow-actions` contract as bounded proposals with an executor, authority limit,
required gate, prohibited actions, and source digest. Any future breaking field
change requires a new version directory.

The candidate-portfolio projection is an unordered human-review composition
summary governed only by the frozen eligibility contract. Dual-state docking is
separate historical structural context: it cannot admit, prioritize, order, or
release a record. MD is optional mechanistic context and is not required for
review-queue membership, dashboard operation, or release; its historical
incomplete and Tier B locked states remain visible without becoming dependencies.

`discovery-run.schema.json` defines the runtime live/cached shadow workflow,
resolved upstream contracts, unordered queue composition, human disposition, and
append-only runtime audit chain. Missing upstream contracts fail closed. Provider
mode is explicit: `auto` may fall back from live DeepSeek to the cached demo,
whereas `live` never falls back and surfaces provider failure.

## Competition-scope overlay

The v1.6.1 governance release adds a non-breaking policy overlay at
`outputs/v1.6.1/governance/dashboard_scope_contract.json`, validated by
`governance-scope.schema.json`. Dashboard consumers must apply this overlay before
rendering a review queue. It prohibits scientific rank and candidate-probability
fields, permits only the enumerated set-level composition rates, separates the
unlabeled queue from the external-confirmation floor, and keeps autonomy shadow-only.

`uncertainty-review-queue.schema.json` defines the non-ranked review-queue payload.
Its records expose evidence quality, scaffold composition, applicability, validated
90% intervals, deterministic eligibility, and human disposition. The contract
forbids outcome-loaded or docking-selected queue data and does not carry ordinal
positions or per-molecule hit probabilities.

`md-production-cutoff.schema.json` defines the separate live-production snapshot
contract projected by `ingest_tier_a_production_status_v16.py`. It reports
observed Tier A progress and Tier B lock state without changing the completed
equilibration gate or inferring anything about model-training completeness.
