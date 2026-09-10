# Track 3 confirmatory holdout status, version 1.3.1

## Decision

The one-time locked-holdout gate **did not pass**. The standardized `d_pk`
coefficient retained the hypothesized positive direction (`+1.048`), but the
predeclared one-sided permutation result was `p = 0.0819`, above `alpha = 0.05`.
This is directional but unconfirmed evidence and cannot support a confirmatory
or biological-efficacy claim.

## Population and controls

- The final machine-curated audit admitted 204 of 220 records.
- The docking feature matrix contains 203 records: 163 development and 40
  locked holdout.
- The holdout contained 13 agonists and 27 antagonists and was evaluated once
  after all input and implementation hashes were frozen.
- Human approval is not required by computational protocol v1.3, but no human
  or experimental validation is claimed.

## Mandatory sensitivities

- Force-field `d_affinity` was null: coefficient `+0.0019`, one-sided
  permutation `p = 0.5192`.
- The holdout correlation between `d_pk` and `d_cnnscore` was `0.7334`, so pose
  quality remains strongly entangled with the learned score.
- Chemistry plus docking did not improve predictive AUC over chemistry alone:
  `AUC(E) = 0.9858`, `AUC(AB) = 0.9886`, `delta = -0.00285`.
- The unpenalized joint sensitivity model was separation-dominated; its extreme
  coefficients are not interpretable as independent effects. A post-hoc
  numerical diagnostic is stored separately and does not alter the primary
  result.

## Defensible conclusion

The development-stage mechanistic signal did not replicate at the predeclared
significance threshold in the locked holdout. The project can still report the
positive direction as hypothesis-generating, while the applied predictive-gain
claim remains negative. The next research cycle should collect counterexample
chemotypes and external functional evidence rather than tune this holdout.
