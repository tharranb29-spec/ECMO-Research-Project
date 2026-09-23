# Shadow evidence source-access sprint — September 23, 2026

This is a versioned operational worklist for the competition demonstration. It
reads the frozen v1.6 pass-1 and pass-2 categorical packets, without reading
external activity outcomes. It does not change the frozen cohort result.

## Deterministic selection

The builder groups metadata-pass records that pass 2 quarantined for unavailable
primary text by first PMID (DOI fallback). It sorts groups by the number of
affected candidates, then by source key, and checks the first 12 groups.
Publication metadata is retrieved from Europe PMC and retained in a separate
snapshot. The release records hashes of both frozen inputs and that snapshot.

## Observed result

- 240 candidate records checked for worklist classification.
- 211 have missing primary text; 29 have unresolved source or identity fields.
- 89 publication groups cover the metadata-pass records missing primary text.
- The first 12 groups affect 53 records. Europe PMC metadata verified all 12
  citations. None was flagged open access or as having supplementary material
  in the returned metadata.
- A title-level subtype screen flags 3 papers whose titles focus on A1 or A2B
  without mentioning A2A. This is a review prompt, not a paper-level verdict;
  the primary source must be checked before an A2A claim is made.
- The release also contains a 29-record source-grounded review packet. Every
  record lacks exact molecule identity and stereochemistry linkage in pass 2;
  29 lack units, 27 lack an explicit relation, and 25 lack wild-type status.
  Each packet row lists its PMCID links and the fields still needing evidence.

The 53 records are **still blocked**. Publication-level citation verification
does not identify which experimental table row belongs to a queued structure,
resolve assay conditions, or establish stereochemistry. A missing open-access
flag is not proof that no lawful source copy exists elsewhere.

## Next operational action

Review the 29 source-grounded but unresolved records first for exact compound
identifiers and endpoint context, then seek permitted primary text or author-held
supplements for the 12 checked papers. Record a source locator and exact
candidate-to-structure linkage before any shadow record advances to review.
Keep contradictions quarantined. The frozen v1.6 external-confirmation cohort
remains 0 admitted; its 60-molecule and 20-scaffold floors failed, and outcomes
remain sealed.
