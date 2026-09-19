# Tier A production cutoff ingestion v1.6

## Purpose

`ingest_tier_a_production_status_v16.py` turns read-only `run_status.json` and
`failure_audit.json` artifacts into a deterministic machine report and a concise
human cutoff report. It never reads, starts, stops, or modifies a trajectory.

The committed cutoff uses the supplied 5NM4-ZMA replica-1 snapshot at 5.92 ns.
The original file SHA-256 is
`9ae68e14b58645a619c18f5693b79be98ab45a45f4bbe8130112ffdbc2927c51`;
an exact test fixture preserves that status record without exposing a mutable
Downloads path to the dashboard.

## Validation boundary

Every artifact must match the frozen production contract and repository
authorities for:

- system, replica, and the replica-to-seed mapping;
- production config, aggregate equilibration gate, individual equilibration
  audit, equilibrated state, and release archive SHA-256 digests;
- 50 ns target, target steps, timestep-derived completed ns, and 10 ps status
  cadence;
- CUDA with mixed precision;
- explicit label firewall, started-trajectory flag, and locked Tier B flag;
- valid running, completed, or technical-failure semantics;
- nondecreasing progress and immutable provenance across later snapshots.

A status snapshot records the current step. It does not prove that the binary
checkpoint was supplied. The report therefore records the last scheduled
100 ps checkpoint floor separately and keeps `checkpoint_file_observed=false`.
A completed status must include hashes for the trajectory, state data, final
state, and checkpoint, but this layer does not claim to have read those large
files.

## Safe update procedure

1. Download or copy each new status artifact to an immutable inbox. Do not edit
   the JSON and do not place it in a trajectory directory used by a running job.
2. Record its SHA-256 independently, for example with `shasum -a 256 FILE`.
3. Validate without writing:

   ```bash
   python3 track3_a2a/ingest_tier_a_production_status_v16.py \
     --previous-report track3_a2a/outputs/v1.6/md/tier_a_production_cutoff/cutoff_status.json \
     --run-status /path/to/new/run_status.json \
     --check-only
   ```

4. For a technical failure, use `--failure-audit` instead of `--run-status`.
   The audit must state `technical_failure`, preserve the failed replica, and
   include its error type and message. Never omit or replace that replica after
   inspecting the outcome.
5. After the check succeeds, rerun without `--check-only`. Passing the existing
   report as `--previous-report` makes progress regression, terminal-status
   reversal, seed changes, and provenance drift fatal. Output replacement is
   atomic.
6. Review both generated files, run the deterministic cutoff tests, and commit
   the new source fixture only when repository reproduction is required. Never
   commit trajectory, checkpoint, or state-data binaries through this workflow.

Multiple new artifacts can be supplied by repeating `--run-status` or
`--failure-audit`. A completed replica counts only when its status reaches the
50 ns target and carries all four output hashes. Tier B remains not executed and
locked until the separate Tier A control analysis passes both controls in at
least two of three replicas.

## Dashboard contract

The machine report embeds `a2a-dashboard.md-production-cutoff.v1`. Its core
fields are:

- `status`
- `equilibration_passed_runs` / `equilibration_required_runs`
- `completed_replicas` / `required_replicas`
- `running_replicas`, `failed_replicas`, and `not_observed_replicas`
- `aggregate_reported_ns`, `aggregate_completed_replica_ns`, and `required_ns`
- `tier_b_status`, `tier_b_executed_replicas`, and `tier_b_unlocked`
- `model_training_status`
- `md_campaign_incomplete_does_not_imply_model_training_incomplete`
- `claim_limit`

The MD cutoff does not assess model-training completeness. The two statuses are
independent and must remain separate in dashboard copy.
