# MD gate status v1.5

Status date: 2026-09-13

## Gate decisions

| Gate | Decision | Evidence |
| --- | --- | --- |
| 5G53 deposited chirality caveat | Pass | Assembly 2 selects receptor B/mini-Gs D; ASN D239 has the dominant L-chirality sign. No deposited coordinate was edited. |
| OpenMM and receptor/membrane force fields | Pass for preparation | OpenMM 8.6 and bundled CHARMM36m/CHARMM36 July 2024 files load; POPC, CHL1, GDP, and TIP3 templates are present. |
| Production compute | Not available locally | Only Reference and CPU platforms are usable; the planned 3 microsecond campaign requires accelerated compute. |
| Tier A source completeness | Pass after correction | The truncated 5NM4 download was replaced by the complete official RCSB PDB; ZMA has 40 atoms, sodium is present, and 17 local waters pass the 5 A retention rule. |
| Tier A builder inputs | Partial | Label-blind, non-production inputs are generated and hashed. Missing loops, sidechains, back-mutations, protonation, and visual audits remain. |
| 5G53 GDP transfer | Fail | Local mini-Gs C-to-D alignment RMSD is 0.087 A, but the transferred GDP O6–Ala D366 CB distance is 0.977 A, below the frozen 1.5 A severe-clash gate. |
| CGenFF | Inputs ready; parameters blocked | Six MOL2 request files are charge-audited. Generated stream/topology files and penalty review are absent. |
| Membrane systems | Blocked | Construction must wait for accepted constructs and ligand parameters. |
| Native contacts | Blocked | Definitions must be enumerated from the final accepted native structures, not preliminary deposited structures. |
| Tier A production | Locked | No trajectory may start before all preceding blockers are cleared. |
| Tier B production | Locked | May start only after both Tier A controls pass in at least two of three replicas. |

## Immediate execution sequence

1. In a visual structure builder, restore the declared wild-type receptor
   mutations, model only the frozen internal segments, and resolve the GDP/Ala
   D366 clash. Reject any model with chirality, knot, peptide, or severe-clash
   defects.
2. Generate CGenFF outputs for all six frozen MOL2 files. Block any molecule
   with a penalty above 50; manually review every term from 10 through 50.
3. Build both native controls in the frozen 70:30 POPC/cholesterol bilayer,
   CHARMM TIP3P water, and 0.15 M salt. Audit composition, orientation,
   protonation, net charge, minimum distances, and all file hashes.
4. Enumerate and freeze native ligand contacts only from those accepted final
   structures.
5. Run short minimization/equilibration smoke tests, then the three independent
   100 ns replicas for each Tier A control on accelerated compute.
6. Evaluate the frozen Tier A criteria. Keep all Tier B candidate systems
   locked unless both native controls pass.

No model-promotion claim is available from MD. Independent external `pBind_Ki`
confirmation remains a separate mandatory gate.
