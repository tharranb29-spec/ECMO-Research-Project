# Track 3 A2A Project Context and Execution Framework

Status date: 2026-09-14  
Competition deadline: 2026-09-30  
Document role: canonical working context for the team and future project work

## Project title

**Evidence-Gated Dual-State Docking and Machine Learning for Functional Classification and Virtual Screening of A2A Adenosine Receptor Ligands**

## Executive position

The project is now a Track 3 virtual-screening study centered on the human A2A adenosine receptor, a class A GPCR. It is no longer primarily an ECMO-interface discovery project. The current scientific contribution is an auditable pipeline that combines evidence curation, chemistry-based machine learning, dual-state docking, applicability controls, bounded molecular-dynamics validation, and an autonomous dashboard layer.

The most important result so far is not that docking or a Random Forest outperformed a simpler chemistry baseline. They did not. The binary agonist-versus-antagonist dataset is strongly confounded by chemical class, particularly the presence of ribose. Chemistry-only models already classify it nearly perfectly, leaving little credible room for docking to improve AUC. The one-time locked holdout preserved the expected direction of the conformation-associated CNN signal but did not confirm it at the predeclared threshold. Continuous human A2A Ki is therefore the primary applied ranking target for the next stage.

The current repository result identifies ridge regression as the strongest development model for `pBind_Ki`. This does not remove the AI contribution. The system should use whichever predictive model survives external testing, even if it is ridge. Its intelligence lies in the closed-loop, evidence-gated architecture: autonomous literature discovery, structured extraction, molecular standardization, deterministic evidence admission, model selection, applicability assessment, docking and MD promotion gates, candidate prioritization, provenance, and reproducible updates.

No wet-lab result has been generated. Docking scores are not experimental affinities, predicted candidates are not hits, and MD cannot rescue a failed external potency model.

## 1. Why the project switched to Track 3

The early research direction focused on ECMO biointerface targets such as Siglec-9 and SIRPalpha. The competition track requires virtual screening of small-molecule drugs using ion-channel or GPCR drug targets. The project therefore pivoted to the human adenosine A2A receptor (`ADORA2A`, ChEMBL target `CHEMBL251`), which offers:

- a clinically and pharmacologically established GPCR target;
- inactive, agonist-bound active-like, and G-protein-coupled active structures;
- a tractable ligand literature containing agonists, antagonists, inverse agonists, and measured binding/function endpoints;
- a suitable test of whether receptor-state information adds value beyond two-dimensional chemistry;
- a natural foundation for an autonomous literature-to-screening dashboard.

The research question evolved from a narrow classification claim into two linked questions:

1. **Mechanistic question:** does the difference between docking features from inactive and active-like A2A receptor structures carry a reproducible conformation-associated signal?
2. **Applied question:** can an evidence-gated QSAR system rank A2A ligands by measured potency and use docking or MD as qualified supporting evidence, especially when the chemistry model is out of domain?

## 2. Scientific premise and claim boundary

The primary docking pair is:

- inactive state: PDB `5NM4`, co-crystallized with ZM241385;
- active-like state: PDB `2YDO`, agonist-bound but without a G protein.

The project summarizes each docking score `x` using an orthogonal mean/difference parameterization:

- `m = (x_active + x_inactive) / 2`, representing overall score magnitude;
- `d = x_active - x_inactive`, representing the state-dependent difference.

This transform contains the same information as the two raw state scores but avoids interpreting a redundant feature set containing both raw scores and their exact difference.

The permitted claim ladder is:

1. **Receptor-validation claim:** the prepared receptor can reproduce a cognate pose under the production settings.
2. **Retrospective association claim:** a score difference is associated with a known label or potency after declared controls.
3. **External predictive claim:** a frozen model performs on a new, disjoint, predeclared external cohort.
4. **Prospective prioritization claim:** the pipeline ranks unlabeled candidates with explicit uncertainty and applicability status.
5. **Biological validation claim:** requires experimental evidence and is outside the present project.

The project currently supports levels 1, 2, and a limited level 4 candidate-prioritization demonstration. Level 3 has not yet passed because the external potency cohort is not frozen or unmasked. Level 5 is not claimed.

## 3. Evidence-gated project framework

The project follows a staged gate architecture. A downstream layer cannot repair an upstream failure.

| Gate | Purpose | Pass condition | Current status |
| --- | --- | --- | --- |
| G0 - source lock | Preserve exact receptor, ligand, assay, and software sources | Versioned files, provenance, and hashes | Passed for current retrospective and docking sources |
| G1 - evidence admission | Admit only traceable human A2A measurements with coherent endpoint definitions | Deterministic rules pass; ambiguous records quarantined | Passed for v1.5 development; external intake pending |
| G2 - receptor redocking | Show the pocket can reproduce a known pose | At least 4/5 poses at RMSD <= 2.0 A and median <= 2.0 A | Passed for 5NM4 and 2YDO |
| G3 - production docking QC | Require valid runs and sufficient seed support in both states | At least two valid seeds per receptor; zero/missing outputs fail | Passed for 214 retrospective compounds and four prospective candidates |
| G4 - model development | Compare chemistry, docking, and combined models without leakage | Frozen splits, fold-local preprocessing, complete baselines | Completed; docking adds no useful binary or Ki lift |
| G5 - untouched confirmation | Test a frozen hypothesis once | Predeclared threshold on untouched data | Binary v1.3.1 gate failed; external Ki gate not run |
| G6 - applicability | Identify unsupported chemistry predictions | Frozen fingerprint and descriptor-distance thresholds | Implemented for development; must be frozen for external use |
| G7 - MD native controls | Validate the dynamic setup on known complexes | Both Tier A controls pass in at least 2/3 replicas | Blocked before production |
| G8 - candidate MD | Evaluate blinded candidate-state systems | Unlocked only if both Tier A controls pass | Locked |
| G9 - model promotion | Serve a model in the autonomous dashboard | External, calibration, provenance, applicability, and hash gates pass | Not allowed yet |

