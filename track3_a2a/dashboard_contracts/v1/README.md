# Track 3 dashboard contracts v1

These schemas define the read-only boundary between audited Track 3 artifacts and
the static dashboard. `build_track3_dashboard.py` is the projector for the core
contract bundle. It reads declared repository artifacts, records each source path
and SHA-256 digest, and emits `outputs/dashboard/v1/contracts.json` plus the
browser bundle.

The contracts never authorize label admission, model promotion, candidate release,
or Tier B MD. Autonomous updates are represented only as `shadow_proposal` records.
Any future breaking field change requires a new version directory.

`md-production-cutoff.schema.json` defines the separate live-production snapshot
contract projected by `ingest_tier_a_production_status_v16.py`. It reports
observed Tier A progress and Tier B lock state without changing the completed
equilibration gate or inferring anything about model-training completeness.
