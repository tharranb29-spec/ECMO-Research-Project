# ECMO Seed Ranking Report

Input set: `data/seed_ligands.json`

This report comes from a small literature-seeded ranking prototype. It is useful for project design and prioritization discussions, not as a final discovery model.

## Model Notes

- `SIRPa`: leave-one-out MAE: 4.5 score points
- `Siglec-9`: leave-one-out MAE: 8.4 score points

## SIRPa

- `CD47 ectodomain WT`: 86.3 (advance)
  Reasoning: strong immunomodulation evidence, strong affinity evidence, surface-translation support.
  Evidence: Strong mechanistic and biomaterial evidence: immobilized CD47 reduces inflammatory cell attachment and neutrophil activation on polymeric blood-contacting surfaces.
- `Self peptide 21 aa`: 82.2 (advance)
  Reasoning: strong immunomodulation evidence, strong affinity evidence, surface-translation support.
  Evidence: Compact CD47-derived peptide with strong nanoparticle persistence and macrophage-avoidance evidence, making it attractive for engineered surfaces.
- `CD47 variant N3612`: 76.1 (secondary)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, surface-translation support.
  Evidence: Very high-affinity engineered CD47 variant with clear binding gains, but much less direct biomaterial-surface validation than WT CD47.
- `Self hairpin 10 aa`: 53.9 (hold)
  Reasoning: surface-translation support, strong affinity evidence, strong immunomodulation evidence.
  Evidence: Smaller derivative around the active loop that retains some activity but is clearly weaker than the full Self peptide.
- `Self-SS T107C`: 14.3 (reject)
  Reasoning: good hemocompatibility proxy, good conjugation feasibility, surface-translation support.
  Evidence: Negative control variant showing loss of SIRPa binding and loss of useful inhibitory signaling.
- `Scrambled Self peptide`: 11.1 (reject)
  Reasoning: good hemocompatibility proxy, good conjugation feasibility, surface-translation support.
  Evidence: Scrambled negative control demonstrating the need for sequence-specific SIRPa engagement.
## Siglec-9

- `pS9L`: 89.5 (advance)
  Reasoning: strong immunomodulation evidence, strong affinity evidence, good target specificity.
  Evidence: Potent multivalent Siglec-9 agonist with strong functional evidence for suppressing NETosis via SHP-1-dependent signaling.
- `MTTSNeu5Ac`: 67.0 (secondary)
  Reasoning: strong affinity evidence, good target specificity, strong immunomodulation evidence.
  Evidence: Best affinity among the monovalent Siglec-9 glycomimetics curated here, though still missing direct ECMO-surface validation.
- `BTCNeu5Ac`: 62.6 (hold)
  Reasoning: strong affinity evidence, good target specificity, strong immunomodulation evidence.
  Evidence: Synthetic Siglec-9 glycomimetic with clearly improved affinity over natural glycans and good receptor-binding evidence.
- `6-O-sulfo sLeX`: 52.4 (hold)
  Reasoning: strong affinity evidence, good target specificity, good conjugation feasibility.
  Evidence: Improved natural glycan ligand for Siglec-9 with better affinity than sLeX but still limited direct functional remodeling evidence.
- `pS9L-sol`: 46.6 (reject)
  Reasoning: strong affinity evidence, good target specificity, good hemocompatibility proxy.
  Evidence: Useful negative control showing that soluble presentation without cis-clustering is not sufficient for strong Siglec-9 agonism.
- `sLeX`: 43.2 (reject)
  Reasoning: good target specificity, good conjugation feasibility, strong affinity evidence.
  Evidence: Natural Siglec-9 ligand with weak-to-moderate affinity and limited direct functional ECMO-surface evidence.
- `pLac`: 16.7 (reject)
  Reasoning: good conjugation feasibility, good hemocompatibility proxy.
  Evidence: Deliberate non-binding negative control for the Siglec-9 glycopolypeptide system.

## Learned Weights

### SIRPa

- `bias`: -0.140
- `affinity_strength_score`: 0.255
- `specificity_score`: 0.133
- `functional_immunomodulation_score`: 0.230
- `surface_validation_score`: 0.218
- `conjugation_feasibility_score`: 0.085
- `hemocompatibility_proxy_score`: 0.129
- `multivalency_or_clustering_score`: 0.064
- `literature_confidence_score`: 0.032

### Siglec-9

- `bias`: -0.039
- `affinity_strength_score`: 0.266
- `specificity_score`: 0.150
- `functional_immunomodulation_score`: 0.268
- `surface_validation_score`: 0.139
- `conjugation_feasibility_score`: 0.098
- `hemocompatibility_proxy_score`: 0.087
- `multivalency_or_clustering_score`: 0.089
- `literature_confidence_score`: 0.035