### Operating rule

Every new molecule enters a quarantine-first evidence ledger. Literature text, LLM output, database labels, docking scores, and predictions are treated as separate evidence types. No model score can create a training label. No label can enter a frozen cohort after outcomes or model performance are viewed. Every update receives a version identifier and immutable manifest.

## 4. Work completed after the Track 3 switch

### 4.1 Receptor selection, preparation, and redocking

The original inactive structure `4EIY` failed the strict production-equivalent redocking gate. It produced only 2/5 acceptable top-ranked poses and a median RMSD around 3.03 A. The failure was diagnosed as pose-ranking rather than sampling: crystal-like poses existed but were not consistently ranked first. Raising exhaustiveness would not have resolved that specific validation problem.

`5NM4`, which contains the same antagonist class and inactive-state context, replaced `4EIY` as the primary inactive structure. Final redocking results were:

- `5NM4`: 4/5 passing poses; median symmetry-aware heavy-atom RMSD `0.8885 A`;
- `2YDO`: 5/5 passing poses; median RMSD `0.0342 A`;
- `4EIY`: retained as a documented failed/sensitivity structure, not silently deleted.

The production box was defined from ligand heavy atoms, transferred consistently between aligned receptor frames, and audited so both states sampled the same orthosteric region. A transmembrane alignment found 230 common C-alpha atoms with approximately `1.7476 A` RMSD between `5NM4` and `2YDO`.

### 4.2 Full dual-state GNINA campaign

The retrospective campaign completed:

- 214 molecules;
- two receptor conformations;
- three independent seeds per state;
- 1,284/1,284 GNINA jobs completed;
- zero failed jobs, timeouts, zero-byte outputs, or logged execution errors.

The frozen production settings used GNINA with exhaustiveness 8, one retained pose, and CNN rescoring. Per-molecule values were aggregated by the median of three seeds. `minimizedAffinity` was interpreted as a negative energy-like GNINA score and `CNNaffinity` as a positive pK-like model output. Neither is a measured affinity.

CNNscore was retained as a pose-quality indicator. A threshold of `<= 0.3` was treated as a soft warning rather than a hard deletion because failure was class-asymmetric: 90/378 agonist-state runs were flagged (`23.81%`) compared with 22/906 antagonist-state runs (`2.43%`). Hard deletion would disproportionately remove the minority agonist class.

### 4.3 Dataset reconstruction and the 11 inverse agonists

The team reconstructed the previously missing list of 11 inverse agonists. Removing them from the 214 docked compounds reproduced the frozen 203-compound binary cohort exactly:

- 63 agonists;
- 140 antagonists;
- 163 development compounds;
- 40 locked-holdout compounds.

The 203 compounds contain 199 generic Murcko scaffolds: 196 singleton scaffolds, two pairs, and one triple. This explains why nominal scaffold cross-validation behaves similarly to random splitting and cannot be presented as strong evidence of scaffold-level generalization.

The ribose detector was independently checked and confirmed that 51/63 agonists contain ribose, compared with only 2/151 antagonists in the original 214 set. This makes the binary label closely aligned with a sugar-versus-no-sugar distinction.

### 4.4 Binary classification and confound analysis

On the original 171-compound provisional development set, the five principal model families produced:

| Model | Inputs | ROC AUC |
| --- | --- | ---: |
| A | ECFP4 chemistry | 0.9830 |
| B | physicochemical descriptors | 0.9522 |
| AB | ECFP4 + descriptors | 0.9840 |
| C | single-state 5NM4 docking | 0.9159 |
| D | dual-state docking | 0.9045 |
| E | chemistry + dual-state docking | 0.9864 |

The primary increment `AUC(E) - AUC(AB)` was approximately `+0.0022`, with a 95% interval from about `-0.0003` to `+0.0077`. It failed the predeclared minimum improvement of `0.02`. The dual-versus-single docking comparison `D - C` was approximately `-0.0114`. Random Forest sensitivity analysis reached the same conclusion: chemistry plus docking improved AUC by only about `+0.0010`, with an interval crossing zero.

The development mechanistic analysis identified a positive, robust association for the standardized CNNaffinity state-difference feature `d_pk`:

- coefficient `+1.089`;
- molecule-bootstrap 95% interval `[+0.368, +3.363]`;
- two-sided label-permutation `p < 0.0001`;
- positive sign in 171/171 leave-one-molecule-out fits.

This was an exploratory conformation-associated CNN signal, not evidence of improved prediction or receptor conformational selectivity. It was strongly entangled with pose quality: `corr(d_pk, d_cnnscore) = 0.7929`, and neither score was independently significant in a joint model.

The one-time v1.3.1 locked holdout preserved the hypothesized positive direction but did not confirm the effect:

- standardized `d_pk = +1.048`;
- one-sided permutation `p = 0.0819`, above `0.05`;
- force-field `d_affinity` was null (`p = 0.5192`);
- chemistry plus docking reduced rather than improved AUC: `0.9858` versus `0.9886`, delta `-0.00285`.

The defensible conclusion is that the development association was hypothesis-generating and did not replicate at the frozen significance threshold.

