# Google Colab MD runbook v1.5

Use Colab only after the repository preflight status is
`ready_for_tier_a_production` and a completed, hashed system bundle exists for
each native control. The runner intentionally refuses preliminary builder files.

## Runtime

1. Select a GPU runtime and verify that OpenMM reports `CUDA` or `OpenCL`.
2. Mount Google Drive for durable checkpoints and trajectory output.
3. Clone or update the exact Git commit containing the accepted bundle
   manifests and preflight status.
4. Install `openmm==8.6.0`; do not silently change the production engine or
   version between replicas.

## Tier A order

Run each system with replicas 1, 2, and 3 and the frozen seeds:

- `5NM4_ZMA_native`: 20260912, 20260913, 20260914
- `5G53_NECA_miniGs_native`: 20260912, 20260913, 20260914

Use `run_tier_a_openmm_v15.py`. It writes a checkpoint every 1 ns, records all
replicas, and resumes from an existing checkpoint. Keep each replica in a
separate Drive directory. Never choose a best replica or replace an unfavorable
run.

## Tier B lock

Do not adapt the Tier A runner to candidate systems. First complete the frozen
control analysis and commit a control-gate report showing that both controls
passed in at least two of three replicas. A separate Tier B launcher should then
verify that report and preserve the blinded candidate identifiers.
