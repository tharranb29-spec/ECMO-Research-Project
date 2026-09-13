# External pBind Ki status v1.5

Status date: 2026-09-13

## Current decision

The independent BindingDB P29274 intake has started, but the external cohort is
not frozen and no potency outcome has been unmasked. The raw response and the
candidate-linked Ki values remain outside the repository in the sealed-label
workspace.

The first API download attempt was incomplete and was quarantined. The complete
official response was then acquired and parsed successfully. It contains 12,184
P29274 affinity records, including 8,516 Ki records. A deterministic firewall
retained 6,865 exact-relation Ki records for structure-only screening; numerical
Ki values were never written to the public workspace or used in screening.

## Label-blind structure screen

After parent standardization and deduplication:

- 5,742 unique standardized structures were observed;
- 2 structures could not be parsed and remain quarantined;
- 753 structures overlapped an exact structure previously visible to the
  project;
- 1,454 structures overlapped a generic Murcko scaffold used in model
  selection;
- 1,002 structures lacked a PMID or a non-BindingDB primary-publication DOI;
- 2,968 structures across 834 generic scaffolds remain eligible for primary-
  evidence review.

The 60-molecule and 20-scaffold planning floors are therefore feasible before
primary review, but they have not yet been met by admitted evidence. Counts at
this stage are discovery-pool counts, not cohort counts.

BindingDB's `10.7270/...` identifiers are repository-entry DOIs rather than
primary-publication identifiers. They do not satisfy the v1.5 publication gate.
Patent-derived or database-only measurements remain excluded unless a candidate
is independently linked to an admissible primary paper.

## Required next work

1. Build a label-blind, scaffold-diverse review queue from the 2,968 candidates.
2. Retrieve each linked primary paper and confirm human wild-type A2A, direct
   binding Ki, exact relation, units, assay context, molecule identity, and
   extractable stereochemistry.
3. Require two independent reviewers and adjudicate every disagreement.
4. Freeze the final membership, structure hashes, source documents, precision
   analysis, model artifact, applicability thresholds, and evaluation code.
5. Only then perform the one-time join to the sealed Ki outcomes.

No candidate may be selected by potency magnitude, and no MD or docking result
may create or repair an external Ki label.
