# Track 3 release-candidate preflight

Date: 26 September 2026. This is an **offline preflight**, not a passed live Render rehearsal or a final submission tag.

## Frozen-claim audit

| Judge-facing statement | Frozen source | Checked value / permitted wording |
| --- | --- | --- |
| Development model comparison | `outputs/v1.6/model_reproduction/development_results.json` | AB_Ridge grouped out-of-fold R² = 0.5605378 (display 0.561); **78 assay rows**, not 78 unique molecules. Development only. |
| Shadow scoring artifact | `outputs/v1.6/model_reproduction/ab_ridge_shadow_scorer.json` | 78 training rows, **69 distinct molecule IDs**, alpha 1.0, pinned RDKit preprocessing. It supplies uncalibrated development-fit point estimates only; no validated interval, scientific rank, or promoted model. |
| External validation | `outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json` | 240 candidate records; 29 source-grounded but unresolved; **0 admitted molecules / 0 scaffolds** against 60 / 20 floors. Membership frozen; one-time outcome join prohibited. |
| Tier A / B | `outputs/v1.6/md/tier_a_production_cutoff/cutoff_status.json` | Tier A equilibration 6/6; production **1/6 observed, 0/6 complete, 5.92/300 ns** at the frozen cutoff. Tier B locked. These are historical cutoff numbers, not a live progress report. |
| Teammate charts | Team-supplied PDF transcription in `track3-dashboard.js` | Provisional aggregate reference only. Its 276 screen-eligible count is **not** this dashboard's governed 0-record queue and is not external confirmation. |

The UI copy was updated to distinguish the available shadow scorer from a **promoted/validated** model and to label the 78 development observations as assay rows. No numerical source artifact, model coefficient, frozen membership, or gate was changed.

## Reproducibility checks

- Full repository suite: `../ECMO-Research-Project/.venv-track3/bin/python -m unittest discover -s tests -q` → **251 tests passed**.
- Dashboard JavaScript syntax: bundled Node `--check track3-dashboard.js` → passed.
- `git diff --check` → passed before the release-candidate commit.
- Local browser rehearsal: see `FINAL_SPRINT_QA_AND_DEMO_2026-09-26.md`.

## Live Render gate: not yet passed

The public URL configured in `render.yaml` is `https://ecmo-research-dashboard.onrender.com/`. From this session, both browser attempts timed out and the health endpoint could not be DNS-resolved, including outside the filesystem sandbox. Therefore **deployment status, runtime commit SHA, RDKit installation, DeepSeek state, and live screenshots were not verified** here. Do not mark the Sep 29 rehearsal or Sep 30 submission complete on the basis of this offline check.

On a working connection, before tagging or submitting:

1. Manually deploy the release-candidate SHA on Render (or confirm that branch auto-deploy selected the exact SHA). Record the SHA from Render's deployment page and compare it to GitHub.
2. Open `/healthz`; confirm HTTP 200 and the reported revision matches the deployment. Sign in normally if the dashboard is protected; do not paste credentials into the submission record.
3. Open Discovery lab and check `/api/discovery/status` through the signed-in app: RDKit must be `available`, AB Ridge `development_only`, external outcomes `sealed`, model promotion `disabled`, Tier B `locked`.
4. Run the deterministic cached demo and confirm three cited metadata records, two simulated/standardized molecules, and **0** screen-eligible records. Check the audit trace and source links. If DeepSeek is configured, any live extraction must still be quarantined and source-bound; do not require a paid live call for the judge demo.
5. Search and expand `BDB-50318250` in Evidence inbox; verify the unresolved fields and frozen quarantine remain visible. Check 390 px mobile width for no horizontal clipping.
6. Capture the five live screenshots in `FINAL_SPRINT_QA_AND_DEMO_2026-09-26.md` with UTC time and deployed SHA. Then rehearse the five-minute narration and verify every number against the table above.
7. Only after the live gate passes, create the final submission tag and share the dashboard URL. If Render remains unavailable, use the deterministic local demo and explicitly label it local/offline.

No external outcomes were unsealed and no new docking or MD production is required for this release candidate.
