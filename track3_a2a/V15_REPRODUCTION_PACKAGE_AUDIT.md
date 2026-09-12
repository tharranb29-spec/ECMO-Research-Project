# Audit of teammate v1.5 reproduction package

Audit date: 2026-09-12

## Decision

The package is useful exploratory evidence, but it is **not an implementation of
the frozen v1.5 protocol** and is not yet an end-to-end reproduction package.
Keep the frozen v1.5 protocol unchanged. Accept the verified set arithmetic,
ribose counts, adjusted-AUC reconciliation, and arithmetic of the supplied OOF
predictions as exploratory results. Do not use the package's RF results for a
v1.5 confirmatory or model-promotion claim.

## Checks that passed

- The 214-row manifest contains the exact 11 IDs in the frozen inverse-agonist
  exclusion manifest.
- Removing those IDs gives 203 molecules: 63 agonists, 140 antagonists, 163
  provisional-development records, and 40 provisional locked-holdout records.
- The ribose detector gives 51/63 agonists and 2/140 antagonists.
- Under the package's own broader endpoint definitions, the supplied molecule
  table contains 98 pBind and 96 pFunc values; 46 molecules have both, 148 have
  either, and 55 have neither.
- The adjusted AUC calculations rerun exactly from the matching 214-molecule
  docking input. For the 203 set, `d_cnnaffinity_pk` gives 0.5619 after the four
  physicochemical descriptors and 0.4757 after adding ribose. `d_cnnscore`
  gives 0.6423 and 0.5451, respectively.
- The supplied OOF table recalculates to the reported point estimates:

  | Target | FP R2 | RMSE | MAE | FP+M delta R2 | FP+D delta R2 | FP+M+D delta R2 |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | pBind | 0.4002 | 0.9955 | 0.7336 | +0.0049 | -0.0133 | +0.0115 |
  | pFunc | 0.4240 | 0.7661 | 0.6243 | -0.0045 | -0.0450 | -0.0391 |

- No scaffold in either supplied target-specific OOF table crosses CV folds.

## Corrections needed in the teammate package

### 1. The scaffold count in the README is wrong

The supplied `molecule_level_activity.xlsx` has **199**, not 201, distinct
generic Murcko scaffold values across 203 molecules. Three scaffold groups are
repeated: one group has three molecules and two groups have two molecules.
The target-specific counts are 97 scaffolds among 98 pBind molecules and 95
among 96 pFunc molecules.

The qualitative caveat still stands: these folds mostly separate singleton
scaffolds and do not establish broad chemotype generalization. The phrase
"statistically almost identical to random splitting" should remain an
interpretation unless a paired random-split sensitivity is actually reported.

### 2. The documented RF configuration conflicts with the executable code

- README section 4 says the main model uses 500 trees with all other Random
  Forest settings at defaults.
- README section 5 calls the chosen model `(500, sqrt, 1)`.
- `s3_model.py` sets only 500 trees and seed 42; therefore `max_features` is the
  installed scikit-learn default, not explicitly `sqrt`.
- `s5_grid.py` tests `sqrt` and `0.1`, but not the main script's default
  `max_features=1.0` in current scikit-learn.
- `s4b_perm.py` uses 150 trees, so its permutation reference does not test the
  exact 500-tree estimator used for the supplied headline OOF predictions.

The package must declare and use one explicit estimator configuration in model,
sensitivity, and permutation code.

### 3. The delivered files do not regenerate the supplied result set

The scripts require `/data/inputs/a2a_activity.xlsx` and
`/data/inputs/docking_clean.xlsx`, but neither input is included. The main model
also requires `molecule_target_v15.csv`, which is absent. The README lists
`s6_package.py` and `oof_predictions.json`, but neither is delivered.

More importantly, the included `s3_model.py` initializes an empty permutation
section and writes it unchanged. The delivered `model_results.json` contains
30-permutation summaries. Therefore that JSON was not produced solely by the
included version of `s3_model.py`; a missing or different packaging step is
required.

