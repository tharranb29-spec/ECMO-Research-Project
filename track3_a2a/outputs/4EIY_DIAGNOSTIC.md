# 4EIY redocking diagnostic

## Frozen v1.0 result

The pre-registered `a2a-dual-state-v1.0` redocking gate failed and remains
failed. ZM241385 passed the 2.0 A top-pose RMSD threshold in only 2 of 5 seeds;
the median top-pose RMSD was 3.0894 A. No acceptance threshold was changed after
observing this result.

The 2YDO/adenosine control passed all 5 seeds with a median RMSD of 0.4894 A.
This indicates that the shared-box implementation and general GNINA execution
path are functioning, but it does not rescue the failed 4EIY case.

## Diagnostic experiment

Seed 44 was repeated with nine retained poses while keeping the receptor, box,
exhaustiveness, and scoring mode unchanged. This diagnostic is not part of the
registered pass/fail calculation.

| GNINA mode | CNNscore | Empirical affinity | RMSD to crystal pose |
| --- | ---: | ---: | ---: |
| 1 | 0.9635 | -9.14 | 3.094 A |
| 2 | 0.7447 | -9.56 | 2.467 A |
| 3 | 0.6820 | -8.51 | 1.205 A |
| 4 | 0.6050 | -8.65 | 1.044 A |
| 5 | 0.5923 | -7.16 | 1.144 A |
| 6 | 0.5916 | -7.84 | 1.454 A |
| 7 | 0.5694 | -9.09 | 2.855 A |
| 8 | 0.4708 | -8.02 | 2.638 A |
| 9 | 0.3315 | -9.57 | 2.873 A |

## Interpretation

GNINA sampled several crystal-like ZM241385 poses but did not rank them first by
CNNscore. Empirical affinity also did not identify the best-RMSD pose. The
failure is therefore pose selection under this receptor/preparation protocol,
not simply failure to explore the crystallographic region.

The high CNNscore of the wrong top pose is also evidence that CNNscore cannot be
treated as an experimentally calibrated probability or an automatic validity
certificate for this target.

## Required next decision

Production docking and model training remain locked. Before creating protocol
v1.1, the team should:

1. Audit receptor atom typing and the aromatic-kekulization warning emitted by
   Open Babel for both receptors.
2. Evaluate at least one additional inactive A2A co-crystal structure selected
   on structural quality and pharmacological relevance, not on whether it gives
   a favorable result.
3. Pre-register whether production features use one selected pose or a
   pose-ensemble aggregation. This decision must be validated across multiple
   co-crystal ligands rather than optimized on ZM241385 alone.
4. If no inactive-state protocol reliably selects cognate poses, use the
   declared single-conformation fallback and remove the state-difference claim.

