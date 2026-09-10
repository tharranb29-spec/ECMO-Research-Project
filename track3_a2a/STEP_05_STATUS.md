# Step 5 status: exploratory mechanistic analysis

## Scope and status

This analysis independently implements the Step 5 model proposed after the
Step 4 development results were known. It is therefore exploratory rather than
confirmatory. It uses only the 171 provisional development records (50
agonists, 121 antagonists); the 43-record locked holdout was not loaded or
scored.

The endpoint is agonist versus antagonist. Seven chemistry descriptors were
standardized and reduced to three principal components, explaining 94.49% of
their variance. Molecular weight was excluded because it correlates 0.9959
with heavy-atom count. The unpenalized logistic model was:

`agonist ~ chemistry PC1 + PC2 + PC3 + m_pk + d_pk`

Here, `m_pk` is mean CNNaffinity across 5NM4 and 2YDO, while `d_pk` is
CNNaffinity(2YDO) minus CNNaffinity(5NM4). All continuous model inputs were
standardized.

## Main result

- Standardized `d_pk` coefficient: **+1.089**
- Molecule-bootstrap 95% interval: **+0.368 to +3.363** (5,000 resamples)
- Two-sided label-permutation p-value: **< 0.0001** (10,000 resamples; no
  permuted coefficient was as extreme)
- Leave-one-molecule-out sign stability: **171/171 positive**
- Chemistry PC sensitivity: positive for every specification from one through
  six PCs; permutation p-values ranged from 0.0005 to 0.0020

This is evidence of a reproducible **conformation-associated CNN scoring
signal** in the development dataset after adjustment for coarse chemistry. It
is not experimental proof of receptor conformational selectivity.

## Negative and limiting results

The force-field `d_affinity` comparator was not significant: standardized
coefficient -0.286, permutation p = 0.148.

`d_pk` correlates 0.7929 with `d_cnnscore`. In a joint model, the conditional
`d_pk` coefficient was +0.209 (Wald p = 0.742) and the conditional
`d_cnnscore` coefficient was +1.270 (Wald p = 0.0508). Neither independently
passes p < 0.05, so pose-quality entanglement prevents attribution of the
development signal uniquely to CNNaffinity.

Step 4 remains negative for predictive gain. Step 5 does not overturn that
result and should not be described as improving agonist-versus-antagonist
classification.

## Permitted conclusion

The development analysis identified a robust directional difference in GNINA
CNN scoring between active-like and inactive receptor conformations after
coarse chemistry adjustment. This signal is exploratory, correlated with pose
quality, and requires confirmation on formally reviewed, untouched data.

## Next gate

Complete record-level dual review and hash the reviewed manifest. Then freeze
a prospective v1.3 hypothesis before performing one evaluation on untouched
data. A future dataset should prioritize same-scaffold functional
counterexamples to weaken the current chemistry-label confounding.
