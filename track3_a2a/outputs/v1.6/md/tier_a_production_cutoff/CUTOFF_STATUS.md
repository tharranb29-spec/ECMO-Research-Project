# Tier A production cutoff status

**Cutoff:** 2026-09-17T14:24:05.656022Z

**Equilibration:** 6/6 passed

**Tier A production:** started; campaign incomplete

**Tier B:** not executed; locked

## Exact cutoff totals

- Completed production replicas: 0/6
- Running replicas: 1
- Failed replicas: 0
- Replicas not observed in the supplied cutoff artifacts: 5
- Aggregate reported production: 5.92/300.00 ns
- Sampling in completed replicas: 0.00/300.00 ns
- Last scheduled checkpoint floor represented by snapshots: 5.90 ns

## Ingested replica snapshots

| System | Replica | Seed | Status | Reported ns | Target ns | Scheduled checkpoint floor ns | Source SHA-256 |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 5NM4_ZMA_native | 1 | 20260914 | running | 5.92 | 50.00 | 5.90 | `9ae68e14b58645a619c18f5693b79be98ab45a45f4bbe8130112ffdbc2927c51` |

## Interpretation boundary

The pilot tests short-timescale pose stability. It is not a convergence, affinity, efficacy, or experimental-validation claim.

This MD cutoff does not assess model-training status. An incomplete MD campaign must not be described as incomplete model training.

A status snapshot establishes only what the hashed artifact reports, including scheduled checkpoint semantics; it does not prove that the checkpoint file itself was supplied. The binary trajectory, checkpoint, and state-data files were not ingested by this cutoff layer.
