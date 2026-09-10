# Computational curation amendment, version 1.3

## Purpose

This prospective amendment replaces mandatory human dual review with a
machine-curated evidence audit for future label admission. It is adopted after
the v1.2 development analyses but before rebuilding or accessing a new locked
holdout. It does not rewrite, relabel, or erase the frozen v1.2 protocol or its
results.

The governing machine-readable rules are in
`config/computational_curation.v1.3.json`.

## Scientific boundary

The audit may classify a record only when cached ChEMBL evidence establishes:

- an explicit functional readout;
- an agonist or antagonist direction;
- human ADORA2A / CHEMBL251 context;
- target confidence of at least 8; and
- a traceable primary publication with a DOI or PubMed identifier.

Binding-only, partial agonist, inverse agonist, wrong-context, conflicting, and
unresolved evidence is rejected or quarantined. The process never describes a
machine decision as human-reviewed or experimentally validated.

## Two independent gates

Label admission is determined only from source evidence. Model AUC, GNINA,
CNNaffinity, chemical similarity, and same-scaffold agreement cannot admit or
reject a label.

Model promotion is evaluated separately using the frozen scaffold-split and
uncertainty protocol. A model-performance gate cannot repair weak provenance or
establish that an individual label is correct.

## LLM role

An LLM may extract candidate passages for quarantined records, but its
self-reported confidence is not evidence. Every promoted record must still pass
the deterministic source, assay, organism, target, and class-direction checks.

## Reproducibility

Run:

```bash
.venv-track3/bin/python -m track3_a2a.run_computational_curation_v13
```

The command writes an all-record decision ledger, a computationally curated
unpartitioned benchmark, and a hash-linked audit report. Accepted records remain
training-ineligible until scaffold-separated development and holdout manifests
are rebuilt and hashed.
