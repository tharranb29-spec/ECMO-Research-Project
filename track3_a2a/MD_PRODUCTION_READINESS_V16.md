# MD production and Tier B readiness v1.6

**Prepared:** 2026-09-17

**Trajectory execution in this workstream:** none

**Current gate:** all six v1.6.4 equilibration audits accepted; Tier A pilot production is authorized only after the six hash-matched external state files are staged; Tier B remains locked

## Scope and authority

`config/md_production.v1.6.json` is the prospective execution and analysis contract for the deadline pilot already authorized by `config/protocol.v1.6.json`: two Tier A controls, three fixed seeds, and 50 ns per replica. It preserves the v1.5 pose/contact gate, requires all three replicas to be reported, and prohibits favorable-replica selection. The 1 fs production timestep carries forward the validated v1.6.4 numerical ceiling rather than returning to the unvalidated v1.5 2 fs setting.

This readiness layer does not alter the signed v1.6 protocol freeze, the accepted release archives, or any historical v1.5 output. It adds downstream contracts that cite and revalidate those authorities. The pilot supports only short-timescale stability statements.

## Tier A start gate

`run_tier_a_production_v16.py` refuses to initialize OpenMM until all of the following are true:

1. `tier_a_equilibration/equilibration_gate_report.json` is a passed v1.6.4 aggregate gate with exactly six observed and six passed runs and no missing audits.
2. The exact system/seed set is the Cartesian product of both controls and seeds `20260914`, `20260915`, and `20260916`.
3. Every individual audit is full scale, passed, hash-matched by the aggregate report, and tied to the frozen v1.6.4 config.
4. Every individual audit cites the system and smoke-state hashes in the accepted deterministic release archive.
5. Every `equilibrated_state.xml` exists beside its audit and matches the state hash recorded by that audit.
6. The repository release archive, its external manifest, its embedded manifest, and all extracted members reconcile.

The aggregate gate from main commit `002b5be` passes all six audits and `tier_a_production_unlocked` is true. The large `equilibrated_state.xml` files remain external execution artifacts rather than repository fixtures. The readiness validator accepts the complete audit set, but the execution runner remains fail-closed until all six state files are staged beside their audits and match the recorded hashes. No placeholder state or production bundle is generated.

After staging the six accepted state files, a dry execution gate check is:

```bash
python track3_a2a/run_tier_a_production_v16.py \
  --system 5NM4_ZMA_native \
  --replica 1 \
  --equilibration-root /path/to/complete/tier_a_equilibration \
  --preflight-only
```

Remove `--preflight-only` only on the intended OpenMM 8.6 accelerator host. Runs checkpoint every 100 ps and resume only when the prior status metadata matches the exact config, system, seed, equilibrated state, audit, and aggregate gate. A technical failure is recorded and may not be silently replaced.

For Google Colab execution, use `notebooks/A2A_TIER_A_PRODUCTION_V16_COLAB.ipynb`. It verifies all six Drive-hosted state files before launch, runs one predefined system/replica per session, prints checkpoint progress, and resumes only the same frozen job.

## Tier A analysis and Tier B unlock

`analyze_tier_a_production_v16.py` requires all six completed 50 ns runs. For the final 80% of each trajectory it applies the predeclared v1.5 control criteria:

- median aligned ligand heavy-atom RMSD at most 3.0 A;
- median ligand center-of-mass displacement at most 5.0 A;
- at least half of frozen native contacts have at least 50% occupancy at 4.0 A;
- production state data are present and finite.

It emits `control_gate_report.json`. `tier_b_unlocked` is true only when both controls pass at least two of three replicas and all three replicas per control are present. It never loads candidate activity or functional labels.

```bash
python track3_a2a/analyze_tier_a_production_v16.py \
  --runs-root /path/to/tier_a_production \
  --output /path/to/tier_a_production/control_gate_report.json
```

## Label-blind Tier B readiness

`config/tier_b_build.v1.6.json` enumerates only the four frozen candidate IDs, ligand bundle codes, two receptor states, retained-pose authority, and required files. `preflight_tier_b_build_v16.py` verifies retained-pose and GAFF2 bundle hashes without reading activity outcomes.

```bash
python track3_a2a/preflight_tier_b_build_v16.py
```

The current report records the passed six-run equilibration gate, four missing 2YDO accepted-construct inputs, and a missing Tier A production control gate. It creates no bundle and launches no trajectory. Bundle construction remains unauthorized until all eight inputs pass and the later control gate passes.

`run_tier_b_production_v16.py` is a second fail-closed boundary for later use. It requires:

- the exact passed Tier A control report;
- one of the eight frozen label-blind system IDs;
- an independently created `a2a-tier-b-release-bundle-v1.6` manifest marked `accepted_for_tier_b_production` and signed with the exact control-report hash;
- all required bundle members with matching hashes.

No Tier B bundle is fabricated here. Until a real builder produces and audits those artifacts, even `--preflight-only` remains locked.

## Verification

Run the scoped tests with:

```bash
python -m unittest tests.test_a2a_md_production_readiness_v16
```

The tests assert incomplete-set rejection, acceptance of the real six-audit aggregate gate, deterministic release-archive verification, the 50 ns/three-replica contract, the complete 2-of-3 control rule, label blindness, missing 2YDO blocker propagation, and the Tier B launch guard.
