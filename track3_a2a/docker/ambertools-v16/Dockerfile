FROM mambaorg/micromamba:2.3.3

ARG AMBERTOOLS_VERSION=25.3

RUN micromamba install --yes --name base --channel conda-forge \
      "ambertools=${AMBERTOOLS_VERSION}" \
    && micromamba clean --all --yes

LABEL org.opencontainers.image.title="A2A Track 3 AmberTools v1.6"
LABEL org.opencontainers.image.description="Pinned AmberTools environment for GAFF2/AM1-BCC ligand bundle generation"
LABEL org.opencontainers.image.version="1.6"

WORKDIR /work
