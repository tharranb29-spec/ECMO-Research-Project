(function () {
  const DEFAULT_STRUCTURE = {
    id: "champion",
    pdbId: "2JJS",
    title: "AI champion compared with heparin control",
    candidateName: "Top AI Candidate",
    targetReceptor: "Lead pathway",
    candidateScore: "0.0",
    recommendation: "ADVANCE",
    controlLabel: "Heparin Coating",
    badgeLabel: "No.1 Champion",
  };

  const STRUCTURE_LIBRARY = {
    champion: { pdbId: "2JJS", referenceLabel: "CD47-SIRPalpha interface reference" },
    siglec: { pdbId: "1OD9", referenceLabel: "Representative Siglec-family glycan-bound reference" },
    sirpa: { pdbId: "2JJS", referenceLabel: "CD47-SIRPalpha interface reference" },
    "2JJS": { pdbId: "2JJS", referenceLabel: "CD47-SIRPalpha interface reference" },
    "2VSC": { pdbId: "2VSC", referenceLabel: "CD47 ectodomain scaffold reference" },
    "2WNG": { pdbId: "2WNG", referenceLabel: "SIRPalpha ectodomain reference" },
    "1OD9": { pdbId: "1OD9", referenceLabel: "Representative Siglec-family glycan-bound reference" },
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

  function resolveStructure(structure, container) {
    const libraryEntry = STRUCTURE_LIBRARY[structure.id] || STRUCTURE_LIBRARY[structure.pdbId] || {};
    const targetReceptor = normalizeTarget(structure.targetReceptor || container.dataset.targetReceptor || DEFAULT_STRUCTURE.targetReceptor);
    const fallbackLibrary = targetReceptor === "Siglec-9" ? STRUCTURE_LIBRARY.siglec : STRUCTURE_LIBRARY.sirpa;

    return {
      ...DEFAULT_STRUCTURE,
      ...fallbackLibrary,
      ...libraryEntry,
      ...structure,
      pdbId: structure.pdbId || container.dataset.structurePdbId || libraryEntry.pdbId || fallbackLibrary.pdbId || DEFAULT_STRUCTURE.pdbId,
      targetReceptor,
      candidateName: structure.candidateName || container.dataset.candidateName || DEFAULT_STRUCTURE.candidateName,
      candidateScore: String(structure.candidateScore || container.dataset.candidateScore || DEFAULT_STRUCTURE.candidateScore),
      recommendation: String(structure.recommendation || container.dataset.recommendation || DEFAULT_STRUCTURE.recommendation).toUpperCase(),
      controlLabel: structure.controlLabel || container.dataset.controlLabel || DEFAULT_STRUCTURE.controlLabel,
      badgeLabel: structure.badgeLabel || container.dataset.badgeLabel || DEFAULT_STRUCTURE.badgeLabel,
      referenceLabel: structure.referenceLabel || container.dataset.referenceLabel || libraryEntry.referenceLabel || fallbackLibrary.referenceLabel || "Protein reference",
    };
  }

  function buildComparisonLayout(container, structure) {
    container.innerHTML = `
      <div class="comparison-viewer-shell">
        <div class="comparison-protein-grid">
          <section class="comparison-protein-pane control">
            <span class="comparison-pane-label">Control</span>
            <div>
              <h4 class="comparison-pane-title">${escapeHtml(structure.controlLabel)}</h4>
              <p class="comparison-pane-copy">Real 3D protein scaffold shown with a muted control interaction overlay for baseline comparison.</p>
            </div>
            <div class="comparison-pane-viewer">
              <div class="viewer-host" data-viewer-role="control"></div>
            </div>
          </section>
          <section class="comparison-protein-pane candidate">
            <span class="comparison-pane-label">${escapeHtml(structure.badgeLabel)}</span>
            <div>
              <h4 class="comparison-pane-title">${escapeHtml(structure.candidateName)}</h4>
              <p class="comparison-pane-copy">${escapeHtml(structure.targetReceptor)} pathway view • score ${escapeHtml(structure.candidateScore)} • ${escapeHtml(structure.recommendation)}</p>
            </div>
            <div class="comparison-pane-viewer">
              <div class="viewer-host" data-viewer-role="candidate"></div>
            </div>
          </section>
        </div>
        <div class="comparison-insight-row">
          <article class="comparison-insight-card">
            <span class="comparison-insight-label">Control Interpretation</span>
            <strong>Heparin benchmark</strong>
            <p>Used as the baseline non-specific coating comparator rather than a target-matched inhibitory ligand.</p>
          </article>
          <article class="comparison-insight-card">
            <span class="comparison-insight-label">3D Protein Reference</span>
            <strong>${escapeHtml(structure.referenceLabel)}</strong>
            <p>The model stays interactive so you can rotate the protein while discussing the control-versus-AI interaction hotspots.</p>
          </article>
        </div>
      </div>
    `;

    return {
      controlHost: container.querySelector('[data-viewer-role="control"]'),
      candidateHost: container.querySelector('[data-viewer-role="candidate"]'),
    };
  }

  function getAtoms(model) {
    if (!model || typeof model.selectedAtoms !== "function") {
      return [];
    }
    return model.selectedAtoms({});
  }

  function computeAnchorPoints(model, targetReceptor) {
    const atoms = getAtoms(model);
    if (!atoms.length) {
      return {
        center: { x: 0, y: 0, z: 0 },
        control: { x: -18, y: 12, z: 8 },
        candidate: { x: 18, y: -10, z: -8 },
        controlAnchor: { x: -6, y: 2, z: 0 },
        candidateAnchor: { x: 6, y: -2, z: 0 },
      };
    }

    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    let minZ = Infinity;
    let maxZ = -Infinity;
    let sumX = 0;
    let sumY = 0;
    let sumZ = 0;

    atoms.forEach((atom) => {
      minX = Math.min(minX, atom.x);
      maxX = Math.max(maxX, atom.x);
      minY = Math.min(minY, atom.y);
      maxY = Math.max(maxY, atom.y);
      minZ = Math.min(minZ, atom.z);
      maxZ = Math.max(maxZ, atom.z);
      sumX += atom.x;
      sumY += atom.y;
      sumZ += atom.z;
    });

    const center = {
      x: sumX / atoms.length,
      y: sumY / atoms.length,
      z: sumZ / atoms.length,
    };

    const spanX = Math.max(18, maxX - minX);
    const spanY = Math.max(18, maxY - minY);
    const spanZ = Math.max(18, maxZ - minZ);
    const isSiglec = normalizeTarget(targetReceptor) === "Siglec-9";

    return {
      center,
      control: {
        x: center.x - spanX * 0.34,
        y: center.y + spanY * (isSiglec ? 0.12 : 0.16),
        z: center.z + spanZ * 0.12,
      },
      candidate: {
        x: center.x + spanX * 0.28,
        y: center.y - spanY * (isSiglec ? 0.18 : 0.12),
        z: center.z - spanZ * 0.08,
      },
      controlAnchor: {
        x: center.x - spanX * 0.08,
        y: center.y + spanY * 0.04,
        z: center.z,
      },
      candidateAnchor: {
        x: center.x + spanX * 0.08,
        y: center.y - spanY * 0.04,
        z: center.z,
      },
    };
  }

  function addInteractionShapes(viewer, points, mode, structure) {
    const colors = mode === "control"
      ? { primary: "#4a95ff", secondary: "#7fb8ff", labelBg: "rgba(74,149,255,0.82)" }
      : normalizeTarget(structure.targetReceptor) === "Siglec-9"
        ? { primary: "#1f73ff", secondary: "#4ed3b0", labelBg: "rgba(31,115,255,0.82)" }
        : { primary: "#1b8f5a", secondary: "#f0bf4e", labelBg: "rgba(27,143,90,0.82)" };

    const hotspot = mode === "control" ? points.control : points.candidate;
    const anchor = mode === "control" ? points.controlAnchor : points.candidateAnchor;

    viewer.addSphere({
      center: hotspot,
      radius: 2.6,
      color: colors.secondary,
      opacity: 0.62,
    });

    viewer.addArrow({
      start: hotspot,
      end: anchor,
      radius: 0.22,
      color: colors.primary,
      mid: 0.7,
    });

    viewer.addLabel(
      mode === "control" ? "Heparin control" : structure.candidateName,
      {
        position: hotspot,
        backgroundColor: colors.labelBg,
        fontColor: "#ffffff",
        fontSize: 13,
        padding: 6,
        borderRadius: 8,
        inFront: true,
        showBackground: true,
      }
    );
  }

  function applyViewerStyle(viewer, pdbText, structure, mode) {
    viewer.clear();
    const model = viewer.addModel(pdbText, "pdb");

    if (mode === "control") {
      viewer.setStyle({}, { cartoon: { color: "#8ea3bf", opacity: 0.88 } });
      viewer.setStyle({ hetflag: true }, { stick: { color: "#4a95ff", radius: 0.18, opacity: 0.55 } });
      try {
        viewer.addSurface(window.$3Dmol.SurfaceType.VDW, { color: "#d7e5fa", opacity: 0.06 }, {});
      } catch (error) {
        // Surface rendering is optional; keep the model visible if this fails.
      }
    } else {
      viewer.setStyle({}, { cartoon: { colorscheme: "chain" } });
      viewer.setStyle({ hetflag: true }, { stick: { color: "#f28a2e", radius: 0.22, opacity: 0.9 } });
      try {
        viewer.addSurface(window.$3Dmol.SurfaceType.VDW, { color: "#cfe9dc", opacity: 0.05 }, {});
      } catch (error) {
        // Surface rendering is optional; keep the model visible if this fails.
      }
    }

    const points = computeAnchorPoints(model, structure.targetReceptor);
    addInteractionShapes(viewer, points, mode, structure);
    viewer.zoomTo();
    viewer.render();
  }

  function fallbackMarkup(container, structure, detail) {
    container.innerHTML = "";
    container.style.display = "grid";
    container.style.placeItems = "center";
    container.style.padding = "24px";

    const card = document.createElement("div");
    card.style.maxWidth = "520px";
    card.style.padding = "18px";
    card.style.borderRadius = "18px";
    card.style.background = "rgba(255,255,255,0.82)";
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
    body.textContent = detail || `Unable to render the live 3D protein model for ${structure.pdbId} right now.`;

    const link = document.createElement("a");
    link.href = `https://www.rcsb.org/structure/${structure.pdbId}`;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = `Open PDB ${structure.pdbId} on RCSB`;
    link.style.color = "#0c43af";
    link.style.fontWeight = "700";

    card.append(title, body, link);
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

    try {
      const pdbText = await fetchPdbText(resolved.pdbId);
      const refs = buildComparisonLayout(container, resolved);

      await afterLayout();

      const controlViewer = window.$3Dmol.createViewer(refs.controlHost, {
        backgroundColor: "white",
        antialias: true,
      });

      const candidateViewer = window.$3Dmol.createViewer(refs.candidateHost, {
        backgroundColor: "white",
        antialias: true,
      });

      applyViewerStyle(controlViewer, pdbText, resolved, "control");
      applyViewerStyle(candidateViewer, pdbText, resolved, "candidate");

      refs.controlViewer = controlViewer;
      refs.candidateViewer = candidateViewer;
      container.__comparisonRefs = refs;

      window.setTimeout(() => {
        try {
          controlViewer.resize();
          controlViewer.zoomTo();
          controlViewer.render();
          candidateViewer.resize();
          candidateViewer.zoomTo();
          candidateViewer.render();
        } catch (error) {
          // Keep the last successful render if resize throws.
        }
      }, 180);

      container.dataset.structureId = resolved.id;
      container.dataset.structurePdbId = resolved.pdbId;
      container.dataset.structureTitle = resolved.title;
      container.dataset.candidateName = resolved.candidateName;
      container.dataset.targetReceptor = resolved.targetReceptor;
      container.dataset.candidateScore = resolved.candidateScore;
      container.dataset.recommendation = resolved.recommendation;
      container.dataset.controlLabel = resolved.controlLabel;
      container.dataset.badgeLabel = resolved.badgeLabel;
      container.dataset.referenceLabel = resolved.referenceLabel;
    } catch (error) {
      fallbackMarkup(container, resolved, error.message);
    }
  }

  async function mount(container) {
    if (!container || container.__proteinViewerMounted) {
      return;
    }
    container.__proteinViewerMounted = true;

    await renderStructure(container, {
      id: container.dataset.structureId || DEFAULT_STRUCTURE.id,
      pdbId: container.dataset.structurePdbId || DEFAULT_STRUCTURE.pdbId,
      title: container.dataset.structureTitle || DEFAULT_STRUCTURE.title,
      candidateName: container.dataset.candidateName || DEFAULT_STRUCTURE.candidateName,
      targetReceptor: container.dataset.targetReceptor || DEFAULT_STRUCTURE.targetReceptor,
      candidateScore: container.dataset.candidateScore || DEFAULT_STRUCTURE.candidateScore,
      recommendation: container.dataset.recommendation || DEFAULT_STRUCTURE.recommendation,
      controlLabel: container.dataset.controlLabel || DEFAULT_STRUCTURE.controlLabel,
      badgeLabel: container.dataset.badgeLabel || DEFAULT_STRUCTURE.badgeLabel,
      referenceLabel: container.dataset.referenceLabel || "",
    });
  }

  function updateTextTarget(id, value) {
    if (!id || !value) {
      return;
    }
    const el = document.getElementById(id);
    if (el) {
      el.textContent = value;
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
      pdbId: button.dataset.structurePdbId || container.dataset.structurePdbId || DEFAULT_STRUCTURE.pdbId,
      title: button.dataset.structureTitle || DEFAULT_STRUCTURE.title,
      candidateName: button.dataset.candidateName || container.dataset.candidateName || DEFAULT_STRUCTURE.candidateName,
      targetReceptor: button.dataset.targetReceptor || container.dataset.targetReceptor || DEFAULT_STRUCTURE.targetReceptor,
      candidateScore: button.dataset.candidateScore || container.dataset.candidateScore || DEFAULT_STRUCTURE.candidateScore,
      recommendation: button.dataset.recommendation || container.dataset.recommendation || DEFAULT_STRUCTURE.recommendation,
      controlLabel: button.dataset.controlLabel || container.dataset.controlLabel || DEFAULT_STRUCTURE.controlLabel,
      badgeLabel: button.dataset.badgeLabel || container.dataset.badgeLabel || DEFAULT_STRUCTURE.badgeLabel,
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

  window.ECMOProteinViewer = { mount, mountAll, renderStructure };
})();
