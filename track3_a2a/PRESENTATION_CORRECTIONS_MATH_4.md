# Required corrections for the Math 4.0 workflow deck

1. Replace "mean of 3 seeds" with "median of valid seeds" on the docking and
   feature slides. The saved pipeline uses median aggregation and prohibits
   best-of-seed selection.
2. Replace "automated triage, no human adjudication" with "versioned
   computational evidence audit." State that no human validation is claimed.
3. Require explicit functional evidence, human ADORA2A context, adequate target
   confidence, and a traceable primary publication before label admission.
4. Remove self-reported LLM confidence as an acceptance criterion. An LLM may
   extract evidence for quarantined records but cannot provide evidence itself.
5. Remove rejection based on contradiction with same-scaffold molecules.
   Same-scaffold efficacy switches are scientifically possible and should be
   quarantined for conflict analysis instead.
6. Separate label admission from model promotion. AUC can decide whether a
   model version is promoted; it cannot validate or repair individual labels.
7. Add the completed Step 4 result: docking did not significantly improve
   prediction beyond chemistry.
8. Add the completed Step 5 result: the development-stage CNNaffinity state
   difference was directionally positive but entangled with pose quality and is
   not evidence of biological efficacy.
9. Report the active counts: 204 computationally admitted labels, 203 docked
   molecules, 163 development records, 40 untouched holdout records, and 16
   quarantined or rejected records. Eleven exclusions are inverse agonists,
   which are outside the declared binary endpoint.