### 4.5 Residualized score analysis

Independent reproduction clarified an earlier discrepancy. Residualizing `d_cnnaffinity_pk` on four physicochemical descriptors gives AUC `0.5731` on the 214 set and `0.5619` on the 203 set. Adding ribose as a covariate accounts for the lower earlier estimate near `0.477`.

`d_cnnscore` behaves differently: after the four descriptor controls it retains AUC `0.6423` with `p = 0.002`, but falls to approximately `0.545` after adding ribose. This supports the conclusion that CNNaffinity and CNNscore are not interchangeable, while also showing that both are influenced by chemistry-class structure.

### 4.6 Reproduction and specification audit

The v1.3 reproduction package reproduced all 133 numerical fields exactly, with zero maximum absolute difference and matching report hashes. Later cross-team checks exposed several specification sensitivities:

- early continuous-activity counts and R2 values had been calculated before filtering to the frozen 203 cohort;
- pooled functional endpoints inflated apparent sample size and mixed incompatible biology;
- pFunc agonism and pFunc inhibition must remain separate;
- Ki and Kd must not be pooled for the primary binding target;
- Random Forest `max_features` and `min_samples_leaf` can change R2 by up to approximately `0.12` in these small datasets;
- a scaffold split is leak-free but not strong external-generalization evidence when nearly every scaffold is unique.

The current repository is the source of truth. Any alternative RF setting, endpoint count, or teammate result is sensitivity evidence until merged into a new versioned protocol and rerun with frozen splits.

### 4.7 Continuous activity v1.5

Version 1.5 added continuous potency without rewriting the completed binary history. It keeps endpoints biologically separate:

- primary: `pBind_Ki`, human A2A direct binding Ki;
- secondary: `pFunc_agonism`, agonist EC50 or explicit equivalent;
- secondary: `pFunc_inhibition`, antagonist IC50 in an agonist-stimulated assay;
- inverse agonism: separate exploratory endpoint.

The frozen ChEMBL snapshot contained 644 candidate activity rows. The deterministic measurement gate admitted 258 and quarantined 386 with row-level reasons. Molecule summaries contained 98 `pBind_Ki`, 25 agonism, and 44 inhibition records. The historical locked holdout contributed zero model-selection rows.

Current development-only results are:

| Endpoint | Development n | Scaffolds | Chemistry ridge R2 | Chemistry RF R2 | Chemistry+docking RF R2 | Paired docking delta R2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `pBind_Ki` | 78 | 68 | 0.561 | 0.453 | 0.434 | -0.020 `[-0.033, -0.008]` |
| `pFunc_agonism` | 19 | 18 | -0.455 | -0.220 | -0.211 | +0.009 `[-0.012, +0.033]` |
| `pFunc_inhibition` | 36 | 36 | 0.553 | 0.361 | 0.384 | +0.023 `[+0.011, +0.039]` |

Interpretation:

- `pBind_Ki` is the best-supported applied target, but the chemistry ridge currently outperforms the RF and docking-augmented RF.
- Functional agonism is not modelable at the present sample size.
- Functional inhibition is exploratory because `n = 36`, despite an apparent small docking increment.
- None of these development results can promote a model without independent external confirmation.

### 4.8 External pBind Ki intake

An independent BindingDB intake for UniProt `P29274` was acquired into a sealed-label workflow:

- 12,184 affinity records;
- 8,516 Ki records;
- 6,865 exact-relation Ki records retained for structure-only screening;
- 5,742 standardized unique structures;
- 2 unparseable structures quarantined;
- 753 exact-structure overlaps removed;
- 1,454 development-scaffold overlaps removed;
- 1,002 records without an admissible primary publication identifier removed;
- 2,968 label-blind candidates across 834 generic scaffolds remain eligible for evidence review;
- a deterministic queue contains 240 candidates on 240 distinct scaffolds.

The external cohort is not frozen, outcomes remain masked, and no confirmatory evaluation has occurred. The planning floors remain at least 60 molecules and 20 independent generic Murcko scaffolds. The current 240-record queue is a discovery pool, not admitted membership.

### 4.9 Prospective candidate docking

Four label-blind literature candidates were prepared and docked against both primary states with three seeds each. All 24 runs were valid, and eight candidate-state poses were frozen for the MD plan.

| Candidate | 5NM4 median affinity | 5NM4 CNNscore | 2YDO median affinity | 2YDO CNNscore |
| --- | ---: | ---: | ---: | ---: |
| LIT25-MET-PGD2 | -7.1291 | 0.5859 | -7.0607 | 0.7386 |
| LIT25-RL-C5 | -9.6379 | 0.9373 | -10.0486 | 0.9171 |
| LIT25-RL-C7 | -9.9848 | 0.9685 | -9.4730 | 0.9553 |
| LIT25-RL-C9 | -9.5699 | 0.9700 | -8.8396 | 0.8326 |

These are computational prioritization scores, not measured potency or proof of agonism/antagonism.

### 4.10 MD protocol and preflight

The v1.5 MD plan defines:

- Tier A: two native controls, `5NM4`-ZM241385 and `5G53`-NECA-mini-Gs;
- Tier B: four candidates against `5NM4` and `2YDO`, eight systems total;
- three replicas per system;
- original production target of 100 ns per replica;
- 30 Tier A plus Tier B trajectories and 3.0 microseconds total sampling.

Completed MD preparation work includes:

