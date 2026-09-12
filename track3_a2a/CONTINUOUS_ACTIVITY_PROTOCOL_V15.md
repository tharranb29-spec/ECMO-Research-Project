# Continuous A2A activity protocol, version 1.5

## Decision

Version 1.5 adds continuous potency modeling as a new Track 3 workstream. It
does not rewrite the completed agonist-versus-antagonist analysis. The v1.3.1
holdout result remains immutable and hypothesis-generating.

The current 214- and 203-molecule potency analyses have already been viewed.
They are therefore exploratory development evidence. A confirmatory claim
requires a newly frozen external potency cohort whose outcomes are withheld
until the model, applicability rules, predictions, and analysis hashes are
fixed.

## Separate prediction targets

The primary applied endpoint is `pBind_Ki`, defined as the negative base-10
logarithm of molar human A2A Ki. This endpoint directly serves the project's
high-affinity ranking objective.

Functional potency remains valuable but is split by pharmacology:

- `pFunc_agonism` uses agonist EC50 or an explicitly equivalent functional
  potency measurement;
- `pFunc_inhibition` uses antagonist IC50 in an agonist-stimulated assay;
- inverse agonism remains a separate exploratory endpoint because inhibition
  of basal activity is not equivalent to antagonism of a stimulated response.

Ki, Kd, IC50, EC50, and generic pChEMBL values are not pooled into one target.
Binding and functional measurements are also never pooled. These restrictions
prevent a larger but biologically incoherent training set.

## Measurement gate

Every admitted measurement must have an exact standardized parent structure,
human `ADORA2A` / `CHEMBL251` context, target confidence of at least 8, equality
relation, positive nM value, acceptable ChEMBL validity status, and a traceable
primary DOI or PMID. Reviews, patents, mutant-receptor assays, censored values,
and unresolved stereochemistry remain excluded from the primary endpoint.

The activity ledger retains the original measurement. Aggregation first takes
the median of exact replicates within an assay, then the median across eligible
assays for one molecule and one endpoint. Each molecule contributes one row and
one weight to the primary model. Inter-assay dispersion remains visible. An SD
above 0.75 log units triggers a declared sensitivity analysis rather than a
silent deletion.

## Modeling and evaluation

The primary QSAR model is a fixed Random Forest using ECFP4 plus the existing
physicochemical descriptor panel. A fixed ridge model provides a linear
reference. The docking-augmented model adds the six frozen mean/difference
GNINA and CNN features and is evaluated on the same molecules.

Development reporting uses ten repeated five-fold generic-Murcko-scaffold
splits. All preprocessing occurs inside each training fold. Every model uses
identical splits. Random splits are optimistic sensitivity analyses only.

Required metrics are R2, RMSE, MAE, Spearman correlation, regression calibration,
interval coverage, and performance inside and outside the applicability domain.
The report must include uncertainty intervals and endpoint-specific sample
sizes. A single scaffold-split estimate without its split manifest and
out-of-fold predictions is not sufficient for a frozen result.

## Applicability and docking

Applicability combines nearest-neighbor ECFP4 similarity with robust descriptor
distance. Thresholds are derived from the fixed development scaffold folds and
frozen before external outcomes are joined. Out-of-domain predictions carry an
abstention or high-uncertainty flag.

Docking is orthogonal supporting evidence, not an automatic fallback for an
out-of-domain QSAR result. It has its own applicability limits. Incremental
value requires paired external improvement in both R2 and RMSE over the
chemistry model on identical molecules.

## LLM and update boundary

An LLM may discover primary papers, identify candidate tables and passages,
normalize candidate molecule names, and flag ambiguity. It may not infer a
missing value, turn a model prediction into a label, admit a measurement, or
promote a model. Deterministic checks and named human approval remain required.

## Confirmation and promotion

The primary external cohort uses planning floors of 60 `pBind_Ki` molecules and
20 generic Murcko scaffolds, with no exact-structure or generic-scaffold overlap
with model-selection data. A simulation or precision analysis must set the
final size before outcomes are unmasked. The frozen QSAR model passes only if
the external R2 bootstrap lower bound exceeds zero and RMSE improves over the
training-mean baseline with a paired interval excluding zero.

Docking receives a separate incremental-value decision. MD cannot repair a
failed potency gate. Model promotion remains manual and occurs only after the
external, provenance, calibration, applicability, and hash checks pass.

The complete machine-readable specification is
`config/continuous_activity.v1.5.json`.

## Source definitions

- ChEMBL pChEMBL definition and validity rules:
  <https://github.com/chembl/GLaDOS-docs/blob/master/frequently-asked-questions/chembl-data-questions.md>
- ChEMBL activity, assay, and target curation reference:
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC4607714/>
