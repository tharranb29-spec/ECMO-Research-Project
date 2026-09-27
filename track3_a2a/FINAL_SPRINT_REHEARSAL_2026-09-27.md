# Track 3 release rehearsal — 27 September 2026

Status: **local QA passed; live Render rehearsal not yet evidenced**. This is a release-check record, not a new scientific protocol, model result, or submission approval.

## Scope and source boundaries

The current dashboard baseline is commit `0516b67`, which adds the production route for the redesigned theme. The user reports that this Render deployment works. This session could not independently reach the public Render URL or read its deployment metadata, so the live commit, capabilities, and screenshots remain unverified here.

The teammate analysis remains a separate, provisional PDF transcription. The UI shows the requested nested breakdown: 155 compounds / 58 scaffolds at the reported point-estimate tier, and 13 compounds / 4 scaffolds at the reported robust tier, within its 276 / 120 screen-eligible set. These are **not** the frozen governed queue and are not confirmed hits. The UI also explains that project R² 0.561 is grouped development evaluation on 78 assay rows (69 distinct molecules), whereas PDF R² 0.5685 concerns a separate 74-molecule strict Ki-only cohort. They are not directly comparable. The previously supplied PDF files were inaccessible to this session under macOS file permissions; this check confirms the maintained dashboard transcription and tests, not a new independent reproduction of those PDFs.

## Local end-to-end evidence

An isolated app-server run used the pinned project virtual environment and temporary discovery state/job directories under `/private/tmp`; it did not alter the frozen external cohort or production discovery state.

| Gate | Observed result |
| --- | --- |
| Capabilities | `rdkit=available`; `ab_ridge_scorer=development_only`; `external_outcomes=sealed`; `model_promotion=disabled`; `tier_b=locked`; `autonomy=shadow_only`. |
| Cached demo | Three cached PubMed metadata sources, three quarantined extractions, two explicitly simulated molecules, development-only scores without intervals, and zero screen-eligible records. |
| Audit | Eight events from contract resolution to promotion firewall; no served model or external outcome load. |
| Identity failure | Repeated caffeine structure marked duplicate; `not-a-smiles` marked invalid; neither entered the governed queue. |
| Live failure | With no DeepSeek key, explicit live mode failed with `cached fallback is disabled`; it did not present cached evidence as live. |
| Asset regression | A new test checks every local CSS/JS asset referenced by the Track 3 page against the app server's static-file map, existence, and no-store cache policy. This specifically guards against the theme-serving failure found after the redesign. |
| Repository | 253 tests passed; dashboard JavaScript syntax check and `git diff --check` passed. |

No live DeepSeek call, new docking run, MD production, external outcome join, or model promotion was performed.

## Live gate to complete before the 29 September rehearsal

1. In Render, record the deployed commit SHA and compare it with the intended GitHub revision. Open `/healthz`; its `git_commit` must match. Do not use a cached screenshot as deployment evidence.
2. After signing in normally, confirm the page loads `track3-dashboard-theme.css` without a 404. In Discovery Lab, confirm the capability badges report RDKit available and AB Ridge development-only; external outcomes must be sealed and promotion disabled.
3. Run **Deterministic cached demo** with the molecule box empty. Expect three labelled cached citations, two simulated inputs, an unordered queue count of 0, and a visible promotion firewall. Do not call the resulting point estimates validated predictions.
4. In Evidence inbox, search `BDB-50318250` and expand its source-grounded quarantine packet. Check source URL, XML hash, unresolved categorical fields, and frozen disposition. Do not call it admitted.
5. In Teammate analysis, verify the 155 / 58 and 13 / 4 nested tiers and the two-cohort R² note. Confirm provisional labeling remains visible and that 276 is not conflated with the governed zero-record queue.
6. Check Overview, Evidence inbox, Discovery Lab, and Teammate analysis at desktop and approximately 390 px width. Capture the five screenshots listed in `FINAL_SPRINT_QA_AND_DEMO_2026-09-26.md` with UTC capture time and deployed SHA; exclude credentials and sealed outcomes.

Only after those checks pass should the team perform the 29 September judge narration, then tag and submit on 30 September. If the public service or provider is unavailable, demonstrate the deterministic cached mode and label the offline capability honestly.

## Remaining limitations

- The public Render site timed out from this session; the live gate above is **not passed** by the local checks.
- macOS denied this session direct access to the original teammate PDFs, so PDF assertions are not newly source-reproduced here.
- The generic premium UI static audit reports legacy/heuristic findings across this repository and does not pass strict mode. It is not evidence of a clean accessibility audit; the submission-critical Track 3 behavior must be judged by the targeted tests and live review above.
