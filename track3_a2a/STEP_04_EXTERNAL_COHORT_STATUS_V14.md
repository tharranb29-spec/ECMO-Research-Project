# Step 4 status: independent counterexample-rich A2A cohort

## Current decision

Step 4 is active. The dashboard redesign and presentation editing are outside
this workstream and will resume after the scientific pipeline is complete.

The v1.4 protocol foundation, sample-size analysis, historical-independence
screen, label-free candidate intake, and the first two database-source evidence
screens are now implemented. No candidate has yet passed the complete evidence
and independence gate, so the external cohort is not assembled or frozen.

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

Evidence-only review retrieved all 26 cited PubMed records associated with the
42 GtoPdb candidates. Candidate-centered abstract triage left 4 high-priority
full-text checks, but manual paper-level review showed that each candidate's
human A2A evidence was binding/selectivity evidence while the functional assay
belonged to A1 or A3, or to a different compound. Therefore **0 GtoPdb
candidates are evidence-admitted**. Ten PMCID records were queried through both
Europe PMC and NCBI PMC EFetch; one machine-readable article body was available.
XML unavailability is recorded as a retrieval limitation, not a scientific
rejection.

The complete PubChem P29274 inventory was also acquired and screened:

- assays requested and retrieved: **1,661 / 1,661**;
- ChEMBL mirrors excluded: **1,568**;
- independent-source assays: **93**;
- direct single-target P29274 assays: **33**;
- functional-readout assays: **14**;
- assays with explicit agonist/antagonist direction: **11**;
- assays also linked to a qualifying primary DOI or PMID: **0**.

Most independent PubChem records were BindingDB patent deposits. Even where a
cAMP assay existed, patent-only provenance did not satisfy the frozen primary-
publication rule. Consequently **0 PubChem assays are evidence-admitted**.

Every source record must still pass the human A2A functional-evidence gate and
link to a primary publication. Action annotations, database curation, binding
assays, patents, and LLM summaries do not by themselves create labels.

## Next executable sequence

1. Register post-freeze primary-literature sources with explicit human A2A
   functional assays, prioritizing recent studies with extractable structures
   and both agonist and antagonist or inactive counterexamples.
2. Extract structures and evidence into the sealed evidence workspace; publish
   only label-free candidates and aggregate audit counts to the repository.
3. Apply exact-structure, generic-scaffold, source-date, target, assay, and
   prior-visibility gates before any record can enter the cohort.
4. Perform dual evidence review for candidate-linked human A2A functional
   direction; database annotations, binding, patents, and LLM summaries remain
   insufficient.
5. Quantify the remaining gap to 280 total and approximately 140 per class,
   then define a prospective blinded functional-assay campaign to fill it.
6. Freeze membership, labels, and file hashes only after the cohort meets the
   protocol or a prospective amendment is approved before unmasking.
7. Proceed to the frozen docking and feature pipeline in Step 5 only after that
   freeze.

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
- `build_gtopdb_evidence_packet_v14.py`: sealed evidence packet and label-free
  review queue builder
- `acquire_pubmed_evidence_v14.py`: primary-reference acquisition
- `triage_gtopdb_primary_evidence_v14.py`: candidate-centered abstract triage
- `acquire_pmc_fulltext_v14.py`: Europe PMC/NCBI machine-readable full-text
  acquisition with explicit availability accounting
- `acquire_pubchem_assay_inventory_v14.py`: complete P29274 assay inventory
- `screen_pubchem_assays_v14.py`: non-ChEMBL functional and provenance gate
- `outputs/v1.4/evidence_review/gtopdb_2026.2/`: label-free queues and aggregate
  GtoPdb evidence audits
- `outputs/v1.4/external_sources/pubchem/`: aggregate PubChem acquisition and
  screening audits

All activity rows, candidate-level evidence proposals, abstracts, and full text
remain outside the repository in the sealed evidence workspace.
