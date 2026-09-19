# Track 3 dashboard contracts v1

These schemas define the read-only boundary between audited Track 3 artifacts and
the static dashboard. `build_track3_dashboard.py` is the only projector. It reads
declared repository artifacts, records each source path and SHA-256 digest, and
emits `outputs/dashboard/v1/contracts.json` plus the browser bundle.

The contracts never authorize label admission, model promotion, candidate release,
or Tier B MD. Autonomous updates are represented only as `shadow_proposal` records.
Any future breaking field change requires a new version directory.

## Competition-scope overlay

The v1.6.1 governance release adds a non-breaking policy overlay at
`outputs/v1.6.1/governance/dashboard_scope_contract.json`, validated by
`governance-scope.schema.json`. Dashboard consumers must apply this overlay before
rendering a review queue. It prohibits scientific rank and candidate-probability
fields, permits only the enumerated set-level composition rates, separates the
unlabeled queue from the external-confirmation floor, and keeps autonomy shadow-only.
