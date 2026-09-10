# Step 4 status: provisional model development

## Scope

Step 4 used 171 provisional development molecules (50 agonists and 121
antagonists) from 167 generic Murcko scaffolds. The 43-molecule provisional
locked holdout was not loaded, scored, or used to choose model settings.

The evaluation used 10 repeats of five-fold stratified scaffold-grouped
cross-validation. Every reported development probability is the mean of ten
out-of-fold predictions. Confidence intervals use 2,000 paired molecule-level
bootstrap resamples.

## Development results

| Model | Inputs | ROC AUC |
| --- | --- | ---: |
| A | ECFP4 | 0.9830 |
| B | Physicochemical descriptors | 0.9522 |
| AB | ECFP4 + descriptors | 0.9840 |
| C | Single-state 5NM4 GNINA/CNN | 0.9159 |
| D | Dual-state orthogonal GNINA/CNN | 0.9045 |
| E | AB + dual-state GNINA/CNN | 0.9864 |

The primary difference, `AUC(E) - AUC(AB)`, was 0.0022 with a 95% bootstrap
interval of -0.0003 to 0.0077. This does not meet the predeclared minimum
improvement of 0.02.

The secondary difference, `AUC(D) - AUC(C)`, was -0.0114 with a 95% bootstrap
interval of -0.0403 to 0.0125. The dual-state docking representation did not
outperform the single-state representation.

The standardized `d_affinity` coefficient estimate was -0.157, with a
fold-distribution interval of -0.667 to 0.076. Because the interval crosses
zero, this run does not establish an independent conformational signal.

## Decision

The provisional development admission gate did not pass. Chemistry features
classify this dataset strongly, while GNINA adds only a small, statistically
uncertain increment. GNINA should therefore be described as an interpretable
secondary structural feature and prioritization aid, not as a demonstrated
source of improved agonist-versus-antagonist classification.

The near-identical random and scaffold-grouped results are not evidence of
external validity: 167 of 171 records have distinct generic scaffolds, so the
two split strategies are unusually similar for this dataset.

## Review and holdout gate

The project lead reports that two team members reviewed the analysis-ready and
docking-clean files. However, the record-level fields in
`chembl251_curation_plan_220_v1.2.csv` remain blank. Formal promotion requires
two distinct named reviewers to record a class decision and evidence tier for
each molecule, with adjudication for disagreements. The reviewed manifest must
then be hashed before a single locked-holdout evaluation.

Until that is complete, all Step 4 results must be labeled **provisional
computational development results**.

## Random Forest sensitivity

The predeclared nonlinear model-class sensitivity also failed to show useful
incremental docking value. Random Forest ROC AUC was 0.9853 for Model AB and
0.9864 for Model E. The paired `E - AB` difference was 0.0010 with a 95%
bootstrap interval of -0.0010 to 0.0042. The `D - C` difference was -0.0046
with a 95% interval of -0.0374 to 0.0267. This reinforces rather than rescues
the negative primary Step 4 result.
