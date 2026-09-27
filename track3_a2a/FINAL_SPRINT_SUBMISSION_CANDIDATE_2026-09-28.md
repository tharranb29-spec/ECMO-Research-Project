# Track 3 dashboard submission candidate — 28 September 2026

Status: **local release candidate verified; live deployment and signed-in rehearsal pending**. This document records what was actually checked, not a claim of scientific model promotion or final competition submission.

## Frozen claims and chart sources

- Primary AB_Ridge grouped out-of-fold development R² = 0.5605378 (display 0.561), 78 assay rows / 69 distinct molecules. RMSE and MAE share numeric zero-based axes; R² shows the negative mean baseline on a signed axis. No model is promoted.
- Evidence accounting shows 240 held, 29 source-grounded unresolved records *within* the held set, and 0 admitted externally. These are not additive bars. The external floor is 60 molecules / 20 scaffolds, so the outcome join remains prohibited.
- Teammate PDF aggregates stay separate and provisional: 276 / 120 screen-eligible, nested 155 / 58 point-estimate tier, and nested 13 / 4 robust tier. Their R² 0.5685 is from a different 74-molecule Ki-only cohort; it must not be compared as a direct improvement over 0.561.
- Historical Tier A: 6/6 equilibration, 1/6 production replicas observed, 0 complete, 5.92/300 ns at cutoff. Tier B remains locked. MD is not a review-queue, dashboard-operation, or release prerequisite.

## Local checks

- Render build steps `build_dashboard_bundle.py` and `build_track3_dashboard.py` completed without changing generated scientific contracts.
- Full project virtual-environment suite: **254 tests passed**. JavaScript syntax and `git diff --check` passed.
- Local app server: `/healthz` returned 200; Track 3 CSS/JS returned 200 with `no-store`; security headers included nosniff, same-origin framing/resource policy, restrictive CSP, and HSTS.
- Discovery capabilities: RDKit available; AB_Ridge development-only; external outcomes sealed; model promotion disabled; Tier B locked; autonomy shadow-only. Existing cached demo shows three cited metadata records, two simulated inputs, zero screen-eligible records, and no validated interval.
- Browser: all 12 route hashes displayed their matching panels with no document-level horizontal overflow at approximately 390 px. Five submission-critical routes also had no overflow at 1280 px. R²/RMSE chart toggles, source-quarantine copy, teammate 58/13/4 breakdown, and inline empty-query recovery were exercised. Browser error/warning log was empty.
- A direct-hash navigation mismatch and a phone-width evidence-chart overflow were found and fixed during this pass.

## Audit limitation

The broad premium static UI audit does **not** pass strict mode. It reports legacy-page controls and heuristic “actionless button” findings for JavaScript-bound controls; the Track 3 native-select ownership is explicitly documented in `DESIGN.md` but not represented in the audit manifest. The changed Track 3 routes were verified in the browser instead of treating that scan as proof of accessibility. This is not a full assistive-technology or cross-browser certification.

## Required live gate before submission

1. Deploy the new candidate commit to Render. `/healthz` must report that exact commit; the currently observed live service reported the earlier `0516b67` revision before this candidate was pushed.
2. Sign in normally and verify `/track3-dashboard.html` loads the theme, all charts, the evidence accounting note, and the Discovery capability badges without console or network errors. Do not put credentials in screenshots or the repository.
3. Run deterministic cached demo with no molecule input; verify three cached citations, two simulated molecules, zero admitted/eligible records, and the promotion firewall. Verify `BDB-50318250` remains quarantined and source-linked.
4. Check desktop and phone layouts on the deployed site; capture overview, evidence, discovery, teammate, and model screenshots with timestamp and deployed SHA. Verify the 0.561/0.5685 cohort note and the 155/58 → 13/4 nested tiers.
5. Only after the signed-in live gate passes, rehearse the judge story, create the submission tag, and submit the exact deployed SHA and dashboard URL. If a live provider is unavailable, use the deterministic cached demonstration and label it honestly.

No external outcomes were unsealed, and no candidate rank, per-molecule probability, hit claim, or automated model promotion was introduced by this UI release.
