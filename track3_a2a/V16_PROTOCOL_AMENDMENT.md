# Track 3 protocol amendment v1.6

**Frozen:** 2026-09-14, before any external `pBind_Ki` outcome join and before any Tier A or Tier B trajectory.

## Purpose

Version 1.6 converts the completed v1.5 development and preflight work into a deadline-specific, open, reproducible execution protocol. Versions v1.2 through v1.5 remain immutable historical artifacts. This amendment does not reinterpret their outcomes.

## Frozen decisions

1. The primary applied endpoint is direct wild-type human A2A `pBind_Ki`. Functional inhibition is exploratory. Agonism is reported as not modelable at the current endpoint-specific sample size.
2. `AB_Ridge` with alpha 1.0 is the primary external predictor because it was the strongest frozen v1.5 development model before external outcomes. Random Forest is a comparator, not a required winner.
3. Both RF comparators use exactly 500 trees, `max_features=sqrt`, `min_samples_leaf=1`, random seed 20260914, and one job. Alternative RF settings are sensitivity analyses and cannot replace the frozen models after unmasking.
4. External admission requires agreement between two independent computational passes. Missing evidence, ambiguity, or disagreement causes quarantine. No human validation is claimed or required.
5. The external outcome firewall remains sealed through cohort membership, structure standardization, applicability-threshold derivation, prediction generation, and artifact hashing.
6. The inaccessible CGenFF route is archived. Prospective MD uses AmberTools 25, OpenMM 8.6, ff19SB, Lipid21, GAFF2 with AM1-BCC charges, TIP3P water, and 0.15 M NaCl.
7. The 5G53 B/D control is prospectively defined as nucleotide-free mini-Gs. GDP is absent from the selected deposited B/D assembly, and the rejected cross-copy transfer produced a 0.9768 A severe clash. GDP will not be transplanted or minimized into place.
8. The deadline pilot is three 50 ns replicas for each Tier A control. Both controls must pass in at least two of three replicas before Tier B unlocks. Tier B pilot sampling is three 20 ns replicas per system. These pilot trajectories demonstrate short-timescale stability and gating; they are not convergence claims.
9. The dashboard operates in autonomous shadow mode. It records evidence, validation, model, docking, MD, and release events but cannot invent measurements, bypass quarantine, unmask outcomes, or promote a model without the declared gates.

## Claim boundary

The competition claim is an auditable evidence-to-screening system. Docking and MD are separate structural evidence channels. Neither is described as experimental validation, and neither can rescue a failed independent potency-model gate. The dashboard must display the model that survives external confirmation even if that model is ridge regression.

## Execution order

1. Generate and verify the computational freeze manifest.
2. Reproduce all three frozen development models on identical splits.
3. Run the two-pass, label-blind external evidence gate and freeze cohort membership.
4. Build and audit six GAFF2 ligand bundles and two Tier A constructs.
5. Freeze contacts, build membranes, and pass local minimization/NVT/NPT smoke tests.
6. Run Tier A on GPU; keep Tier B locked unless both controls pass.
7. Perform the one-time external outcome join only after predictions and hashes are frozen.
8. Integrate versioned outputs into the Track 3 dashboard and demonstrate one complete autonomous shadow-mode path.

The machine-readable authority for these decisions is `config/protocol.v1.6.json`. Any change requires a new version and must occur before the affected outcome is inspected.
