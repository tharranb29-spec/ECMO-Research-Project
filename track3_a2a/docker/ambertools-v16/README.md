# AmberTools v1.6 container

This image pins the open ligand-parameterization environment used by Track 3 protocol v1.6.

Build from the repository root:

```bash
docker build --platform linux/arm64 \
  -t a2a-ambertools:v1.6 \
  track3_a2a/docker/ambertools-v16
```

The production bundle script records the resulting image ID, AmberTools program versions, command lines, input hashes, and output hashes. It uses GAFF2 atom types and AM1-BCC charges. The image does not contain project outcomes.
