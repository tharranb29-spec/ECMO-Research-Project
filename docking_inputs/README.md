# Prepared GNINA inputs

Keep locally prepared structures in this directory.

Expected layout:

- structure_registry.json (tracked provenance and review gate)
- siglec9/AF-Q9Y336-F1-model_v6.pdb (local source model)
- siglec9/siglec9_vset_18-144_raw.pdb (local cropped model)
- siglec9/siglec9_vset_18-144_ph7.4.pdb (local protonated receptor)
- siglec9/reference_ligand.sdf
- sirpa/receptor.pdb
- sirpa/reference_ligand.sdf
- ligands/<candidate-id>.sdf

The receptor must be prepared for docking, and the reference ligand must define a validated binding pocket. Candidate SDF paths are stored in each autonomous candidate record as ligand_sdf_path.

Do not treat an RCSB download or an LLM-generated SMILES as a docking-ready structure without manual chemistry review.

Run `python3 prepare_siglec9_gate.py` after receptor preparation or ligand
review. Direct Siglec-9 ranking must remain locked until the registry reports a
reviewed receptor, two verified ligand structures, reproduced NMR contacts, and
five seeded GNINA runs.
