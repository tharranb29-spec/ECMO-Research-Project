# MD external-service handoff v1.5

This handoff contains public molecular structures only. It does not contain
external potency outcomes or candidate functional labels.

## CGenFF requests

Submit each MOL2 file in `outputs/v1.5/md/cgenff_requests/` independently to
CGenFF/ParamChem or the CHARMM-GUI Ligand Reader and Modeler. Preserve the
submitted MOL2, generated topology/parameter stream, job metadata, software
version, and retrieval timestamp.

Expected formal charges are:

- NEC: 0
- ZMA: 0
- C5A: -1
- C7A: 0
- C9A: 0
- PGD2: -1

Reject an output if the returned structure differs from the submitted parent
structure or formal charge. Any CGenFF penalty above 50 blocks that ligand.
Every term from 10 through 50 requires documented manual review. Do not average,
ignore, or silently edit penalties.

Return one stream file per residue, with each filename beginning with its frozen
residue name (for example, `NEC.str`). Place the six files in
`outputs/v1.5/md/cgenff_parameters/`, then run
`python3 track3_a2a/audit_cgenff_parameters_v15.py`. Production remains blocked
unless the audit reports `all_ligand_parameters_audited_and_accepted`; terms in
the manual-review range cannot be cleared automatically.

## Tier A structure building

The files in `outputs/v1.5/md/builder_inputs/` are non-production starting
coordinates. They must pass through visual structure rebuilding before membrane
construction.

For 5NM4:

1. Restore all nine declared receptor mutations to human ADORA2A, including
   orthosteric S277A.
2. Model only the declared ICL3 segment and complete missing sidechains.
3. Preserve the deposited ZMA pose, sodium ion, and the 17 frozen local waters.

For 5G53:

1. Retain receptor B, mini-Gs D, and NECA.
2. Restore receptor A154N and model only the declared internal missing segments.
3. Refine the GDP pose and local mini-Gs pocket. The preliminary rigid transfer
   has a 0.977 A GDP O6–Ala D366 CB clash and must not be accepted unchanged.

For both systems, reject chirality errors, cis-peptide artifacts, severe clashes,
loop knots, membrane-spanning loop artifacts, or unexplained ligand movement.
Return coordinate, topology, decision, and validation files with SHA-256 hashes.

## Membrane construction

Only after the completed constructs and ligand parameters pass:

- orient using the stored OPM/PPM transform;
- build both leaflets as 70:30 POPC:cholesterol;
- use CHARMM-modified TIP3P, 0.15 M salt, 310 K, and 1 bar;
- record exact lipid, water, and ion counts and final net charge;
- generate OpenMM-compatible production inputs and preserve all builder logs.

The Mac is suitable for minimization and short smoke tests. Full Tier A/Tier B
production should be checkpointed on GPU compute, such as Google Colab, after
the preflight manifest reports no blockers.