- acquisition and hashing of the deposited `5G53` structure;
- computational resolution of the ASN C239 chirality caveat by selecting unaffected biological assembly 2, receptor chain B and mini-Gs chain D, without editing deposited coordinates;
- OpenMM 8.6 and core receptor/membrane force-field audit;
- correction of an incomplete local `5NM4` source using the complete official RCSB file;
- preparation and charge audit of six ligand requests: NECA, ZM241385, C5A, C7A, C9A, and PGD2;
- creation of the full Tier A/B Colab notebook and campaign manifest;
- local CPU benchmark showing approximately `6.93 ns/day` for only a 21,308-atom water benchmark.

The local Mac is suitable for preparation, audit, and smoke tests, but not the full 3-microsecond production campaign. Even the optimistic small-system benchmark implies approximately 433 serial days for 3 microseconds before accounting for larger membrane-protein systems.

## 5. Hurdles, challenges, and what they taught us

### 5.1 The initial receptor failed its own gate

`4EIY` failed redocking. This delayed production but protected the project from building a full campaign on an invalid top-pose ranking protocol. The replacement with `5NM4` was evidence-driven and is a methodological strength.

### 5.2 The binary endpoint measures chemistry class more than subtle conformation

Most agonists are ribose-bearing analogues, while antagonists are largely non-ribose heterocycles. The classifier can solve much of the task from two-dimensional chemistry. This explains the very high chemistry AUC and why docking adds almost no predictive lift. The corrective action is not to tune the binary model harder; it is to prioritize continuous Ki and seek counterexample-rich chemistry.

### 5.3 Scaffold cross-validation was less informative than expected

With 199 generic scaffolds among 203 molecules, almost every compound is a scaffold singleton. Scaffold grouping prevents exact leakage, but it does not create a meaningful series-held-out challenge. A truly external, structurally disjoint potency cohort is therefore mandatory.

### 5.4 The development mechanistic signal did not confirm

The `d_pk` direction remained positive in the locked holdout, but `p = 0.0819`. The correct response is to preserve the negative gate, state the signal as hypothesis-generating, and avoid repeated tuning on the holdout.

### 5.5 Docking did not improve the primary potency model

For development `pBind_Ki`, adding docking reduced R2 by approximately 0.020 relative to the chemistry RF. This means docking should not be marketed as a universal accuracy booster. It remains valuable for structural interpretation, state comparison, candidate pose generation, and a separate evidence channel for out-of-domain compounds.

### 5.6 Functional datasets became too small after biologically correct splitting

Pooling agonism and inhibition produced larger but incoherent targets. Once split correctly, agonism had only 19 development molecules and was not modelable. Inhibition had 36 and remains exploratory. The solution is additional evidence, not a more elaborate model.

### 5.7 RF hyperparameters materially changed small-sample results

Cross-team reruns found that `max_features` and `min_samples_leaf` can shift R2 by up to about 0.12. The repository v1.5 configuration and a teammate-proposed `500/sqrt/1` configuration are not interchangeable. A v1.6 model manifest must freeze one setting before any external outcome is unmasked. Ridge must remain a required baseline and may be selected as the production model if it wins externally.

### 5.8 Missing inverse-agonist identities blocked exact reproduction

The 203 set could not initially be reconstructed from the 214 file because the 11 inverse agonists were not enumerated. That list has now been recovered and the 63/140 split reproduced exactly. Future exclusions must always be stored as explicit ID manifests.

### 5.9 CGenFF access requires an unavailable institutional account

The v1.5 CHARMM/CGenFF route cannot currently generate the six ligand parameter streams because the service requires institutional credentials. Frozen CGenFF 4.6 requests are complete, but request files are not production parameters. The recommended response is a prospective v1.6 force-field amendment before any trajectory is run:

- Amber `ff19SB` for protein;
- Lipid21 for membrane;
- GAFF2 with AM1-BCC charges for ligands;
- compatible TIP3P water and ions;
- AmberTools 25 and OpenMM 8.6.

The v1.5 plan must remain archived. Mixing CHARMM receptor/lipid terms with ad hoc GAFF ligand terms inside the same frozen protocol is not acceptable.

### 5.10 The deposited active control contains a GDP clash after rigid transfer

Aligning GDP from mini-Gs chain C to the selected chain D gives a local backbone RMSD of `0.087 A` but creates a severe `0.9768 A` contact between GDP O6 and Ala D366 CB. Minimization must not be used to hide this. A v1.6 computational decision must be frozen before building systems: either retain and parameterize GDP with a jointly remodeled pocket, or justify a nucleotide-free mini-Gs construct and remove GDP consistently. The chosen option must pass chirality, chain-continuity, geometry, and clash audits.

### 5.11 Membrane systems and native-contact definitions are not yet frozen

Completed receptor constructs, ligand parameters, POPC/cholesterol membranes, protonation, net charge, contact definitions, and system hashes remain outstanding. Therefore no production trajectory has started and Tier B remains locked.

### 5.12 Compute and deadline constraints

The full 3.0-microsecond plan is not feasible on the local CPU by September 30. GPU execution is required. If GPU time is limited, a deadline-specific v1.6 pilot amendment must be written before results are viewed. A shorter pilot may support a stability-screen demonstration but must not be described as converged GPCR dynamics.

### 5.13 The dashboard narrative had drifted toward the old ECMO framing

The current dashboard needs a serious Track 3 redesign. The final UI should center A2A evidence, potency ranking, docking states, applicability, MD gates, candidate progression, and autonomous updates. Legacy ECMO-interface material should be isolated as historical work rather than mixed into the competition story.

## 6. Revised workflow to the September 30 deadline

