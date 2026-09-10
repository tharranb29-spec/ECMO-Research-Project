# Independent audit of the shared repro v1.3 package

## Execution result

The shared script was executed unchanged except for replacing its two
container-only input paths and output path with paths inside an isolated `/tmp`
copy. The analytical code, seeds, models, and resampling counts were unchanged.

- Script SHA-256: `66ee6bc04c0135ad7a3214998ee9838d2fbb7c69c21247eb3833cc5b3f185689`
- Docking input SHA-256: `7c4251aafec0e5dc1575e3b575742decc181a59008b6ba696593e2beeacb2cab`
- OOF input SHA-256: `9f2715964c227e389f87b3fb2af7623e851ef71cbc4f41786176ab126c9884b2`
- Teammate output SHA-256: `caa6a08be6746177aa6b0ae4dcd0e3e8062781f0a5c5a1a22f79d7a9bf9f0592`
- Independent output SHA-256: `caa6a08be6746177aa6b0ae4dcd0e3e8062781f0a5c5a1a22f79d7a9bf9f0592`
- Numeric fields compared: 133
- Maximum absolute numeric difference: `0.0`

Execution environment: NumPy 2.5.2, pandas 3.0.5, scikit-learn 1.7.2,
openpyxl 3.1.5.

The package therefore reproduces the teammate's implementation exactly,
including `d_pk = +0.937361`, its bootstrap interval, all three reported
permutation values, LOO results, and Step 4 AUCs.

## Scope limitation

The package analyzes the historical 214-record matrix with 171 development and
43 holdout records. It does not analyze the current computational-audit cohort,
which contains 203 docked records after 11 inverse-agonist exclusions: 163
development and 40 locked holdout. The package is therefore a reproduction of
the earlier development analysis, not a replacement run for frozen v1.3.1.

## Specification discrepancies

1. The README says preprocessing is refitted inside each bootstrap resample,
   but the script constructs each design matrix once and resamples that fixed
   matrix.
2. The reported Freedman-Lane implementation uses OLS residuals and an OLS test
   statistic for a binary response. It is not a logistic-regression partial
   coefficient permutation test and should be labelled accordingly.
3. The joint-model `permute_d` branch compares logistic-regression permuted
   coefficients with an OLS observed coefficient. That branch is not a coherent
   test, although the package already advises against quoting it.
4. Permuting `d` preserves the outcome-control relationship but breaks the
   `d`-control relationship; it is not automatically a valid conditional null.
5. The script does not write `repro_v13_results_table.csv` or record the data
   hashes in its JSON, despite the README saying it does.
6. The Step 4 paired bootstrap p-value omits the documented `+1` correction and
   can report exactly zero.

## Locked interpretation

The exact match establishes computational reproducibility of the shared code.
It does not resolve which inferential procedure is scientifically preferred.
The already unblinded v1.3.1 primary result must not be replaced retroactively.
For a future external cohort, the team should preregister either a properly
specified binary-outcome conditional test or a reduced-logistic-model
parametric bootstrap before outcomes are accessed.
