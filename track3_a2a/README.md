# Track 3 A2A virtual-screening study

This directory contains the evidence-gated Track 3 study. It is intentionally
isolated from the legacy ECMO/Siglec work so targets, labels, and validation
standards cannot be mixed accidentally.

## Scientific question

Does the difference between docking features from inactive and active-like
human A2A receptor structures add useful information for classifying known A2A
binders as agonists or antagonists?

This is an agonist-versus-antagonist classification study. It is not a biased
agonism study, and GNINA scores are not experimental affinity measurements.

## Current frozen protocol

- Primary inactive-state receptor: PDB `5NM4`.
- Primary active-like receptor: PDB `2YDO`.
- Mandatory inactive-state sensitivity structure: PDB `4EIY`.
- GNINA: `gnina/gnina:v1.3.3`.
- Seeds: `42, 43, 44, 45, 46`; exhaustiveness: `8`; one retained pose.
- Redocking pass: at least 4/5 symmetry-aware heavy-atom RMSDs at or below
  2.0 A and median RMSD at or below 2.0 A.
- Aggregation: median valid run; zero scores and missing poses are failures.

Protocol v1.1.1 is a documented implementation correction to v1.1: docking
boxes are calculated from ligand heavy atoms only, preventing explicit-H file
differences from changing the box. The acceptance rule and sampling settings
did not change.

The primary redocking gate passes:

- `5NM4`: 4/5 passing poses; median RMSD 0.8885 A.
- `2YDO`: 5/5 passing poses; median RMSD 0.0342 A.

This unlocks retrospective model development, not production screening.

## Evidence stages

1. `source_locked`: official receptor and co-crystal files plus checksums.
2. `redocking_gate`: cognate pose recovery under production sampling settings.
3. `retrospective_benchmark`: evidence-admitted functional labels, scaffold-grouped
   validation, and an untouched holdout.
4. `prospective_screen`: frozen model applied to an independent library.
5. `shadow_update`: automated discoveries remain quarantined until they pass the
   same versioned source-evidence rules.

## Computational curation amendment

Version 1.3 prospectively replaces mandatory dual-human review with a
machine-curated evidence audit. The frozen v1.2 protocol and results are kept as
historical artifacts. Machine decisions are never described as human-reviewed
or experimentally validated.

The audit admits labels only from explicit human A2A functional evidence linked
to a traceable primary publication. AUC, docking scores, LLM confidence, and
same-scaffold agreement cannot decide a label. Ambiguous or insufficient records
remain quarantined.

Run the current evidence and feature stage with:

```bash
.venv-track3/bin/python -m track3_a2a.run_computational_curation_v13
.venv-track3/bin/python -m track3_a2a.freeze_computational_partitions_v13
.venv-track3/bin/python -m track3_a2a.build_feature_matrix_v13
```

Current output: 204 evidence-admitted records and 16 quarantined or rejected.
The 203-record docking feature matrix contains 163 development records and 40
untouched holdout records; one admitted agonist has no valid docking result.
The holdout membership is preserved from v1.2 and has zero scaffold overlap
with development.

The one-time confirmatory gate was frozen and executed with:

```bash
.venv-track3/bin/python -m track3_a2a.freeze_confirmatory_v131
.venv-track3/bin/python -m track3_a2a.run_confirmatory_holdout_v131
```

The gate did not pass (`d_pk = +1.048`, one-sided permutation `p = 0.0819`).
Do not delete or overwrite the resulting holdout report to obtain another run.

## Version 1.4 external validation and shadow automation

Version 1.4 starts a new external-validation cycle without modifying or rerunning
the v1.3.1 holdout. The Track 3 dashboard remains in shadow mode: an LLM may
discover literature, extract candidate passages, and propose molecules, while
the supervised classifier may score unlabeled candidates. Neither may create
training labels or promote a served model.

The foundation is defined in:

- `config/external_validation.v1.4.json`
- `config/external_power.v1.4.json`
- `config/external_sources.v1.4.json`
- `config/shadow_update.v1.4.json`
- `EXTERNAL_VALIDATION_AND_SHADOW_UPDATE_PLAN_V14.md`
- `STEP_04_EXTERNAL_COHORT_STATUS_V14.md`

The frozen power analysis selects an approximately class-balanced external
cohort of 280 evidence-admitted molecules. The pre-freeze pool audit found 202
chemically disjoint retrospective stress-test candidates, but zero records that
can honestly be claimed as definitive external validation because that source
pool was already visible before v1.3 was evaluated.

No Track 3 autonomous model is currently promoted. Promotion requires a new,
independent external cohort, successful predeclared external gates, clean data
provenance, and named human release approval.

## Reproduce the current data stage

Create the isolated chemistry environment once:

```bash
python3 -m venv .venv-track3
.venv-track3/bin/pip install -r track3_a2a/requirements.txt
```

Build the cached ChEMBL functional snapshot, standardize structures, and create
the evidence-review queue:

```bash
python3 track3_a2a/ingest_chembl_functional.py
.venv-track3/bin/python track3_a2a/standardize_quarantine.py
.venv-track3/bin/python -m track3_a2a.build_evidence_review_queue
```

The current snapshot contains 1,591 standardized molecules. The strict readout
gate queues 938 candidates for evidence triage. A record remains
training-ineligible until it passes the versioned computational evidence gate,
receives a scaffold-safe partition, and has the required docking features.

## Important boundaries

- `assay_type=F` alone is not proof of functional evidence; some ChEMBL rows
  describe radioligand binding.
- Binding-only Ki/Kd evidence cannot establish agonism or antagonism.
- Prospective MW/QED filters do not decide retrospective benchmark eligibility.
- No LLM self-confidence, autonomous output, AUC result, or docking score may
  establish a functional label.
- Report computationally curated labels separately from experimental or human
  validation.
- Do not alter the 40 surviving locked-holdout records or use them for model
  selection.

See `ANALYSIS_PLAN.md` and `CURATION_GUIDE.md` for the frozen v1.2 history, and
`COMPUTATIONAL_CURATION_AMENDMENT_V13.md` for the active evidence-admission
rules.