The remaining work should run as four coordinated workstreams with a single evidence ledger and release manifest.

### Workstream A - protocol and governance freeze, September 14-15

1. Archive v1.5 exactly as executed.
2. Write a prospective v1.6 amendment before any new MD or external-confirmation outcome is inspected.
3. Freeze the primary endpoint as `pBind_Ki`; retain functional inhibition as exploratory and classify agonism as not modelable at current size.
4. Freeze required model candidates: ridge, RF, and chemistry-plus-docking RF. Do not assume RF must win.
5. Resolve the RF configuration discrepancy in the manifest. Use one declared setting for external evaluation and keep all other settings as sensitivities.
6. Replace mandatory human evidence review with two independent computational evidence passes if the team confirms this is the competition operating rule. Quarantine every disagreement. Do not silently reinterpret the existing v1.5 language.
7. Freeze success criteria, applicability thresholds, outcome firewall, code hashes, and model artifacts.

**Exit gate:** one signed/versioned machine-readable v1.6 manifest with no ambiguous endpoint, force-field, model, or review rule.

### Workstream B - independent external pBind Ki confirmation, September 14-22

1. Start from the existing label-blind 240-candidate/240-scaffold queue.
2. Retrieve linked primary publications and extract target species, wild-type status, assay type, Ki relation, units, molecule identity, stereochemistry, and source locator.
3. Run two independent computational audits: a deterministic metadata/structure pipeline and a separately prompted evidence-extraction pipeline. Agreement admits a candidate; disagreement or missing evidence quarantines it.
4. Maintain the sealed-outcome firewall. No numeric Ki value may influence membership, literature priority, or model selection.
5. Stop and report a stress-test cohort if fewer than 60 admissible molecules or 20 independent scaffolds remain. Do not weaken the floor after seeing outcomes.
6. Run the predeclared precision analysis, freeze membership and all hashes, then perform the one-time outcome join.
7. Evaluate ridge, RF, and docking-augmented RF on identical molecules using R2, RMSE, MAE, Spearman correlation, calibration, interval coverage, and applicability strata.
8. Promote no model unless the external R2 bootstrap lower bound is above zero and RMSE beats the training-mean baseline with a paired interval excluding zero.
9. Decide docking incremental value separately. MD cannot alter this decision.

**Exit gate:** immutable external report, prediction file, cohort manifest, provenance ledger, and promotion decision.

### Workstream C - open, reproducible MD v1.6, September 14-26

1. Build and audit the AmberTools/OpenMM environment: AmberTools 25, OpenMM 8.6, ff19SB, Lipid21, GAFF2, AM1-BCC, and compatible solvent/ion definitions.
2. Generate six ligand bundles for NECA, ZM241385, C5A, C7A, C9A, and PGD2. Each must contain the standardized structure, typed MOL2, `frcmod`, net charge, atom-name map, stereochemistry audit, parameter-generation log, and SHA-256 manifest.
3. Freeze the GDP choice. If retained, generate and audit a compatible GDP bundle and resolve the Ala366 clash through an explicit local-model search. If removed, document the structural justification and apply the construct consistently.
4. Complete receptor back-mutations, missing internal loops, sidechains, termini, protonation, and clash/geometry checks for the two Tier A controls.
5. Build both controls in the frozen membrane composition and audit orientation, lipid counts, water/ion composition, net charge, minimum distances, periodic box, and file hashes.
6. Enumerate and freeze native ligand contacts only from the accepted final structures.
7. Run minimization and short NVT/NPT smoke tests locally. Require stable energy, temperature, pressure, bond constraints, and no severe structural defects.
8. Run Tier A on GPU. The original target is three 100-ns replicas per control. If the deadline cannot support this, freeze a pilot amendment before running: recommended minimum is three 50-ns replicas per control, explicitly labeled a short-timescale control test.
9. Evaluate ligand RMSD, center-of-mass displacement, native-contact occupancy, receptor-state diagnostics, and replica agreement. Both controls must pass in at least two of three replicas.
10. Only after Tier A passes, build and launch all eight Tier B systems. For a deadline pilot, three 20-ns replicas per system can demonstrate the gated workflow but cannot establish convergence or long-timescale stability. Continue to 100 ns where compute permits.
11. Keep candidate identities/functional labels masked during setup and trajectory QC. Report every replica; never select only favorable runs.

**Exit gate:** either a passed Tier A report plus qualified Tier B pilot/full trajectories, or a transparent stopped-at-control result. A failed control is still a valid competition result if the gate is preserved.

### Workstream D - autonomous Track 3 dashboard, September 16-29

1. Redesign the information architecture around the A2A project rather than the original ECMO interface.
2. Implement the evidence inbox, molecule registry, model registry, docking/MD gate views, candidate portfolio, and immutable audit log.
3. Connect the dashboard to static, versioned repository outputs first. Do not build an opaque live agent before the underlying evidence contracts are stable.
4. Add the autonomous literature agent in shadow mode. It may search approved public sources, retrieve documents, extract candidate records, deduplicate structures, and queue evidence.
5. Add deterministic validators for target/species, assay type, units, stereochemistry, relation operators, structure identity, and source traceability.
6. Add model scoring with applicability status and uncertainty. Display the winning externally validated model, even if it is ridge.
7. Add docking as a separate structural-evidence panel and MD as a promotion-gated validation panel. Do not collapse all outputs into one unexplained score.
8. Record every autonomous action: source URL/identifier, excerpt locator, extraction version, validation outcome, model version, hashes, timestamp, and reason for quarantine or promotion.
9. Keep automated discoveries in a shadow library until they satisfy the same evidence gate as the frozen development data.
10. Test a complete demonstration path: discover one paper, extract one molecule, validate evidence, standardize the structure, score applicability and potency, optionally dock, and show the audit trail.

