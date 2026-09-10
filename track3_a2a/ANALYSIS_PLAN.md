# Frozen analysis plan, version 1.2

This plan is frozen before functional-label review, production docking, or model
results. The machine-readable specification is `config/analysis_spec.v1.2.json`.

## Scope and endpoint

- Target: human adenosine A2A receptor (`ADORA2A`, UniProt `P29274`, ChEMBL
  `CHEMBL251`).
- Primary endpoint: agonist versus antagonist among reviewed A2A ligands.
- Positive class: agonist.
- This is functional-classification, not biased agonism, experimental affinity
  prediction, molecular dynamics, or active-versus-decoy enrichment.
- Partial agonists, inverse agonists, ambiguous records, binding-only records,
  and unresolved records are excluded from the primary binary endpoint.

## Structural design

- Primary inactive receptor: PDB `5NM4`, co-crystallized with ZM241385.
- Primary active-like receptor: PDB `2YDO`, co-crystallized with adenosine.
- Mandatory inactive sensitivity receptor: PDB `4EIY`.

`4EIY` failed the original frozen top-pose redocking gate but sampled
crystal-like poses diagnostically. It is not discarded or substituted post hoc;
it remains a declared sensitivity analysis.

For each ligand, let:

- `x_inactive = median valid affinity(5NM4)`
- `x_active = median valid affinity(2YDO)`
- `m_affinity = (x_active + x_inactive) / 2`
- `d_affinity = x_active - x_inactive`
- `d_affinity_per_heavy_atom = d_affinity / heavy_atom_count`

Mean/difference coordinates contain the same information as the two raw state
scores but are full-rank. Do not include both raw scores and their exact
difference in the same linear model. CNN state features use an analogous
mean/difference parameterization.

More-negative `d_affinity` is a hypothesis for agonist association, not an
assumed decision rule. Pocket geometry and ligand-size effects are empirical
questions assessed by the declared diagnostics.

## Redocking gate

- GNINA image: `gnina/gnina:v1.3.3`.
- Exhaustiveness: 8.
- Validation seeds: 42, 43, 44, 45, 46.
- One retained pose per seed.
- Pass: at least 4/5 symmetry-aware heavy-atom RMSDs <=2 A and median RMSD
  <=2 A.
- Missing pose, invalid output, or zero empirical score is a failed run.
- Aggregate by median valid run; report mean, SD, valid count, and failure count.
- Best-of-seed aggregation is prohibited.

The primary gate passed: `5NM4` 4/5 with median RMSD 0.8885 A; `2YDO` 5/5
with median RMSD 0.0342 A. This validates pose recovery, not biological efficacy.

## Label tiers and admission

- Tier 1: direct human A2A functional assay with interpretable agonist or
  antagonist direction. Used in the primary analysis.
- Tier 2: unambiguous functional assignment in a primary source but incomplete
  machine-readable direct assay detail. Used only in a predeclared sensitivity
  analysis.
- Excluded: binding-only, partial agonist, inverse agonist, ambiguous,
  wrong-context, and unresolved records.

Two different reviewers must independently agree on class and evidence tier.
Disagreement requires a named adjudicator. Automated rules and LLM output may
prioritize review but cannot admit a training label.

The planned reviewed dataset is 220 accepted records: 65 agonists and 155
antagonists. Rejected records do not count toward this target.

## Dataset partitions

- `development`: reviewed records available to scaffold-grouped model fitting.
- `locked_holdout`: scaffold-separated records untouched by preprocessing,
  feature selection, thresholds, and hyperparameters.
- `prospective`: unlabeled molecules ranked only after model freeze.
- `quarantine`: unreviewed or insufficient evidence; never used for training.

Partitions are assigned after review. The manifest and locked holdout are hashed
before model comparison.

## Predeclared models

- Model A: ECFP4 fingerprint only.
- Model B: physicochemical descriptors only.
- Model AB: ECFP4 plus physicochemical descriptors.
- Model C: single-state `5NM4` GNINA/CNN features.
- Model D: dual-state orthogonal mean/difference GNINA/CNN features.
- Model E: Model AB plus Model D.

Primary estimator: regularized logistic regression in an `sklearn.Pipeline`.
Random Forest is a nonlinear sensitivity analysis. Scaling and feature selection
are fitted only inside training folds.

## Comparisons and evaluation

- Headline validation: scaffold-grouped splits.
- Primary endpoint: paired scaffold-split `AUC(E) - AUC(AB)`, testing whether
  docking features add information beyond chemistry.
- Secondary endpoint: paired scaffold-split `AUC(D) - AUC(C)`, testing whether
  two receptor states outperform one.
- Mechanistic coefficient: sign and confidence interval of `d_affinity` in the
  full-rank mean/difference model.
- Companion metrics: PR AUC, balanced accuracy, MCC, sensitivity, specificity,
  Brier score, and calibration.
- Confidence intervals: molecule-level bootstrap of out-of-fold predictions.
- Random stratified validation is reported only as an optimistic comparison.

The numeric model-admission tolerance is not set until reviewed class balance,
sample size, and scaffold distribution are known. It will be frozen before
model updates are evaluated.

## Autonomous update safety

Autonomous discovery remains in shadow quarantine. An LLM cannot admit labels,
retrain the served model, or publish a promotion. Every ingestion, review,
partition, training run, evaluation, and promotion is append-only and versioned.
