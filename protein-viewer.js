(function () {
  const CONTROL_REFERENCE = {
    controlPdbId: "1FQ9",
    controlReferenceLabel: "Human FGF2-FGFR1-heparin complex",
    controlLegend: "Heparin control reference",
  };

  const DEFAULT_STRUCTURE = {
    id: "champion",
    viewMode: "dual",
    title: "AI champion compared with heparin control",
    candidatePdbId: "2JJS",
    candidateReferenceLabel: "CD47-SIRPalpha interface",
    candidateLegend: "Checkpoint interface reference",
    candidateName: "Top AI Candidate",
    targetReceptor: "Lead pathway",
    candidateScore: "0.0",
    recommendation: "ADVANCE",
    controlLabel: "Heparin Control",
    badgeLabel: "No.1 Champion",
    ...CONTROL_REFERENCE,
  };

  const STRUCTURE_LIBRARY = {
    champion: {
      candidatePdbId: "2JJS",
      candidateReferenceLabel: "CD47-SIRPalpha interface",
      candidateLegend: "Checkpoint interface reference",
    },
    siglec: {
      candidatePdbId: "2G5R",
      candidateReferenceLabel: "Human Siglec-family ligand-bound proxy",
      candidateLegend: "Siglec-family structural proxy",
    },
    combined: {
      viewMode: "combined",
      candidatePdbId: "2G5R",
      candidateReferenceLabel: "Human Siglec-family ligand-bound proxy",
      candidateLegend: "Siglec-family structural proxy",
    },
    sirpa: {
      candidatePdbId: "2JJS",
      candidateReferenceLabel: "CD47-SIRPalpha interface",
      candidateLegend: "Checkpoint interface reference",
    },
    "2JJS": {
      candidatePdbId: "2JJS",
      candidateReferenceLabel: "CD47-SIRPalpha interface",
      candidateLegend: "Checkpoint interface reference",
    },
    "2G5R": {
      candidatePdbId: "2G5R",
      candidateReferenceLabel: "Human Siglec-family ligand-bound proxy",
      candidateLegend: "Siglec-family structural proxy",
    },
    "1FQ9": {
      controlPdbId: "1FQ9",
      controlReferenceLabel: "Human FGF2-FGFR1-heparin complex",
      controlLegend: "Heparin control reference",
    },
  };

  function afterLayout() {
    return new Promise((resolve) => {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(resolve);
      });
    });
  }

  function normalizeTarget(target) {
    const source = String(target || "").toLowerCase();
    if (source.includes("siglec")) {
      return "Siglec-9";
    }
    if (source.includes("sirp") || source.includes("cd47")) {
      return "SIRPa";
    }
    return target || "Lead pathway";
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function hasRenderableSize(element) {
    if (!element) {
      return false;
    }
    const rect = element.getBoundingClientRect();
    return rect.width > 80 && rect.height > 80;
  }

  async function waitForRenderableSize(element, attempts = 10) {
    for (let index = 0; index < attempts; index += 1) {
      await afterLayout();
      if (hasRenderableSize(element)) {
        return true;
      }
    }
    return false;
  }

  function resolveStructure(structure, container) {
    const structureId = structure.id || container.dataset.structureId || DEFAULT_STRUCTURE.id;
    const libraryEntry = STRUCTURE_LIBRARY[structureId] || STRUCTURE_LIBRARY[structure.candidatePdbId] || {};
    const targetReceptor = normalizeTarget(
      structure.targetReceptor || container.dataset.targetReceptor || DEFAULT_STRUCTURE.targetReceptor
    );
    const targetLibrary = targetReceptor === "Siglec-9" ? STRUCTURE_LIBRARY.siglec : STRUCTURE_LIBRARY.sirpa;

    return {
      ...DEFAULT_STRUCTURE,
      ...targetLibrary,
      ...libraryEntry,
      ...CONTROL_REFERENCE,
      ...structure,
      id: structureId,
      viewMode: structure.viewMode || container.dataset.viewMode || libraryEntry.viewMode || DEFAULT_STRUCTURE.viewMode,
      targetReceptor,
      candidatePdbId:
        structure.candidatePdbId ||
        container.dataset.candidatePdbId ||
        container.dataset.structurePdbId ||
        libraryEntry.candidatePdbId ||
        targetLibrary.candidatePdbId ||
        DEFAULT_STRUCTURE.candidatePdbId,
      controlPdbId:
        structure.controlPdbId ||
        container.dataset.controlPdbId ||
        libraryEntry.controlPdbId ||
        CONTROL_REFERENCE.controlPdbId,
      candidateReferenceLabel:
        structure.candidateReferenceLabel ||
        container.dataset.candidateReferenceLabel ||
        libraryEntry.candidateReferenceLabel ||
        targetLibrary.candidateReferenceLabel ||
        DEFAULT_STRUCTURE.candidateReferenceLabel,
      controlReferenceLabel:
        structure.controlReferenceLabel ||
        container.dataset.controlReferenceLabel ||
        libraryEntry.controlReferenceLabel ||
        CONTROL_REFERENCE.controlReferenceLabel,
      candidateLegend:
        structure.candidateLegend ||
        container.dataset.candidateLegend ||
        libraryEntry.candidateLegend ||
        targetLibrary.candidateLegend ||
        DEFAULT_STRUCTURE.candidateLegend,
      controlLegend:
        structure.controlLegend ||
        container.dataset.controlLegend ||
        libraryEntry.controlLegend ||
        CONTROL_REFERENCE.controlLegend,
      candidateName: structure.candidateName || container.dataset.candidateName || DEFAULT_STRUCTURE.candidateName,
      candidateScore: String(
        structure.candidateScore || container.dataset.candidateScore || DEFAULT_STRUCTURE.candidateScore
      ),
      recommendation: String(
        structure.recommendation || container.dataset.recommendation || DEFAULT_STRUCTURE.recommendation
      ).toUpperCase(),
      controlLabel: structure.controlLabel || container.dataset.controlLabel || DEFAULT_STRUCTURE.controlLabel,
      badgeLabel: structure.badgeLabel || container.dataset.badgeLabel || DEFAULT_STRUCTURE.badgeLabel,
    };
  }

  function buildComparisonLayout(container, structure) {
    container.innerHTML = `
      <div class="comparison-viewer-shell">
        <div class="comparison-protein-grid">
          <section class="comparison-protein-pane control">
            <span class="comparison-pane-label">Control Lane</span>
            <div>
              <h4 class="comparison-pane-title">${escapeHtml(structure.controlLabel)}</h4>
              <p class="comparison-pane-copy">${escapeHtml(structure.controlLegend)} • PDB ${escapeHtml(
                structure.controlPdbId
              )}</p>
            </div>
            <div class="comparison-pane-viewer">
              <div class="viewer-host" data-viewer-role="control"></div>
            </div>
          </section>
          <section class="comparison-protein-pane candidate">
            <span class="comparison-pane-label">${escapeHtml(structure.badgeLabel)}</span>
            <div>
              <h4 class="comparison-pane-title">${escapeHtml(structure.candidateName)}</h4>
              <p class="comparison-pane-copy">${escapeHtml(structure.targetReceptor)} pathway • score ${escapeHtml(
                structure.candidateScore
              )} • ${escapeHtml(structure.recommendation)} • PDB ${escapeHtml(structure.candidatePdbId)}</p>
            </div>
            <div class="comparison-pane-viewer">
              <div class="viewer-host" data-viewer-role="candidate"></div>
            </div>
          </section>
        </div>
        <div class="comparison-insight-row">
          <article class="comparison-insight-card">
            <span class="comparison-insight-label">Heparin Control</span>
            <strong>${escapeHtml(structure.controlReferenceLabel)}</strong>
            <p>Real heparin-bound structural reference used as the ECMO control comparator in this discussion view.</p>
          </article>
          <article class="comparison-insight-card">
            <span class="comparison-insight-label">AI Lead Reference</span>
            <strong>${escapeHtml(structure.candidateReferenceLabel)}</strong>
            <p>Real 3D candidate-side protein context used to explain why the AI-selected ligand differs from heparin control behavior.</p>
          </article>
        </div>
      </div>
    `;

    return {
      controlHost: container.querySelector('[data-viewer-role="control"]'),
      candidateHost: container.querySelector('[data-viewer-role="candidate"]'),
    };
  }

  function buildCombinedLayout(container, structure) {
    container.innerHTML = `
      <div class="combined-viewer-shell">
        <div class="combined-stage-head">
          <div class="combined-stage-copy">
            <h4 class="combined-stage-title">${escapeHtml(structure.candidateName)} + ${escapeHtml(structure.controlLabel)}</h4>
            <p class="combined-stage-note">Single-scene co-visualization of the Siglec-side AI lead and the heparin control reference. This is a conceptual comparison view for discussion, not an experimentally resolved shared complex.</p>
          </div>
          <span class="comparison-pane-label">Combined Scene</span>
        </div>
        <div class="combined-pane-viewer">
          <div class="viewer-host" data-viewer-role="combined"></div>
        </div>
        <div class="comparison-insight-row">
          <article class="comparison-insight-card">
            <span class="comparison-insight-label">Control Reference</span>
            <strong>${escapeHtml(structure.controlReferenceLabel)}</strong>
            <p>The heparin-containing control reference is shown in blue to anchor the ECMO baseline comparison.</p>
          </article>
          <article class="comparison-insight-card">
            <span class="comparison-insight-label">Candidate Reference</span>
            <strong>${escapeHtml(structure.candidateReferenceLabel)}</strong>
            <p>The Siglec-side candidate reference is shown in green so the interaction logic can be discussed in one shared scene.</p>
          </article>
        </div>
      </div>
    `;

    return {
      combinedHost: container.querySelector('[data-viewer-role="combined"]'),
    };
  }

  function getAtoms(model, selection = {}) {
    if (!model || typeof model.selectedAtoms !== "function") {
      return [];
    }
    return model.selectedAtoms(selection);
  }

  function centerOfAtoms(atoms) {
    if (!atoms || !atoms.length) {
      return { x: 0, y: 0, z: 0 };
    }
    const totals = atoms.reduce(
      (acc, atom) => {
        acc.x += atom.x;
        acc.y += atom.y;
        acc.z += atom.z;
        return acc;
      },
      { x: 0, y: 0, z: 0 }
    );
    return {
      x: totals.x / atoms.length,
      y: totals.y / atoms.length,
      z: totals.z / atoms.length,
    };
  }

  function ligandSelection(model) {
    const hetAtoms = getAtoms(model, { hetflag: true });
    if (hetAtoms.length) {
      return {
        selection: { hetflag: true },
        atoms: hetAtoms,
      };
    }
    return null;
  }

  function proteinCenter(model) {
    const atoms = getAtoms(model, {});
    return centerOfAtoms(atoms);
  }

  function shiftModel(model, dx, dy, dz) {
    getAtoms(model, {}).forEach((atom) => {
      atom.x += dx;
      atom.y += dy;
      atom.z += dz;
    });
  }

  function viewerPalette(structure, mode) {
    if (mode === "control") {
      return {
        cartoon: "#8aa3c7",
        ligand: "#3d83f6",
        surface: "#d9e7fb",
        labelBackground: "rgba(61,131,246,0.84)",
      };
    }
    if (normalizeTarget(structure.targetReceptor) === "Siglec-9") {
      return {
        cartoon: "chain",
        ligand: "#13a97b",
        surface: "#d8f2ea",
        labelBackground: "rgba(19,169,123,0.84)",
      };
    }
    return {
      cartoon: "chain",
      ligand: "#d79a1f",
      surface: "#f7ecd0",
      labelBackground: "rgba(215,154,31,0.84)",
    };
  }

  function applyViewerStyle(viewer, pdbText, structure, mode) {
    viewer.clear();
    const model = viewer.addModel(pdbText, "pdb");
    const palette = viewerPalette(structure, mode);

    if (palette.cartoon === "chain") {
      viewer.setStyle({}, { cartoon: { colorscheme: "chain", opacity: 0.95 } });
    } else {
      viewer.setStyle({}, { cartoon: { color: palette.cartoon, opacity: 0.92 } });
    }

    const ligand = ligandSelection(model);
    if (ligand) {
      viewer.setStyle(
        ligand.selection,
        {
          stick: { color: palette.ligand, radius: 0.22, opacity: 0.98 },
          sphere: { color: palette.ligand, radius: 0.28, opacity: 0.72 },
        }
      );
    }

    try {
      viewer.addSurface(
        window.$3Dmol.SurfaceType.VDW,
        { color: palette.surface, opacity: 0.08 },
        {}
      );
    } catch (error) {
      // Surface rendering is optional; keep the 3D model visible if it fails.
    }

    const labelPosition = ligand ? centerOfAtoms(ligand.atoms) : proteinCenter(model);
    viewer.addLabel(mode === "control" ? structure.controlLabel : structure.candidateName, {
      position: labelPosition,
      backgroundColor: palette.labelBackground,
      fontColor: "#ffffff",
      fontSize: 13,
      padding: 6,
      borderRadius: 8,
      inFront: true,
      showBackground: true,
    });

    if (ligand) {
      viewer.zoomTo(ligand.selection);
    } else {
      viewer.zoomTo();
    }
    viewer.zoom(0.92);
    viewer.render();
  }

  function applyCombinedViewerStyle(viewer, controlPdbText, candidatePdbText, structure) {
    viewer.clear();

    const controlModel = viewer.addModel(controlPdbText, "pdb");
    const candidateModel = viewer.addModel(candidatePdbText, "pdb");

    const controlCenter = proteinCenter(controlModel);
    const candidateCenter = proteinCenter(candidateModel);

    shiftModel(controlModel, -24 - controlCenter.x, -controlCenter.y, -controlCenter.z);
    shiftModel(candidateModel, 24 - candidateCenter.x, -candidateCenter.y, -candidateCenter.z);

    if (typeof controlModel.setStyle === "function") {
      controlModel.setStyle({}, { cartoon: { color: "#7fa2d6", opacity: 0.94 } });
      controlModel.setStyle(
        { hetflag: true },
        {
          stick: { color: "#3d83f6", radius: 0.22, opacity: 0.95 },
          sphere: { color: "#3d83f6", radius: 0.28, opacity: 0.7 },
        }
      );
    }

    if (typeof candidateModel.setStyle === "function") {
      candidateModel.setStyle({}, { cartoon: { colorscheme: "chain", opacity: 0.96 } });
      candidateModel.setStyle(
        { hetflag: true },
        {
          stick: { color: "#13a97b", radius: 0.22, opacity: 0.95 },
          sphere: { color: "#13a97b", radius: 0.28, opacity: 0.7 },
        }
      );
    }

    viewer.addLabel(structure.controlLabel, {
      position: proteinCenter(controlModel),
      backgroundColor: "rgba(61,131,246,0.84)",
      fontColor: "#ffffff",
      fontSize: 13,
      padding: 6,
      borderRadius: 8,
      inFront: true,
      showBackground: true,
    });

    viewer.addLabel(structure.candidateName, {
      position: proteinCenter(candidateModel),
      backgroundColor: "rgba(19,169,123,0.84)",
      fontColor: "#ffffff",
      fontSize: 13,
      padding: 6,
      borderRadius: 8,
      inFront: true,
      showBackground: true,
    });

    viewer.addArrow({
      start: { x: -6, y: 0, z: 0 },
      end: { x: 6, y: 0, z: 0 },
      radius: 0.22,
      color: "#7788a3",
      mid: 0.7,
    });

    viewer.addLabel("Conceptual comparison", {
      position: { x: 0, y: 5, z: 0 },
      backgroundColor: "rgba(16,36,62,0.76)",
      fontColor: "#ffffff",
      fontSize: 12,
      padding: 5,
      borderRadius: 8,
      inFront: true,
      showBackground: true,
    });

    viewer.zoomTo();
    viewer.zoom(0.95);
    viewer.render();
  }

  function fallbackMarkup(container, structure, detail) {
    container.innerHTML = "";
    container.style.display = "grid";
    container.style.placeItems = "center";
    container.style.padding = "24px";

    const card = document.createElement("div");
    card.style.maxWidth = "620px";
    card.style.padding = "18px";
    card.style.borderRadius = "18px";
    card.style.background = "rgba(255,255,255,0.84)";
    card.style.border = "1px solid rgba(19, 37, 64, 0.08)";
    card.style.color = "#5e6f88";
    card.style.fontFamily = "Calibri, Arial, sans-serif";
    card.style.lineHeight = "1.55";

    const title = document.createElement("strong");
    title.style.display = "block";
    title.style.marginBottom = "10px";
    title.style.color = "#145df2";
    title.textContent = structure.title;

    const body = document.createElement("p");
    body.style.margin = "0 0 10px";
    body.textContent = detail || `Unable to render the live 3D protein model for ${structure.candidatePdbId}.`;

    const controlLink = document.createElement("a");
    controlLink.href = `https://www.rcsb.org/structure/${structure.controlPdbId}`;
    controlLink.target = "_blank";
    controlLink.rel = "noreferrer";
    controlLink.textContent = `Open heparin control reference (${structure.controlPdbId})`;
    controlLink.style.color = "#0c43af";
    controlLink.style.fontWeight = "700";
    controlLink.style.display = "block";
    controlLink.style.marginBottom = "8px";

    const candidateLink = document.createElement("a");
    candidateLink.href = `https://www.rcsb.org/structure/${structure.candidatePdbId}`;
    candidateLink.target = "_blank";
    candidateLink.rel = "noreferrer";
    candidateLink.textContent = `Open AI candidate reference (${structure.candidatePdbId})`;
    candidateLink.style.color = "#0c43af";
    candidateLink.style.fontWeight = "700";

    card.append(title, body, controlLink, candidateLink);
    container.append(card);
  }

  async function fetchPdbText(pdbId) {
    const response = await fetch(`/api/structure?pdb=${encodeURIComponent(pdbId)}`, {
      headers: { Accept: "chemical/x-pdb,text/plain" },
    });
    if (!response.ok) {
      throw new Error(`Structure request failed with status ${response.status}.`);
    }
    const pdbText = await response.text();
    if (!pdbText || !pdbText.trim()) {
      throw new Error("The structure response was empty.");
    }
    return pdbText;
  }

  async function renderStructure(container, structure) {
    const resolved = resolveStructure(structure, container);

    if (!window.$3Dmol || typeof window.$3Dmol.createViewer !== "function") {
      fallbackMarkup(container, resolved, "The local 3D viewer library did not load.");
      return;
    }

    if (!hasRenderableSize(container)) {
      container.__proteinViewerMounted = false;
      return;
    }

    try {
      const [controlPdbText, candidatePdbText] = await Promise.all([
        fetchPdbText(resolved.controlPdbId),
        fetchPdbText(resolved.candidatePdbId),
      ]);

      container.style.display = "";
      container.style.placeItems = "";
      container.style.padding = "";
      if (resolved.viewMode === "combined") {
        const refs = buildCombinedLayout(container, resolved);
        const ready = await waitForRenderableSize(refs.combinedHost);
        if (!ready) {
          container.__proteinViewerMounted = false;
          return;
        }

        const combinedViewer = window.$3Dmol.createViewer(refs.combinedHost, {
          backgroundColor: "white",
          antialias: true,
        });

        applyCombinedViewerStyle(combinedViewer, controlPdbText, candidatePdbText, resolved);
        refs.combinedViewer = combinedViewer;
        container.__comparisonRefs = refs;

        window.setTimeout(() => {
          try {
            combinedViewer.resize();
            combinedViewer.render();
          } catch (error) {
            // Keep the last successful render if resize throws.
          }
        }, 220);
      } else {
        const refs = buildComparisonLayout(container, resolved);
        const ready = (await waitForRenderableSize(refs.controlHost)) && (await waitForRenderableSize(refs.candidateHost));
        if (!ready) {
          container.__proteinViewerMounted = false;
          return;
        }

        const controlViewer = window.$3Dmol.createViewer(refs.controlHost, {
          backgroundColor: "white",
          antialias: true,
        });

        const candidateViewer = window.$3Dmol.createViewer(refs.candidateHost, {
          backgroundColor: "white",
          antialias: true,
        });

        applyViewerStyle(controlViewer, controlPdbText, resolved, "control");
        applyViewerStyle(candidateViewer, candidatePdbText, resolved, "candidate");

        refs.controlViewer = controlViewer;
        refs.candidateViewer = candidateViewer;
        container.__comparisonRefs = refs;

        window.setTimeout(() => {
          try {
            controlViewer.resize();
            controlViewer.render();
            candidateViewer.resize();
            candidateViewer.render();
          } catch (error) {
            // Keep the last successful render if resize throws.
          }
        }, 220);
      }

      container.__proteinViewerMounted = true;

      container.dataset.structureId = resolved.id;
      container.dataset.viewMode = resolved.viewMode;
      container.dataset.candidatePdbId = resolved.candidatePdbId;
      container.dataset.controlPdbId = resolved.controlPdbId;
      container.dataset.candidateName = resolved.candidateName;
      container.dataset.targetReceptor = resolved.targetReceptor;
      container.dataset.candidateScore = resolved.candidateScore;
      container.dataset.recommendation = resolved.recommendation;
      container.dataset.controlLabel = resolved.controlLabel;
      container.dataset.badgeLabel = resolved.badgeLabel;
      container.dataset.candidateReferenceLabel = resolved.candidateReferenceLabel;
      container.dataset.controlReferenceLabel = resolved.controlReferenceLabel;
      container.dataset.candidateLegend = resolved.candidateLegend;
      container.dataset.controlLegend = resolved.controlLegend;
    } catch (error) {
      container.__proteinViewerMounted = false;
      fallbackMarkup(container, resolved, error.message);
    }
  }

  async function mount(container) {
    if (!container || container.__proteinViewerBusy || container.__proteinViewerMounted) {
      return;
    }
    if (!hasRenderableSize(container)) {
      return;
    }
    container.__proteinViewerBusy = true;
    try {
      await renderStructure(container, {
        id: container.dataset.structureId || DEFAULT_STRUCTURE.id,
        viewMode: container.dataset.viewMode || DEFAULT_STRUCTURE.viewMode,
        title: container.dataset.structureTitle || DEFAULT_STRUCTURE.title,
        candidatePdbId: container.dataset.candidatePdbId || container.dataset.structurePdbId || DEFAULT_STRUCTURE.candidatePdbId,
        controlPdbId: container.dataset.controlPdbId || CONTROL_REFERENCE.controlPdbId,
        candidateName: container.dataset.candidateName || DEFAULT_STRUCTURE.candidateName,
        targetReceptor: container.dataset.targetReceptor || DEFAULT_STRUCTURE.targetReceptor,
        candidateScore: container.dataset.candidateScore || DEFAULT_STRUCTURE.candidateScore,
        recommendation: container.dataset.recommendation || DEFAULT_STRUCTURE.recommendation,
        controlLabel: container.dataset.controlLabel || DEFAULT_STRUCTURE.controlLabel,
        badgeLabel: container.dataset.badgeLabel || DEFAULT_STRUCTURE.badgeLabel,
        candidateReferenceLabel: container.dataset.candidateReferenceLabel || DEFAULT_STRUCTURE.candidateReferenceLabel,
        controlReferenceLabel: container.dataset.controlReferenceLabel || CONTROL_REFERENCE.controlReferenceLabel,
        candidateLegend: container.dataset.candidateLegend || DEFAULT_STRUCTURE.candidateLegend,
        controlLegend: container.dataset.controlLegend || CONTROL_REFERENCE.controlLegend,
      });
    } finally {
      container.__proteinViewerBusy = false;
    }
  }

  function updateTextTarget(id, value) {
    if (!id || !value) {
      return;
    }
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  function activateStructure(button) {
    const targetId = button.dataset.structureTarget;
    const container = targetId ? document.getElementById(targetId) : null;
    if (!container) {
      return;
    }

    const structure = {
      id: button.dataset.structureId || DEFAULT_STRUCTURE.id,
      viewMode: button.dataset.viewMode || container.dataset.viewMode || DEFAULT_STRUCTURE.viewMode,
      title: button.dataset.structureTitle || DEFAULT_STRUCTURE.title,
      candidatePdbId:
        button.dataset.candidatePdbId ||
        button.dataset.structurePdbId ||
        container.dataset.candidatePdbId ||
        DEFAULT_STRUCTURE.candidatePdbId,
      controlPdbId: button.dataset.controlPdbId || container.dataset.controlPdbId || CONTROL_REFERENCE.controlPdbId,
      candidateName: button.dataset.candidateName || container.dataset.candidateName || DEFAULT_STRUCTURE.candidateName,
      targetReceptor: button.dataset.targetReceptor || container.dataset.targetReceptor || DEFAULT_STRUCTURE.targetReceptor,
      candidateScore: button.dataset.candidateScore || container.dataset.candidateScore || DEFAULT_STRUCTURE.candidateScore,
      recommendation: button.dataset.recommendation || container.dataset.recommendation || DEFAULT_STRUCTURE.recommendation,
      controlLabel: button.dataset.controlLabel || container.dataset.controlLabel || DEFAULT_STRUCTURE.controlLabel,
      badgeLabel: button.dataset.badgeLabel || container.dataset.badgeLabel || DEFAULT_STRUCTURE.badgeLabel,
      candidateReferenceLabel:
        button.dataset.candidateReferenceLabel ||
        container.dataset.candidateReferenceLabel ||
        DEFAULT_STRUCTURE.candidateReferenceLabel,
      controlReferenceLabel:
        button.dataset.controlReferenceLabel ||
        container.dataset.controlReferenceLabel ||
        CONTROL_REFERENCE.controlReferenceLabel,
      candidateLegend: button.dataset.candidateLegend || container.dataset.candidateLegend || DEFAULT_STRUCTURE.candidateLegend,
      controlLegend: button.dataset.controlLegend || container.dataset.controlLegend || CONTROL_REFERENCE.controlLegend,
    };

    renderStructure(container, structure);

    updateTextTarget(button.dataset.chipTarget, button.dataset.chipLabel);
    updateTextTarget(button.dataset.descriptionTarget, button.dataset.description);
    updateTextTarget(button.dataset.noteTarget, button.dataset.note);
    updateTextTarget(button.dataset.tagOneTarget, button.dataset.tagOne);
    updateTextTarget(button.dataset.tagTwoTarget, button.dataset.tagTwo);
    updateTextTarget(button.dataset.tagThreeTarget, button.dataset.tagThree);
    updateTextTarget(button.dataset.extraTarget, button.dataset.extraLabel);

    const switcher = button.closest("[data-structure-switcher]");
    if (switcher) {
      switcher.querySelectorAll("button").forEach((node) => {
        node.classList.toggle("active", node === button);
      });
    }
  }

  function mountSwitchers() {
    document.querySelectorAll("[data-structure-switcher]").forEach((switcher) => {
      switcher.querySelectorAll("button").forEach((button) => {
        if (button.__structureBound) {
          return;
        }
        button.__structureBound = true;
        button.addEventListener("click", () => activateStructure(button));
      });
    });
  }

  function mountAll() {
    document.querySelectorAll("[data-protein-viewer]").forEach((element) => mount(element));
    mountSwitchers();
  }

  function refreshVisible() {
    document.querySelectorAll("[data-protein-viewer]").forEach((element) => {
      if (!hasRenderableSize(element)) {
        return;
      }
      element.__proteinViewerMounted = false;
      mount(element);
    });
  }

  window.ECMOProteinViewer = { mount, mountAll, renderStructure, refreshVisible };
})();
