# Track 3 v1.6 implementation status

**Status date:** 2026-09-15

**Deadline:** 2026-09-30

**Outcome firewall:** sealed

**MD production trajectories started:** no

## Workstream A — protocol and governance

The v1.6 exit gate has passed. `config/protocol.v1.6.json` and `V16_PROTOCOL_AMENDMENT.md` are machine-validated and signed by the freeze manifest. The primary endpoint is `pBind_Ki`; `AB_Ridge(alpha=1.0)` is the primary external predictor; and the RF comparators are frozen at 500 trees, `sqrt`, leaf 1, and seed 20260914.

The ten-repeat grouped development rerun used 78 `pBind_Ki` molecules and 68 generic Murcko scaffolds. R2 values were:

| Model | R2 |
| --- | ---: |
| Ridge | 0.561 |
| RF 500/sqrt/1 | 0.503 |
| RF 500/sqrt/1 plus docking | 0.482 |
| Fold-training mean | -0.037 |

The result confirms that the revised RF setting is stronger than the old v1.5 RF setting but does not displace Ridge. Docking remains non-incremental in development.

## Workstream B — independent external confirmation

The label-blind 240-candidate queue remains unchanged. PubMed retrieval covered all 141 unique linked PMIDs; 140 records include abstracts. Twenty-nine records carried PMC identifiers. Eighteen machine-readable full texts were retrieved, while 11 unavailable texts are retained as retrieval limitations, not evidence failures.

Membership is not frozen and no Ki outcome has been joined. The next gate is deterministic source triage followed by an independently configured source-grounded extraction pass. Only exact agreement may admit a molecule; all ambiguity or disagreement is quarantined.

The deterministic pass-1 preflight is now complete for all 240 candidates. It projects only label-blind identity and provenance fields, explicitly ignores the outcome-derived queue field, and admits zero records. It routes 187 candidates to pass 2: 24 are full-text-ready, 131 have primary abstract support but require source text, 31 require exact endpoint resolution, and one has a DOI but no linked PubMed record. Seven non-primary sources and 46 records without explicit A2A support in the retrieved evidence remain quarantined. Multi-PMID records are assessed source by source rather than being treated as malformed identifiers.

## Workstream C — open MD v1.6

The institutional CGenFF blocker has been removed. A pinned Linux ARM64 image containing AmberTools 25.3 was built locally. All six required GAFF2/AM1-BCC bundles—NEC, ZMA, C5A, C7A, C9A, and PGD2—passed net-charge, topology, parameter, atom-map, graph, stereochemistry, and hash checks.

C5A initially failed only because RDKit interpreted valid lowercase GAFF2 types as element symbols. The failed audit is preserved. A separate non-production Tripos-typed audit copy demonstrated that C5A is achiral and that its complete atom/bond graph is preserved. Production GAFF2 files were not altered.

The active 5G53 B/D control is prospectively nucleotide-free. GDP will not be transplanted from the alternate copy after the rejected 0.9768 A GDP–Ala366 clash.

Both Tier A receptor constructs have now been completed computationally. The 5NM4 construct restores nine crystallographic mutations, models the declared ICL3 segment, and maps continuously to human ADORA2A residues 2–304. The 5G53 construct restores A154N, models the declared receptor and mini-Gs gaps, retains only chains B/D, and contains no GDP. The initial 5NM4 candidate correctly failed on one 1.435 Å Arg293–Arg296 side-chain contact; restrained pre-membrane relaxation removed it without breaking sequence continuity. The larger 5G53 construct passed its initial geometry gate and receives only a bounded pre-membrane relaxation because the final periodic-system minimization is the production-relevant gate.

Native ZMA and NECA poses have been transferred into the accepted GAFF2 bundles. ZMA reproduces the deposited heavy-atom pose directly; NECA uses an audited atom-order-identical alignment and then fixes every heavy atom to its deposited coordinate. The mapped controls retain 75 and 72 protein contact pairs within 4 Å, respectively, with no sub-1 Å ligand–protein heavy-atom clash.

Both unsolvated ff19SB/GAFF2 receptor–ligand compatibility builds pass tleap, topology, finite-energy, and geometry checks. A deterministic Amber translation step types explicit histidine tautomers, maps four disulfide pairs per construct to CYX, and removes the generic backbone hydrogen at each 5G53 chain start so tleap can generate correct uncapped N-terminal hydrogens. The accepted bundles contain no missing bonded parameter or fatal token.

The Amber Lipid21 mixed-membrane patch is accepted at 86 POPC and 38 cholesterol molecules (30.65% cholesterol). Three colliding POPC residues and one leaflet-balancing POPC residue were removed. A restrained lipid-heavy-atom relaxation then reduced the patch energy from `2.799e15` to `-247559.8 kJ/mol`; the accepted relaxed patch has no cross-residue non-water atom contact below 1 Å.

Both complete periodic Tier A controls now pass assembly. The inactive 5NM4-ZMA system has 81,447 particles, 156 POPC, 70 cholesterol, and 75 frozen native contacts. The active nucleotide-free 5G53-NECA-mini-Gs system has 210,308 particles, 322 POPC, 148 cholesterol, and 74 frozen native contacts. Both have finite initial energy, the declared approximately 70:30 membrane composition, normalized coordinate-export identifiers, and zero non-water heavy-atom clashes below 1 Å.

Both systems also pass bounded minimization, NVT, and semi-isotropic membrane-NPT smoke tests with finite energy, volume, and coordinates and 100% retention of the frozen contacts at the 6 Å smoke threshold. These are initialization checks, not equilibrated trajectories. Two deterministic signed release archives (6.4 MB and 14.9 MB) now carry the full systems for GitHub/Colab without committing 44–97 MB raw XML files.

The next gate is the prospectively frozen 2.14 ns staged equilibration for both systems under all three predeclared seeds. Its runner is checkpointable and selects CUDA, usable OpenCL, or CPU without changing the protocol. A scaled Mac CPU preflight passed the execution logic but cannot count as equilibration. Tier A production remains locked until all six full-duration equilibration audits pass; Tier B remains locked until the later Tier A control-production rule passes in at least two of three replicas for each control.

## Workstream D — autonomous dashboard

The legacy dashboard is preserved unchanged. Track 3 redesign starts on September 16, after the static v1.6 evidence contracts are stable. The first dashboard release will expose versioned evidence, molecule, model, docking, and MD-gate records before the autonomous literature loop is enabled in shadow mode.

The machine-readable source of this status is `outputs/v1.6/implementation_status.json`.
