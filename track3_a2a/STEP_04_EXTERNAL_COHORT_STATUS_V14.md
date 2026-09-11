# Step 4 status: independent counterexample-rich A2A cohort

## Current decision

Step 4 is active. The dashboard redesign and presentation editing are outside
this workstream and will resume after the scientific pipeline is complete.

The v1.4 protocol foundation, sample-size analysis, historical-independence
screen, and label-free candidate intake are now implemented. The first source
snapshot has been screened. The external cohort itself is not yet assembled or
frozen.

## Frozen power target

The simulation result selects **280 total evidence-admitted molecules**, planned
as an approximately balanced cohort of **140 agonists and 140 antagonists**.
Under the planning standardized `d_pk` coefficient of 0.75, estimated one-sided
power is 0.841 (Wilson 95% interval 0.824 to 0.856). Sensitivity results are:

- standardized coefficient 0.50: 280 records gives 0.566 power; approximately
  600 records are required to exceed 0.80;
- standardized coefficient 0.75: 280 records gives 0.841 power;
- standardized coefficient 1.00: 280 records gives 0.945 power.

The planning effect is deliberately smaller than the accessed v1.3.1 holdout
estimate. The final primary test remains the predeclared reduced-model
parametric bootstrap, not the planning Wald approximation.

## Historical-pool audit

The September 4 review packet contains 938 records. Of the 734 not used in the
v1.3 partitions, 202 are disjoint from the v1.3 generic scaffolds and exact
structures. Nevertheless, all 734 were visible before the model and holdout
analysis. Therefore:

- definitive external-eligible from this pool: **0**;
- retrospective stress-test candidates: **202**;
- allowed claim for those 202: retrospective external-like sensitivity only.

This prevents a chemically disjoint but previously visible subset from being
misreported as independent validation.

## Independent source strategy

The first source is the IUPHAR/BPS Guide to PHARMACOLOGY 2026.2 snapshot. The
retrieved source contains 97 human A2A interaction rows for 96 unique ligands.
All 96 structures were retrieved successfully and screened without loading
functional labels:

- independence-eligible candidates: **42**;
- quarantined candidates: **54**;
- historical generic-scaffold overlaps: **40**;
- exact structures present anywhere in the pre-freeze source pool: **36**;
- duplicate standardized structures within the source snapshot: **4**.

Quarantine reasons overlap, so their counts do not sum to 54. Only one source
interaction has an explicit functional-assay description detectable by the
strict readout terms; therefore, GtoPdb is a discovery source and cannot be the
sole evidence source for the labels. It also cannot satisfy the 280-record power
target alone.

PubChem BioAssay records deposited by non-ChEMBL sources and future blinded
project functional assays are supplemental sources. ChEMBL-mirrored PubChem
records are excluded from the independent source branch.

Every source record must still pass the human A2A functional-evidence gate and
link to a primary publication. Action annotations, database curation, binding
assays, patents, and LLM summaries do not by themselves create labels.

## Next executable sequence

1. Perform evidence-only review of the 42 independence-eligible GtoPdb
   candidates and retain only explicit human A2A functional records.
2. Add non-ChEMBL PubChem functional assays and deduplicate across sources.
3. Publish exact-structure, scaffold, source-date, and prior-visibility
   quarantine counts for every supplemental snapshot.
4. Have an evidence-only review role construct the sealed label file; the model
   role must not read it.
5. Continue acquisition until the frozen 280-total and class-balance target is
   met, or prospectively amend the design before labels are unmasked.
6. Freeze candidate membership and hashes, then proceed to the frozen docking
   and feature pipeline in Step 5.

## Files

- `config/external_validation.v1.4.json`: endpoint and independence rules
- `config/external_power.v1.4.json`: frozen simulation assumptions
- `outputs/v1.4/external_power_analysis.json`: immutable power result
- `outputs/v1.4/prefreeze_pool_independence_audit.json`: historical-pool audit
- `config/external_sources.v1.4.json`: allowed and prohibited source roles
- `screen_external_candidates_v14.py`: label-free intake and quarantine gate
- `data/raw/external/gtopdb_2026.2/`: label-free GtoPdb structure snapshot and
  acquisition manifest
- `outputs/v1.4/external_cohort/gtopdb_2026.2/`: eligible and quarantined rows
  plus the screening audit
- `data/curated/external_candidates_v14_template.csv`: structure-side template
- `data/curated/external_labels_v14_template.csv`: separately controlled labels
