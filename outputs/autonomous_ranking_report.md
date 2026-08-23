# ECMO Seed Ranking Report

Input set: `outputs/autonomous_candidates.json`

This report comes from a small literature-seeded ranking prototype. It is useful for project design and prioritization discussions, not as a final discovery model.

## Model Notes

- `SIRPa`: leave-one-out MAE: 4.5 score points
- `Siglec-9`: leave-one-out MAE: 8.4 score points

## SIRPa

- `CD40`: 44.0 (reject)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer. (new literature lead, heuristic extraction)
- `Fc-fusion`: 44.0 (reject)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer. (new literature lead, heuristic extraction)
## Siglec-9

- `Siglec-7`: 57.2 (hold)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Targeting ST3GAL1 to downregulate ligands for the glycoimmune checkpoint Siglec-7 and reverse immune escape in hepatocellular carcinoma. (new literature lead, heuristic extraction)
- `pLac`: 49.8 (reject)
  Reasoning: strong affinity evidence, strong immunomodulation evidence, good target specificity.
  Evidence: Recent literature mention in article: Nociceptor neurons control pollution-mediated neutrophilic asthma. (known reference, heuristic extraction)

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