**Exit gate:** a deployable Track 3 dashboard demo with reproducible sample data, an autonomous shadow-mode ingestion loop, and no unsupported biological claim.

## 7. Deadline plan

| Date | Critical deliverable | Required decision/gate |
| --- | --- | --- |
| Sep 14 | Team alignment and this context brief | Approve primary endpoint, v1.6 amendment, dashboard scope |
| Sep 15 | Frozen v1.6 machine-readable protocol | Lock RF settings, computational review rule, MD stack, GDP policy |
| Sep 16-18 | Six GAFF2 ligand bundles and two completed Tier A constructs | All geometry, charge, parameter, and hash audits pass |
| Sep 18-20 | Membrane-built Tier A systems; external evidence queue processed | Freeze native contacts; maintain outcome firewall |
| Sep 20-23 | Tier A GPU trajectories; external cohort freeze if floors met | Tier B remains locked until both controls pass |
| Sep 23-26 | Tier B pilot/full execution and external one-time evaluation | Separate MD and model-promotion decisions |
| Sep 20-27 | Dashboard redesign and autonomous shadow-mode integration | Static evidence views before live automation |
| Sep 27-28 | End-to-end QA, reproduction run, report tables/figures | Zero broken hashes, missing provenance, or unqualified claims |
| Sep 29 | Submission rehearsal, demo recording, repository release candidate | Team signs off on scope and claim language |
| Sep 30 | Submission | Buffer reserved for packaging, not new science |

## 8. Autonomous dashboard framework

### 8.1 System layers

1. **Source registry and scheduler:** approved ChEMBL, BindingDB, PubMed/PMC, RCSB, and primary-publication sources; polling cadence and source versions.
2. **Retrieval agent:** finds new A2A literature and database changes, downloads permitted metadata/content, and records exact provenance.
3. **LLM extraction agent:** proposes structured molecule, assay, endpoint, value, and evidence fields with source locators. Its output is always provisional.
4. **Deterministic evidence gate:** validates species, target, wild-type status, endpoint, units, relation, document type, structure identity, and stereochemistry.
5. **Quarantine and adjudication engine:** compares independent computational passes and isolates disagreements without contaminating training data.
6. **Molecule registry:** standardized parent structure, salt/tautomer policy, canonical identifiers, scaffold, fingerprints, descriptors, provenance, and version history.
7. **Feature and applicability service:** creates model inputs, nearest-neighbor similarity, robust descriptor distance, and abstention/high-uncertainty flags.
8. **Model registry:** stores ridge, RF, and future model artifacts, training cohort hash, metrics, calibration, validation status, and promotion state.
9. **Docking service:** runs the frozen dual-state GNINA workflow, records seed-level QC, retains poses, and reports state-specific structural evidence.
10. **MD gate service:** exposes Tier A/Tier B status, system manifests, replica QC, contacts, and trajectory-derived diagnostics.
11. **Candidate portfolio:** ranks molecules using validated potency predictions, applicability, evidence quality, novelty, docking context, and MD status without pretending they are commensurate measurements.
12. **Audit ledger and release controller:** immutable event log, model-update comparison, rollback, and best-ever validated model rule.

### 8.2 Dashboard pages

- **Program overview:** current stage, passed/failed gates, claim status, deadline, and critical blockers.
- **Evidence inbox:** newly found papers/molecules, extraction details, computational-review agreement, and quarantine reasons.
- **Molecule registry:** searchable structures, endpoints, provenance, scaffold, and version history.
- **Model laboratory:** frozen splits, metrics, ridge-versus-RF comparison, calibration, applicability, and promotion decision.
- **Dual-state docking:** receptor validation, seed QC, 5NM4/2YDO scores, retained poses, and state-difference features.
- **MD validation:** Tier A controls, Tier B lock state, build/audit status, replica diagnostics, and contact maps.
- **Candidate portfolio:** evidence-gated shortlist with uncertainty and reason codes.
- **Audit and submission:** hashes, software versions, logs, downloadable reproduction package, and competition-ready figures/tables.

### 8.3 Autonomy boundaries

The autonomous system may:

- discover and retrieve public literature and database updates;
- extract structured evidence with exact source locators;
- standardize, deduplicate, calculate descriptors, and flag ambiguity;
- run authorized frozen scoring/docking workflows;
- compare a candidate model with the best validated model;
- quarantine, abstain, and generate auditable reports.

It may not:

- infer or fabricate missing experimental values;
- use a prediction or docking score as a training label;
- weaken a cohort floor after outcomes are known;
- unmask external outcomes before the cohort/model/code freeze;
- overwrite the 40-record historical holdout;
- promote a model that fails external gates;
- convert MD stability into measured affinity or biological efficacy;
- silently change the force field, endpoint, split, or model settings.

## 9. Why ridge can be the AI system's predictive kernel

The purpose of AI is not to maximize model complexity. A ridge model can be the correct deployed predictor when it generalizes better, is more stable at small sample size, and is easier to audit. The current `pBind_Ki` development result is ridge R2 `0.561` versus RF R2 `0.453`; the combined RF is lower at `0.434`. Choosing RF solely because it appears more sophisticated would be model shopping.

The competition value comes from the whole intelligent system:

