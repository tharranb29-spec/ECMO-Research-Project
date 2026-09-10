# ECMO Seed Ranking Report

Input set: `outputs/autonomous_candidates.json`

This report comes from a small literature-seeded ranking prototype. It is useful for project design and prioritization discussions, not as a final discovery model.

## Model Notes

- `SIRPa`: leave-one-out MAE: 4.5 score points
- `Siglec-9`: leave-one-out MAE: 8.4 score points

## SIRPa

- `PD1`: 41.7 (reject)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Unveiling the immune microenvironment in sinonasal intestinal type adenocarcinoma: new arguments for immunotherapy. (new literature lead, heuristic extraction)
- `pLac`: 37.7 (reject)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Pretransfusion testing interference profile of IMC-002: A novel anti-CD47 monoclonal antibody engineered for minimized red cell binding. (known reference, heuristic extraction)
## Siglec-9

- `Neu5Ac`: 49.8 (reject)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Defined O-acetylated Neu5Ac substrates reveal position-specific preferences of gut bacterial sialidases. (new literature lead, heuristic extraction)
- `Delta`: 54.9 (hold)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages. (new literature lead, heuristic extraction)
- `N-expressing`: 54.9 (hold)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages. (new literature lead, heuristic extraction)
- `SARS-CoV-2`: 54.9 (hold)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages. (new literature lead, heuristic extraction)
- `pLac`: 52.5 (hold)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Molecular innate immune programs of tumor-associated macrophages in immune checkpoint blockade resistance: a staged framework from suppressive circuitry to translational bottlenecks. (known reference, heuristic extraction)

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
