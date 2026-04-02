# ECMO Seed Ranking Report

Input set: `data/custom_candidate_template.csv`

This report comes from a small literature-seeded ranking prototype. It is useful for project design and prioritization discussions, not as a final discovery model.

## Model Notes

- `SIRPa`: leave-one-out MAE: 4.5 score points
- `Siglec-9`: leave-one-out MAE: 8.4 score points

## SIRPa

- `Your SIRPa Candidate`: 73.9 (secondary)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, surface-translation support.
  Evidence: Example row you can overwrite with your own candidate
## Siglec-9

- `Your Siglec-9 Candidate`: 66.9 (secondary)
  Reasoning: strong affinity evidence, good target specificity, strong immunomodulation evidence.
  Evidence: Example row you can overwrite with your own candidate

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
