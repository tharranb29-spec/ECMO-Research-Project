# A2A molecular-dynamics validation plan, version 1.5

## Purpose and boundary

The MD module adds the dynamic evidence missing from the current presentation.
It tests whether native and docked poses remain physically plausible and whether
candidate complexes preserve state-relevant A2A interactions. It does not
generate experimental affinity, functional labels, or permission to promote a
failed QSAR model.

## Tier A: native controls

Two deposited complexes establish that the setup can retain known states:

- inactive control: `5NM4` with ZM241385;
- active control: `5G53` with NECA and mini-Gs retained.

The active control replaces the unsupported assumption that an agonist-bound
receptor without a G protein represents a fully active state. Candidate
interpretation stops if either native ligand fails to remain bound and preserve
its defining orthosteric contacts in at least two of three replicas.

## Tier B: blinded candidate panel

The first candidate panel contains all four structurally independent records
from the v1.4 literature pilot: `LIT25-RL-C5`, `LIT25-RL-C7`, `LIT25-RL-C9`,
and `LIT25-MET-PGD2`. They are simulated against `5NM4` and `2YDO` for direct
continuity with the frozen docking comparison. Functional labels stay masked
during setup and trajectory analysis.

Each candidate-state system receives three independently seeded 100 ns
production trajectories after minimization and staged equilibration. This is a
minimum of 2.4 microseconds of candidate production sampling. Every replica is
reported. Selecting only the best-looking trajectory is prohibited.

## Tier C: active-state sensitivity

After both native controls pass, two structurally diverse candidates may enter
a `5G53` mini-Gs sensitivity. Selection is frozen before MD outcomes are viewed.
This tier tests whether conclusions drawn from the intermediate-active `2YDO`
structure remain plausible in a G-protein-coupled active receptor.

## System and run specification

Systems use a POPC/cholesterol membrane, explicit water, 0.15 M NaCl, 310 K,
and 1 bar. The current plan specifies CHARMM36m protein, CHARMM36 lipid, and
CGenFF ligand parameters. Exact software and force-field versions, protonation,
construct edits, retained waters, parameter penalties, system composition, and
all input hashes must be recorded before production.

Production uses periodic boundaries, particle mesh Ewald electrostatics, a
1.0 nm nonbonded cutoff, 2 fs integration, three declared seeds, 100 ps frame
output, and 1 ns restart checkpoints. A technical failure can be rerun only
under a versioned amendment written before inspecting replacement results.

The final 80 ns of each production replica forms the analysis window. A ligand
passes pose retention when its median heavy-atom RMSD is at most 3.0 A after
pocket alignment and its center-of-mass displacement is at most 5.0 A. Direct
contacts use a 4.0 A heavy-atom cutoff. Hydrogen bonds use a 3.5 A
donor-acceptor cutoff and a minimum 120-degree angle. Native control contacts
are enumerated and hashed before production. Each control must retain at least
half of those contacts at 50% or greater occupancy in at least two replicas.

## Predeclared analysis

The primary MD output is stability and mechanism, not a single score. Reports
include ligand RMSD after pocket alignment, center-of-mass displacement,
binding-site retention, and contact occupancy for Glu169, His250, Asn253,
Ser277, and His278. Water-mediated contacts are retained separately.

Receptor-state diagnostics include TM6 cytoplasmic displacement, the DRY ionic
lock, Trp246 rotamer, and NPxxY geometry. Results are summarized by independent
replica. Frames are not treated as independent samples.

MM/GBSA may be included as exploratory supporting evidence with replica-level
uncertainty. It is never described as measured affinity and is not a promotion
gate.

## Execution sequence

1. Resolve structures, constructs, protonation, missing residues, and ligand
   parameters; freeze all hashes.
2. Build and equilibrate both native controls.
3. Run three control replicas and evaluate the control gate.
4. If both controls pass, prepare the eight blinded candidate-state systems.
5. Run and inspect every declared replica with uniform quality control.
6. Freeze Tier B outputs before selecting the two Tier C systems.
7. Run the active-state sensitivity and publish a complete, qualified report.

The machine-readable plan is `config/md_validation.v1.5.json`.

## Structural and methodological references

- `5NM4` inactive-state control: <https://www.rcsb.org/structure/5NM4>
- `5G53` A2A-mini-Gs active-state control:
  <https://www.rcsb.org/structure/5G53>
- Primary `5G53` structure paper: <https://doi.org/10.1038/nature18966>
- A2A-mini-Gs MD precedent: <https://pmc.ncbi.nlm.nih.gov/articles/PMC6445292/>
