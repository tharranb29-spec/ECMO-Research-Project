# Version 1.5 implementation status

Status date: 2026-09-13

## Completed

- Frozen an official ChEMBL activity, assay, document, and target snapshot for
  the 203-molecule exploratory cohort.
- Applied the full v1.5 measurement gate and retained a row-level rejection
  reason for every quarantined measurement.
- Built separate `pBind_Ki`, `pFunc_agonism`, and `pFunc_inhibition` molecule
  summaries. No Ki/Kd or agonist/antagonist functional pooling is used.
- Ran the frozen development models with ten repeated five-fold grouped splits,
  fold-local preprocessing, complete metrics, applicability-domain flags, and
  high-disagreement sensitivity. The historical locked holdout contributed zero
  model-selection rows.
- Prepared four label-blind external-candidate ligand structures.
- Completed all 24 frozen GNINA runs: four candidates, two receptor states, and
  three seeds. All four candidates met the two-valid-seed requirement in both
  states; all 24 seeds were valid.
- Frozen eight retained Tier B MD poses using the predeclared median-nearest
  affinity rule. No candidate functional labels were loaded.
- Acquired and hashed the deposited `5G53` active-state native-control
  structure.
- Resolved the deposited `5G53` ASN C239 chirality caveat without editing
  coordinates by selecting unaffected biological assembly 2 (receptor B and
  mini-Gs D).
- Installed and audited OpenMM 8.6, the bundled CHARMM36m/CHARMM36 July 2024
  protein/lipid files, POPC, cholesterol, GDP, and CHARMM TIP3P templates.
- Prepared and audited label-blind CGenFF request files for NEC, ZMA, C5A,
  C7A, C9A, and PGD2. CGenFF-generated parameters are still pending.
- Frozen the Tier A construct policy and generated non-production builder
  inputs. The incomplete local `5NM4` source was detected and replaced with
  the complete official RCSB file before the builder input was regenerated.

## Strict exploratory activity results

| Endpoint | Development n | Scaffolds | AB Ridge R2 | AB RF R2 | E RF R2 | E minus AB R2, bootstrap median [95% interval] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pBind Ki | 78 | 68 | 0.561 | 0.453 | 0.434 | -0.020 [-0.033, -0.008] |
| Functional agonism | 19 | 18 | -0.455 | -0.220 | -0.211 | +0.009 [-0.012, +0.033] |
| Functional inhibition | 36 | 36 | 0.553 | 0.361 | 0.384 | +0.023 [+0.011, +0.039] |

These results are exploratory. The agonism and inhibition analyses contain
fewer than 40 development molecules. The apparent positive docking increment
for inhibition and negative increment for Ki require independent external
testing and cannot promote a model.

## External candidate docking result

| Candidate | 5NM4 median affinity | 5NM4 median CNNscore | 2YDO median affinity | 2YDO median CNNscore |
| --- | ---: | ---: | ---: | ---: |
| LIT25-MET-PGD2 | -7.1291 | 0.5859 | -7.0607 | 0.7386 |
| LIT25-RL-C5 | -9.6379 | 0.9373 | -10.0486 | 0.9171 |
| LIT25-RL-C7 | -9.9848 | 0.9685 | -9.4730 | 0.9553 |
| LIT25-RL-C9 | -9.5699 | 0.9700 | -8.8396 | 0.8326 |

GNINA values are computational scores, not measured affinities. They do not
establish functional class or experimental activity.

## Current MD gate

The MD system manifest contains both Tier A controls and all eight Tier B
candidate-state poses. Production trajectories have not started. The chirality
and local OpenMM/core-force-field gates are resolved. Four preparation classes
and one specific structural finding remain:

1. Rigid transfer of GDP from mini-Gs chain C to the selected D copy aligns
   the local backbone at 0.087 A RMSD but creates a 0.977 A heavy-atom contact
   between GDP O6 and Ala D366 CB. This is a failed clash gate and requires
   manual structural resolution; minimization must not be used to hide it.
2. The receptor back-mutations, missing internal loops, missing sidechains,
   termini, and the repaired GDP pose must be completed and visually audited.
3. CGenFF ligand parameters and penalty audits have not been generated.
4. POPC/cholesterol membrane systems have not been built or composition-
   audited.
5. Native contact lists cannot be enumerated and frozen until the final native
   structures are accepted.

The local machine exposes only OpenMM Reference and CPU platforms, so it is
suitable for preparation and smoke tests but not the planned 3 microsecond
campaign. The two Tier A controls require an accelerated compute environment.
Tier B remains locked until both controls pass in at least two of three
replicas.

## Confirmation boundary

No external potency cohort has been frozen or unmasked, no confirmatory potency
evaluation has occurred, and no model is eligible for promotion. The external
primary Ki cohort still requires at least 60 molecules and 20 independent
generic Murcko scaffolds plus the frozen precision analysis.
