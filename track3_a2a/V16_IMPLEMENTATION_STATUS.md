# Track 3 v1.6 implementation status

**Status date:** 2026-09-14

**Deadline:** 2026-09-30

**Outcome firewall:** sealed

**MD trajectories started:** no

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

## Workstream C — open MD v1.6

The institutional CGenFF blocker has been removed. A pinned Linux ARM64 image containing AmberTools 25.3 was built locally. All six required GAFF2/AM1-BCC bundles—NEC, ZMA, C5A, C7A, C9A, and PGD2—passed net-charge, topology, parameter, atom-map, graph, stereochemistry, and hash checks.

C5A initially failed only because RDKit interpreted valid lowercase GAFF2 types as element symbols. The failed audit is preserved. A separate non-production Tripos-typed audit copy demonstrated that C5A is achiral and that its complete atom/bond graph is preserved. Production GAFF2 files were not altered.

The active 5G53 B/D control is prospectively nucleotide-free. GDP will not be transplanted from the alternate copy after the rejected 0.9768 A GDP–Ala366 clash. Tier A remains locked pending completed receptor constructs, membranes, frozen native contacts, and local minimization/NVT/NPT smoke tests. Tier B remains locked until both Tier A controls pass.

## Workstream D — autonomous dashboard

The legacy dashboard is preserved unchanged. Track 3 redesign starts on September 16, after the static v1.6 evidence contracts are stable. The first dashboard release will expose versioned evidence, molecule, model, docking, and MD-gate records before the autonomous literature loop is enabled in shadow mode.

The machine-readable source of this status is `outputs/v1.6/implementation_status.json`.
