# Track 3 competition scope amendment v1.6.1

Effective date: 2026-09-19

Competition cutoff: 2026-09-30

Status: prospectively frozen before any external outcome unsealing or review-queue release

## Purpose and boundary

This amendment narrows the September 30 competition claim. It does not revise the frozen scientific analysis. The `pBind_Ki` endpoint, feature definitions, estimator settings, model mappings, five-fold ten-repeat grouped evaluation, interval procedures, development evidence, and sealed external outcomes remain unchanged. No performance result observed after the v1.6 freeze may be used to tune those choices.

The competition contribution is an auditable evidence-orchestration and screening workflow. It is not a claim that the system can assign a defensible scientific order to individual candidates or estimate a calibrated hit probability for any candidate.

## Human review queue

The permitted output is an uncertainty-aware, scaffold-composed queue for human review. Scaffold composition, applicability status, evidence completeness, and model disagreement may define review bands or set composition. A row's location in the queue is an operational review aid, not a scientific rank.

The only permitted candidate status is **screen-eligible / not ruled out**. This means that the record passed the declared label-blind screening checks used to form the review set. It does not mean **certified hit**, validated ligand, active compound, predicted clinical candidate, or any equivalent claim.

Reporting is set-level only. Allowed rates describe process composition, such as the fraction inside the applicability domain, outside the domain, carrying high model disagreement, possessing complete required evidence, or represented by distinct scaffolds. Hit rate, success probability, certified-hit fraction, per-candidate probability, and per-position enrichment are prohibited while outcomes remain sealed and external confirmation has not passed.

No fixed queue count is authorized by this amendment. No interval-bound inclusion rule is authorized because the current audited artifacts do not establish an exact prospective bound for that purpose. A future fixed count or bound would require its own source artifact, derivation, prospective version, and pre-release hash.

## External-confirmation floor

The minimum of 60 molecules and 20 independent generic Murcko scaffolds belongs only to the outcome-bearing external confirmation cohort. An unlabeled discovery or human-review queue cannot satisfy, inherit, or be described as passing this floor regardless of its row or scaffold count.

The frozen v1.6 pass-2 attempt admitted zero molecules and zero scaffolds, failed both minimum floors, and did not authorize the one-time outcome join. That floor failure remains the external-confirmation result. Review-queue construction does not reopen it.

## Molecular-dynamics cutoff

All six staged-equilibration replicas passed and authorized Tier A pilot production. At this scope freeze, the repository contains no signed, complete Tier A production control-gate report covering all six 50 ns runs. Tier A must therefore be reported at the competition cutoff as ongoing or staged but incomplete unless that exact audited completion artifact exists by the cutoff. Partial trajectories, runtime progress, or a favorable subset cannot establish control stability.

Tier B remains locked and is not submission-critical. The competition submission does not depend on Tier B construction, execution, or candidate-level MD claims.

## Dashboard autonomy

The autonomous dashboard module is shadow-only evidence orchestration. It may discover public evidence, retain provenance, create quarantined proposals, compose uncertainty-aware scaffold sets for human review, report authorized set-level process rates, and display audited gates.

It may not validate science automatically, modify the protocol, tune or promote a model, unseal or join outcomes, admit a certified hit, or unlock either MD tier. Every autonomous record remains a shadow proposal until the corresponding external human or computational release authority acts outside the dashboard.

## Machine-readable authority

`config/competition_scope.v1.6.1.json` is the source authority. The deterministic governance builder emits the claim matrix, dashboard contract, status, and signed release manifest under `outputs/v1.6.1/governance/`. A failure to reconcile any frozen v1.6 model field, firewall flag, external floor result, or MD lock state blocks release.