- autonomous literature and molecule discovery;
- LLM-assisted evidence extraction;
- deterministic conflict detection and quarantine;
- versioned model comparison and promotion;
- applicability-aware abstention;
- dual-state structural interpretation;
- gated MD validation;
- provenance, auditability, and continual updates.

The model registry can later admit more complex methods if they beat ridge on a truly external frozen cohort. Complexity is earned by evidence rather than assumed to be valuable.

## 10. Roles and meeting decisions

Recommended workstream ownership can be assigned by role rather than individual name:

| Role | Responsibilities through Sep 30 |
| --- | --- |
| Scientific/protocol lead | Freeze v1.6, maintain claim boundary, approve final narrative |
| Data/evidence lead | External Ki evidence pipeline, outcome firewall, cohort manifest |
| Modeling lead | Freeze ridge/RF settings, run external evaluation, calibration/applicability |
| Structural lead | Receptor/ligand audit, docking integrity, MD Tier A/B gates |
| Platform lead | Dashboard architecture, autonomous shadow loop, deployment |
| Reproducibility lead | Hashes, environment locks, release package, end-to-end rerun |

The team should decide today:

1. Is `pBind_Ki` formally approved as the primary applied endpoint?
2. Will v1.6 use the open Amber/GAFF2 route and archive the inaccessible CGenFF route?
3. Will GDP be retained and parameterized/remodeled, or removed under a documented nucleotide-free construct?
4. What GPU budget is available, and is the deadline MD target full 100-ns replicas or a predeclared short pilot?
5. Which RF configuration will be frozen, with ridge retained as the required comparator?
6. Is the external evidence gate fully computational, and what two independent computational passes constitute agreement?
7. Who owns each workstream and the final release decision?

## 11. Risks and contingencies

| Risk | Severity | Trigger | Contingency |
| --- | --- | --- | --- |
| External cohort fails 60/20 floor | High | Too few evidence-admitted molecules/scaffolds | Report a labeled stress test only; no confirmatory claim |
| Tier A controls fail | High | Either control fails in 2/3 replicas | Stop Tier B and present gate-preserving negative result |
| GPU access insufficient | High | Projected run cannot finish by Sep 26 | Activate predeclared pilot amendment; do not claim convergence |
| GDP remains structurally invalid | High | Severe clash or parameter audit fails | Use documented nucleotide-free construct if prospectively approved |
| Model settings remain inconsistent | Medium | Teammate/repo manifests disagree | Freeze one v1.6 manifest and rerun all compared models identically |
| Dashboard scope expands too far | High | Core evidence flow incomplete by Sep 23 | Ship a vertical slice from literature to audited candidate; defer extras |
| Autonomous extraction hallucinates | High | Missing/contradictory source evidence | Quarantine by default; require independent computational agreement |
| Results are overclaimed | High | Docking/MD described as measured efficacy | Use fixed claim glossary and automated report checks |

## 12. Definition of done for the competition

The project is submission-ready when:

- the repository reproduces the frozen 203 cohort and all headline metrics;
- the 11 inverse agonist IDs and every other exclusion are explicit manifests;
- v1.6 endpoint, RF, evidence-review, MD force-field, GDP, and sampling rules are frozen;
- an external `pBind_Ki` report exists, or the project explicitly states that the confirmatory floor was not met;
- the best externally supported model is selected without preference for complexity;
- receptor redocking, full 214-compound docking, and four-candidate docking evidence are traceable;
- Tier A is completed or transparently reported as a blocking control result;
- Tier B is run only if unlocked;
- the Track 3 dashboard demonstrates autonomous shadow-mode literature ingestion and an auditable evidence-to-candidate path;
- all figures, tables, sample sizes, units, software versions, hashes, and limitations match the repository;
- the final presentation states that outputs are computationally prioritized candidates, not hits.

## 13. Meeting-ready summary

The team can present the project in one sentence as:

> We built an evidence-gated A2A virtual-screening system that tests whether receptor-state docking adds value beyond chemistry, preserves negative results when it does not, pivots to externally testable potency ranking, and is being integrated into an autonomous, provenance-first research dashboard.

The three central messages are:

1. **Rigor:** failed receptor, predictive, and holdout gates were preserved rather than hidden.
2. **Adaptation:** the project moved from a chemistry-confounded binary label to continuous Ki and from inaccessible CGenFF infrastructure to a prospectively versioned open parameterization route.
3. **System contribution:** the final product is not a single RF classifier; it is an autonomous evidence, screening, applicability, structural-validation, and audit platform that can use the simplest externally validated model.

## 14. Repository source-of-truth map

- `README.md` - Track 3 overview and frozen history.
- `STEP_04_STATUS.md` - provisional binary model development.
- `STEP_05_STATUS.md` - exploratory mechanistic analysis.
- `CONFIRMATORY_HOLDOUT_STATUS_V131.md` - immutable v1.3.1 holdout result.
- `CONTINUOUS_ACTIVITY_PROTOCOL_V15.md` - current continuous-endpoint rules.
- `V15_IMPLEMENTATION_STATUS.md` - consolidated v1.5 execution status.
- `EXTERNAL_PBIND_KI_STATUS_V15.md` - label-blind BindingDB intake.
- `MD_VALIDATION_PLAN_V15.md` - Tier A/Tier B/Tier C MD plan.
- `MD_GATE_STATUS_V15.md` - MD preflight decisions and blockers.
- `outputs/v1.5/implementation_status.json` - canonical machine-readable metrics and status.
- `outputs/v1.5/md/preflight_status.json` - canonical MD blocker manifest.
- `notebooks/A2A_FULL_TIER_A_B_COLAB.ipynb` - existing v1.5 Colab campaign notebook; must be amended for the v1.6 Amber route before production.

