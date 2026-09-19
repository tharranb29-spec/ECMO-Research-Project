# Track 3 dashboard contracts v1

These schemas define the read-only boundary between audited Track 3 artifacts and
the static dashboard. `build_track3_dashboard.py` is the only projector. It reads
declared repository artifacts, records each source path and SHA-256 digest, and
emits `outputs/dashboard/v1/contracts.json` plus the browser bundle.

The contracts never authorize label admission, sealed-outcome access, model
promotion, candidate release, or Tier B MD. Autonomous work is represented in the
`shadow-actions` contract as bounded proposals with an executor, authority limit,
required gate, prohibited actions, and source digest. Any future breaking field
change requires a new version directory.

`discovery-run.schema.json` defines the runtime live/cached shadow workflow,
resolved upstream contracts, unordered queue composition, human disposition, and
append-only runtime audit chain. Missing upstream contracts fail closed.
