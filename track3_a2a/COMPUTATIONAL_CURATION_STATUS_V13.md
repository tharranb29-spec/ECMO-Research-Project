# Track 3 computational curation status, version 1.3

## Completed

- Preserved all frozen v1.2 inputs, outputs, results, and dual-review rules.
- Added a prospective computational label-admission amendment.
- Audited all 220 planned records using cached ChEMBL assay and publication
  evidence.
- Admitted 204 Tier 1 labels: 64 agonists and 140 antagonists.
- Quarantined four records pending primary-source confirmation, rejected one
  wrong-context record, and quarantined 11 records with raw inverse-agonist
  evidence because inverse agonism is outside the binary endpoint.
- Preserved every surviving pre-existing scaffold assignment: 164 admitted
  development records and 40 locked-holdout records, with zero scaffold overlap.
- Rebuilt the feature matrix for 203 docked molecules: 163 development and 40
  locked holdout.
- Kept `CHEMBL3414942` admitted but training-ineligible because docking is not
  available.

## Scientific controls

- Human approval is not required under the v1.3 computational pathway.
- No human validation is claimed.
- Label admission does not use AUC, GNINA, CNNaffinity, LLM confidence, or
  same-scaffold agreement.
- The 40-record holdout remains excluded from training and model selection.
- CNNscore values at or below 0.3 remain soft flags; they do not silently remove
  minority-class records.

## Pose-quality finding

Across the 203-record feature matrix, 23.81% of agonist receptor-seed results
were CNNscore-flagged compared with 2.62% for antagonists. This class asymmetry
confirms that CNNscore cannot be treated as a neutral primary predictor or used
as an unreported deletion rule.

## Blocked records

- `CHEMBL186113`: primary source not established.
- `CHEMBL1095999`: primary source not established.
- `CHEMBL4064207`: primary source not established.
- `CHEMBL4065326`: primary source not established.
- `CHEMBL1258170`: target/organism context failed.
- Eleven records that triggered the conservative inverse-agonist quarantine are
  listed in `data/curated/chembl251_inverse_agonist_exclusions_v1.3.csv`:
  `CHEMBL113`, `CHEMBL113142`, `CHEMBL240624`, `CHEMBL273094`,
  `CHEMBL3904408`, `CHEMBL4125975`, `CHEMBL4126427`, `CHEMBL4127213`,
  `CHEMBL4159215`, `CHEMBL4167557`, and `CHEMBL431770`.
- Seven have candidate-linked primary functional inverse-agonist evidence. Four
  (`CHEMBL113`, `CHEMBL240624`, `CHEMBL273094`, and `CHEMBL431770`) are
  conservatively quarantined because ChEMBL uses inverse-agonist wording for a
  mutant-receptor SPR binding assay; they still require candidate-linked
  functional confirmation.
- Removing exactly these 11 historical antagonist labels reconstructs the
  203-record matrix: 63 agonists and 140 antagonists, with 163 development and
  40 locked-holdout records. The machine-checkable reconciliation is stored in
  `outputs/v1.3/inverse_agonist_exclusion_audit_v1.3.json`.

## Confirmatory gate completed

The development-only preprocessing and model settings were frozen under
`confirmatory_spec.v1.3.1.json`, then evaluated exactly once on the 40-record
locked holdout. The direction was positive, but the primary gate did not pass
(`p = 0.0819`; predeclared `alpha = 0.05`). Chemistry plus docking also did not
improve predictive AUC over chemistry alone. See
`CONFIRMATORY_HOLDOUT_STATUS_V131.md` for the locked interpretation.

The guarded commands were:

```bash
.venv-track3/bin/python -m track3_a2a.freeze_confirmatory_v131
.venv-track3/bin/python -m track3_a2a.run_confirmatory_holdout_v131
```

The second command refuses to run if any frozen input or implementation hash
changes, and refuses to overwrite an existing holdout report.