A local audit rerun used the supplied molecule-level workbook converted to the
missing CSV and the matching docking workbook (SHA-256
`7c4251aafec0e5dc1575e3b575742decc181a59008b6ba696593e2beeacb2cab`).
The AUC outputs reproduced exactly, but the RF outputs did not. In the available
environment (RDKit 2025.09.6, scikit-learn 1.7.2), the included main script gave
pBind R2 0.3510 and pFunc R2 0.3983. This does not prove the supplied predictions
are numerically wrong; it shows that the environment and executable provenance
are not locked tightly enough to reproduce them. The README names RDKit
2026.03.6 but supplies no complete environment lock or scikit-learn version.

### 4. Statistical wording needs tightening

- The 19-permutation result has a resolution floor of 0.05. It is a weak
  exploratory check, not strong evidence for a confirmatory claim.
- The permutation calculation must use the exact same estimator and full
  modeling pipeline as the observed model.
- The reported `p(>0)=0.006` for the pFunc FP+D delta is the proportion from a
  paired bootstrap of fixed OOF predictions. The percentile interval excludes
  zero, so "harmful in this exploratory OOF analysis" is supportable. Calling it
  a general or confirmatory effect is not.
- The adjusted-AUC bootstrap residualizes once on the full data and then
  resamples fixed residuals. Its intervals and p-values do not include
  uncertainty from fitting the residualization model. Treat them as descriptive
  unless residualization is refit within each bootstrap or evaluated by a
  prespecified cross-fitted method.

## Differences from the frozen v1.5 protocol

| Area | Teammate package | Frozen v1.5 requirement | Audit disposition |
| --- | --- | --- | --- |
| Primary binding target | Pools Ki and Kd | Ki only | Do not merge into v1.5 primary target |
| Functional target | Pools agonist EC50 and antagonist IC50 | Separate agonism and inhibition endpoints | Split before training |
| Admission gate | Equality relation plus two invalidity exclusions | Human A2A single protein, confidence >=8, exact positive nM, pChEMBL consistency, primary DOI/PMID, no review/patent/mutant, resolved structure | Rebuild from row-level raw activity data |
| Aggregation | One median over all eligible records | Within-assay duplicate median, then across-assay median within endpoint and mode | Rebuild provenance ledger |
| Historical holdout | Included in grouped CV (22 pBind and 18 pFunc rows) | Locked v1.3.1 holdout not reused for model selection | Exclude from v1.5 development selection |
| QSAR baseline | ECFP4 only | ECFP4 plus frozen physicochemical descriptors | Add descriptor block inside each fold |
| RF | 500 trees, seed 42, other values inconsistent | 1000 trees, sqrt, leaf 2, seed 20260912 | Use frozen settings |
| Development CV | One grouped 5-fold split | Ten repeated grouped 5-fold splits | Run all frozen repeats |
| Required metrics | R2, RMSE, MAE | Also Spearman, calibration intercept/slope, interval coverage, applicability-domain strata | Complete metric set |
| Docking increment | FP versus separate M/D subsets | AB versus AB plus all six frozen docking features on identical molecules | Run the predeclared E minus AB comparison |
| High disagreement | SD retained but no declared sensitivity | Flag SD >0.75 and report with/without sensitivity | Four pBind and four pFunc rows require the sensitivity |
| Confirmation | Current 203-set labels used | Newly frozen external cohort; one-time unmask | Exploratory only |

## Recommended integration workflow

1. Ask for the missing raw activity and docking inputs, the missing packaging
   script, all generated intermediates, and an environment lock containing
   exact Python, RDKit, scikit-learn, pandas, and NumPy versions.
2. Correct the scaffold statement to 199 for the supplied scaffold column and
   report the three repeated groups.
3. Preserve this package as an exploratory analysis snapshot; do not rename its
   pooled pBind/pFunc columns to the frozen v1.5 endpoints.
4. Reconstruct the row-level activity ledger under the frozen admission gate.
   Produce `pBind_Ki`, `pFunc_agonism`, and `pFunc_inhibition` separately.
5. Exclude the historical locked holdout from model selection, then run the
   frozen AB_RF, AB_Ridge, and E_RF pipeline with ten repeated grouped splits,
   complete metrics, high-disagreement sensitivity, and applicability-domain
   analysis.
6. Freeze the external cohort, labels, code, environment, splits, predictions,
   and hashes before the one-time confirmatory evaluation.