## Context-preservation note

This file is the durable context copy for future work. Update it only through a versioned change that also updates the relevant machine-readable status/configuration files. Do not overwrite historical v1.3, v1.3.1, v1.4, or v1.5 artifacts when implementing v1.6.

## 13. Execution update — September 14, 2026

Protocol v1.6 is prospectively frozen. Ridge is the primary external `pBind_Ki` predictor; the RF comparators use `500/sqrt/1`. A ten-repeat rerun on the repository's 78-molecule development subset reproduced Ridge R2 `0.561`, RF R2 `0.503`, and docking-augmented RF R2 `0.482`.

The open AmberTools route is operational on the Mac through the pinned `a2a-ambertools:v1.6` container. All six GAFF2/AM1-BCC ligand bundles have passed the computational bundle gate. The selected 5G53 B/D active control is prospectively nucleotide-free; cross-copy GDP transfer is prohibited. Tier A awaits completed constructs and membrane/smoke-test audits, and Tier B remains locked.

For independent external confirmation, all 141 PubMed records linked to the frozen 240-candidate queue were retrieved without loading outcomes. Eighteen of 29 PMC-linked full texts were obtained; unavailable full text is a retrieval limitation and not an evidence rejection. Cohort membership remains unfrozen pending the two-pass computational evidence gate.

The authoritative current status is `outputs/v1.6/implementation_status.json` and the human-readable summary is `V16_IMPLEMENTATION_STATUS.md`.

## 14. Execution update — September 15, 2026

External evidence pass 1 is complete for all 240 label-blind candidates. The deterministic preflight admits no records and loads no Ki outcome. It routes 187 candidates to an independently configured pass-2 source extractor, including 24 with available full text. Composite PMID/DOI locators are evaluated article by article. Membership remains unfrozen until pass 2 independently resolves molecule identity, stereochemistry, human wild-type A2A context, binding assay type, exact Ki endpoint, relation, units, and primary source locator and agrees with pass 1.

The static Tier A MD inputs have materially advanced. Both completed receptor constructs are available; the single 5NM4 modeled-side-chain clash was removed by restrained pre-membrane relaxation, while 5G53 remains the frozen nucleotide-free B/D mini-Gs construct. Native ZMA and NECA coordinates are mapped into their accepted GAFF2/AM1-BCC topologies with deposited heavy atoms fixed exactly and no severe protein clash.

Both unsolvated Tier A receptor–ligand compatibility bundles pass the pinned AmberTools 25.3 tleap build, finite-energy check, and native-pose geometry audit. The computational audit also resolved format-level ff19SB requirements by typing histidine tautomers from explicit hydrogens, naming four disulfide pairs per construct as CYX, and allowing tleap to generate correct hydrogens at the two 5G53 chain starts.

The audited Amber membrane route is now concrete: the accepted reusable patch contains 86 POPC and 38 Lipid21 CHL1 molecules, a 30.65% cholesterol fraction, symmetric leaflet edits, full template resolution, and no cross-residue non-water heavy-atom contact below 1 Å. This replaces the historical CHARMM prototype and satisfies the v1.6 single-force-field-family requirement.

### September 15 execution addendum — periodic and smoke gates passed

The relaxed Lipid21 patch, both full periodic Tier A systems, frozen native-contact lists, and minimization/NVT/membrane-NPT smoke audits are complete. The inactive control contains 81,447 particles and 75 contacts; the active nucleotide-free mini-Gs control contains 210,308 particles and 74 contacts. Both periodic assemblies and both smoke tests pass, with no candidate labels loaded and no production trajectory started.

Because the serialized active system is approximately 97 MB, raw regenerable XML/coordinate files remain local. Deterministic signed release archives of approximately 6.4 MB and 14.9 MB are the GitHub/Colab transport artifacts. The prospective staged-equilibration contract is now frozen at 2.14 ns per control/seed with the three existing seeds, staged heavy-atom restraint release, membrane-semi-isotropic NPT, checkpoints, and an all-six-runs aggregate gate. A scaled CPU execution preflight validates the runner but is explicitly ineligible to pass equilibration. The next execution is full-duration GPU equilibration; production remains locked until all six audits pass, and Tier B remains locked until both Tier A controls later pass their production rule.

The first full-duration CUDA attempt failed during the initial NVT stage with a particle-coordinate NaN before any 10 ps report or accepted checkpoint. This is retained as a computational QC failure, not omitted data. Hotfix contract v1.6.1 leaves the systems, total 2.14 ns duration, ensembles, seeds, contacts, and gates unchanged while introducing conservative 0.25–1 fs timesteps, an intermediate 1 kJ mol-1 nm-2 restraint-release stage, bounded re-minimization from the already smoke-minimized state, 2 ps finite-state monitoring, 50 ps resumable checkpoints, and explicit failure artifacts. No trajectory passed equilibration and all downstream locks remain in force.

A subsequent six-case CUDA matrix isolated the remaining failure. Base, restrained, and restrained-plus-disabled-barostat systems all passed in both mixed and double precision, and there were no duplicate constraints. The old restraint definition nevertheless raised initial energy by approximately `3.734e8 kJ/mol` because it anchored the periodically translated smoke state to the original PDB image. Version 1.6.2 corrects the restraint reference to each atom's accepted smoke-state position. This is an implementation-coordinate correction, not a change to the scientific experiment. No failed attempt is counted, and all production and Tier B locks remain active.
