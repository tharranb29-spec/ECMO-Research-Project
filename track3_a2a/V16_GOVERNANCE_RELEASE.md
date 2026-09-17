# Track 3 v1.6 governance release

Status date: 2026-09-17

Competition deadline: 2026-09-30

Scope: protocol and model governance only

## Purpose

This release gives reviewers one deterministic, machine-checkable package for the frozen v1.6 decisions and their current evidence state. It does not refit a model, select a new model, join external outcomes, admit the external cohort, unlock MD, or modify presentation material.

## Frozen authority

- Primary endpoint: direct wild-type human A2A `pBind_Ki`.
- Primary external predictor: `AB_Ridge(alpha=1.0)`.
- RF comparators: 500 trees, `max_features=sqrt`, `min_samples_leaf=1`, seed 20260914, one job.
- External outcome firewall: sealed until membership, standardization, applicability thresholds, predictions, and hashes are frozen.
- Historical v1.3.1 holdout: never reused for selection.
- Retroactive tuning or automatic model replacement: prohibited.

Development metrics remain development-only evidence. They cannot be described as external confirmation. Docking and MD remain separate structural channels and cannot create potency labels or rescue a failed external model gate.

## Release contents

The deterministic builder writes `outputs/v1.6/governance/`:

- `governance_checks.csv`: every cross-artifact invariant and its evidence;
- `model_evidence_table.csv`: identical-cohort development metrics with governance roles and claim limits;
- `gate_status_table.csv`: current release, external, Tier A, and Tier B lock states;
- `evidence_artifact_inventory.csv`: source artifact paths, hashes, sizes, and roles;
- `governance_status.json`: concise machine-readable status for competition integration;
- `governance_release_manifest.json`: source and release hashes plus a deterministic release signature.

Run from the repository root:

```bash
python3 track3_a2a/build_v16_governance_release.py
python3 -m unittest tests.test_a2a_governance_release_v16
```

The builder fails closed if any frozen file, protocol decision, model mapping, prediction hash, outcome-firewall assertion, or current MD lock state does not reconcile. A legitimate future state change must first update its authoritative audited artifact; it must never be hidden by weakening a governance check.

## Current interpretation

Workstream A is release-ready. External confirmation remains pending because pass 2 and cohort freeze are incomplete, no external outcome join has occurred, and model promotion is prohibited. All six prospectively declared v1.6.4 staged-equilibration replicas passed, so the frozen Tier A 50 ns pilot-production campaign is authorized but has not started. This authorization is not a control-stability result and does not unlock Tier B; Tier B remains locked until both Tier A controls pass the production rule in at least two of three replicas. These open gates are expected status, not failures of the Workstream A governance release.
