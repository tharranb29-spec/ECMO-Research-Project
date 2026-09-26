# Track 3 final-sprint checkpoint — 26 September 2026

## Completed in this milestone

- The source-grounded 29-record quarantine packet is searchable in the Evidence inbox. Each record exposes its source link, XML SHA-256, frozen quarantine reasons, and unresolved categorical fields. This is read-only triage, not admission.
- Render's build path now installs pinned RDKit 2025.09.6. Discovery Lab uses the same cleanup/parent/uncharging and descriptor definitions as the development chemistry pipeline, with canonical identity and generic Murcko scaffold.
- A transparent AB_Ridge(alpha=1.0) point-estimate artifact was fitted only to the frozen 78 `pBind_Ki` development rows (69 distinct molecule IDs). The model export and runtime verify source hashes. No external outcomes were loaded.
- The Discovery Lab presents this as a **development-only, uncalibrated** estimate. Applicability to a new molecule is not validated; interval, threshold provenance, admission, rank, promotion, and hit certification remain unavailable. Any artifact or dependency mismatch fails closed.

## Frozen scientific limits

The external evidence cohort still has zero admitted compounds and has failed its 60-molecule / 20-scaffold floors. The one-time external outcome join remains prohibited. The active dashboard model is not externally confirmed or promoted. The MD Tier B gate remains locked. The source-review UI does not silently revise those decisions.

## Remaining deadline sequence

1. **26–27 September:** deploy this commit to Render, confirm its build log installed the pinned RDKit, then verify `/api/discovery/status` reports `rdkit: available` and `ab_ridge_scorer: development_only`. Run one deterministic demo and verify queue count stays zero. If Blueprint build settings do not sync automatically, use Manual Sync before the deploy; the existing build script also installs RDKit when `RENDER=true` to support a specific-commit deploy.
2. **27–28 September:** end-to-end QA of evidence search/detail, source links, duplicate/invalid SMILES handling, DeepSeek failure behavior, model provenance, responsive layout, and the audit trail. Freeze a reproducible demo script and screenshots. Do not pursue new docking/MD production merely to fill the UI.
3. **29 September:** perform a submission rehearsal against the live dashboard. Present the independent external floor failure honestly; show the shadow autonomous literature/extraction loop and development-only scorer as a prototype, not a validated drug-discovery result. Check each numerical claim against its frozen source artifact.
4. **30 September:** submit the tagged repository and dashboard URL after a final smoke test. If Render or DeepSeek is unavailable, use the deterministic cached demo and explicitly say which capabilities are offline.

The next scientific expansion after the competition is a prospective, separately versioned evidence-intake amendment and independent validation. It must not be used to retroactively rescue the frozen failed cohort.
