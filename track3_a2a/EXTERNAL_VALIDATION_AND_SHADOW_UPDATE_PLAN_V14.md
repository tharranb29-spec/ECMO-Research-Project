# Track 3 external validation and shadow-update plan, version 1.4

## Decision carried forward

The v1.3.1 locked-holdout gate did not pass. The positive `d_pk` direction is
hypothesis-generating, and chemistry plus docking did not improve AUC over
chemistry alone. The 40-record holdout and its reports are immutable historical
artifacts. They are not rerun, tuned, or relabeled as external validation.

No Track 3 model is promoted for autonomous replacement. Version 1.4 begins in
shadow mode and produces candidate predictions, audit records, and promotion
recommendations without changing a served model.

## Two systems with separate authority

The autonomous workflow combines an LLM-assisted discovery layer with a
supervised A2A classifier. They have different jobs.

The LLM may find literature, extract candidate evidence passages, summarize
ambiguity, and propose molecules for screening. It cannot create functional
ground truth, remove a record from quarantine, change a frozen analysis, or
promote a model.

The classifier may score unlabeled molecules and write shadow predictions. It
cannot train on its own predictions. A new training label must come from a
qualifying external human A2A functional assay or a versioned project wet-lab
result.

## Workstream 1: external cohort design

1. Run a simulation-based power analysis before collecting or unmasking labels.
2. Set the final sample-size target from that analysis. Target at least 60
   minority-class records; below 40, restrict the result to descriptive use.
3. Prefer chemotypes that weaken the current chemistry-label confounding:
   adenosine-scaffold antagonists, non-adenosine agonists, same-scaffold
   functional switches, model-disagreement cases, and applicability-domain
   boundary cases.
4. Exclude exact structures and generic Murcko scaffolds already present in any
   v1.3 partition.
5. Store structures and labels in separate files. Do not expose labels to model
   fitting, feature changes, or analysis-code changes.

The machine-readable rules are in
`config/external_validation.v1.4.json`. Candidate structures use
`data/curated/external_candidates_v14_template.csv`; labels use the separate
`external_labels_v14_template.csv` file.

## Workstream 2: evidence gate

1. Ingest source records additively.
2. Standardize identifiers and structures, then check exact and scaffold
   overlap with the historical cohort.
3. Require explicit human A2A functional evidence with agonist or antagonist
   direction and a traceable primary publication.
4. Quarantine binding-only, partial-agonist, inverse-agonist, conflicting,
   ambiguous, wrong-context, or unresolved records.
5. Allow the LLM to suggest relevant passages only. Its confidence score never
   admits a label.
6. Keep label admission separate from model performance. AUC cannot repair or
   reject source evidence.

## Workstream 3: frozen docking and feature construction

1. Reuse `5NM4` and `2YDO` with the stored preparation and box definitions.
2. Verify the existing redocking and source checksums before a new production
   run.
3. Standardize ligand states before docking.
4. Run GNINA v1.3.3 at exhaustiveness 8 with production seeds 42, 43, and 44.
5. Retain one pose per seed and aggregate each receptor by the median of valid
   seeds.
6. Treat zero or missing scores as failed runs. Require two valid seeds per
   receptor.
7. Keep CNNscore at or below 0.3 as a visible soft flag. Report flag rates by
   receptor and eventual class; do not silently delete flagged molecules.
8. Preserve the failed 4EIY sensitivity. A new production campaign requires a
   new prospectively justified protocol.

## Workstream 4: model freeze and external evaluation

1. Archive the old v1.3.1 holdout result and train the v1.4 candidate artifacts
   only on the frozen 203-record historical cohort.
2. Fit the chemistry baseline `AB` and combined candidate `E` on identical
   records. Freeze preprocessing, features, estimators, and hashes.
3. Score the external cohort while its labels remain masked.
4. Freeze predictions and the analysis environment.
5. Unmask the external labels once.
6. Test the positive `d_pk` coefficient with the predeclared reduced-logistic
   parametric bootstrap.
7. Compare `AUC(E) - AUC(AB)` with a paired molecule bootstrap.
8. Report every mandatory metric and diagnostic, regardless of direction.
9. If separation or nonconvergence invalidates the primary coefficient, mark
   the endpoint unevaluable. Do not switch estimators after unmasking.

## Workstream 5: prospective discovery

1. Add literature-derived or LLM-proposed molecules to the prospective library
   with `functional_class=unknown`.
2. Sanitize structures and reject chemically invalid entries before docking.
3. Calculate chemistry features, applicability-domain distance, and dual-state
   docking features.
4. Score with the frozen shadow models.
5. Rank for experimental review using model probability, uncertainty,
   structural quality, novelty, and chemical diversity.
6. Label outputs `computationally prioritized`, never `validated hit`.
7. Select a diverse experimental panel rather than taking the top numerical
   ranks alone.

## Workstream 6: promotion and dashboard behavior

The dashboard displays the shadow mode, candidate version, cohort status,
quarantine count, external-gate result, and human-release status. A failed model
update still adds its records and reports to the library but does not change the
served model.

Promotion requires all external gates in `external_validation.v1.4.json` plus a
named human release approval. Cross-validation alone cannot promote the model.

## Immediate executable sequence

1. Run and freeze the implemented power-analysis module.
2. Audit the pre-freeze candidate pool and preserve it only as a retrospective
   stress-test option.
3. Screen every new label-free candidate snapshot through exact-structure,
   scaffold, source-date, and prior-visibility checks.
4. Implement separated label storage and an unmask-once guard.
5. Acquire the first genuinely independent source snapshot until the frozen
   sample-size and class-balance targets are met.
6. Run the evidence audit and publish a quarantine report.
7. Prepare and dock the eligible external structures.
8. Freeze model artifacts and predictions.
9. Perform the one-time external evaluation.
10. Add prospective scoring and the shadow update loop only after the science
    pipeline is complete; redesign the dashboard separately for Track 3.
