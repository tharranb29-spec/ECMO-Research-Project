# Independent inactive-state diagnostic: 5NM4

## Purpose

PDB 5NM4 was selected as a secondary diagnostic because it is an independent
1.70 A room-temperature A2A/ZM241385 structure. It was not selected based on a
known favorable GNINA result and it does not overwrite the registered 4EIY
failure.

The first attempted diagnostic was invalidated before interpretation because
naive PDB residue-number matching retained only 12 common C-alpha atoms. The
corrected workflow maps both DBREF ADORA2A segments to UniProt P29274 before
alignment and enforces a hard alignment-quality gate.

## Valid corrected result

- Common transmembrane C-alpha atoms: 232
- Post-alignment receptor RMSD: 0.2751 A
- Valid GNINA runs: 5/5
- Poses at or below 2.0 A: 4/5
- Median symmetry-minimized heavy-atom RMSD: 1.7177 A
- Gate result under the v1.0 acceptance rule: pass

The result indicates that the pose-selection failure observed for 4EIY is not
universal to all inactive A2A/ZM241385 structures. It does not prove that 5NM4
will generate biologically superior state-difference features.

## Protocol consequence

A future v1.1 protocol may nominate 5NM4 as the primary inactive structure only
if the change is declared before functional-class model results are examined.
The 4EIY failure must remain visible, and the final analysis should report a
structure-sensitivity comparison using both inactive structures. If conclusions
depend on choosing 5NM4 while failing with 4EIY, the state-difference claim is
not robust and must be weakened accordingly.

