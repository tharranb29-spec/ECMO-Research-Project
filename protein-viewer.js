(function () {
  const DEFAULT_STRUCTURE = {
    id: "champion",
    title: "AI champion compared with heparin control",
    candidateName: "Top AI Candidate",
    targetReceptor: "Lead pathway",
    candidateScore: "0.0",
    recommendation: "ADVANCE",
    controlLabel: "Heparin Coating",
    badgeLabel: "No.1 Champion",
  };

  const LEGACY_STRUCTURE_MAP = {
    "2JJS": {
      id: "sirpa-reference",
      title: "CD47 ectodomain WT compared with heparin control",
      candidateName: "CD47 ectodomain WT",
      targetReceptor: "SIRPa",
      candidateScore: "86.3",
      recommendation: "ADVANCE",
      controlLabel: "Heparin Coating",
      badgeLabel: "Reference Example",
    },
    "2VSC": {
      id: "sirpa-variant",
      title: "CD47 variant scaffold compared with heparin control",
      candidateName: "CD47 variant scaffold",
      targetReceptor: "SIRPa",
      candidateScore: "82.2",
      recommendation: "ADVANCE",
      controlLabel: "Heparin Coating",
      badgeLabel: "Variant Scaffold",
    },
    "2WNG": {
      id: "sirpa-receptor",
      title: "SIRPalpha lead compared with heparin control",
      candidateName: "SIRPalpha pathway lead",
      targetReceptor: "SIRPa",
      candidateScore: "82.2",
      recommendation: "ADVANCE",
      controlLabel: "Heparin Coating",
      badgeLabel: "Pathway Lead",
    },
  };

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

  function escapeXml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function clampLabel(text, maxLength) {
    const source = String(text || "");
    if (source.length <= maxLength) {
      return source;
    }
    return `${source.slice(0, Math.max(0, maxLength - 1))}\u2026`;
  }

  function getRecommendationColor(recommendation) {
    const value = String(recommendation || "").toUpperCase();
    if (value === "ADVANCE") {
      return "#1b8f5a";
    }
    if (value === "SECONDARY") {
      return "#a16a00";
    }
    if (value === "REJECT") {
      return "#bf3d2a";
    }
    return "#b06600";
  }

  function getInteractionDescriptors(target) {
    const normalized = normalizeTarget(target);
    if (normalized === "Siglec-9") {
      return {
        pathwayLabel: "Siglec-9 inhibitory receptor lane",
        rightSignal: "Receptor-matched inhibitory engagement",
        rightOutcome: "Predicted ROS / NETs calming",
        leftOutcome: "Broad anticoagulation, weak receptor specificity",
        rightAccent: "#1a78d6",
        rightGlow: "#4ed3b0",
      };
    }

    if (normalized === "SIRPa") {
      return {
        pathwayLabel: "SIRPalpha checkpoint lane",
        rightSignal: "Checkpoint-style immune engagement",
        rightOutcome: "Predicted anti-phagocytic calming",
        leftOutcome: "Generic anticoagulation without checkpoint targeting",
        rightAccent: "#1f8a5f",
        rightGlow: "#f0bf4e",
      };
    }

    return {
      pathwayLabel: "Immune-modulating surface lane",
      rightSignal: "AI-guided ligand targeting",
      rightOutcome: "Predicted inhibitory immune modulation",
      leftOutcome: "Generic control coating behavior",
      rightAccent: "#2459d8",
      rightGlow: "#58b8ff",
    };
  }

  function resolveStructure(structure, container) {
    const legacy = LEGACY_STRUCTURE_MAP[structure.id] || {};
    const merged = {
      ...DEFAULT_STRUCTURE,
      ...legacy,
      ...structure,
    };

    merged.targetReceptor = normalizeTarget(merged.targetReceptor || container.dataset.targetReceptor);
    merged.candidateName = merged.candidateName || container.dataset.candidateName || legacy.candidateName || DEFAULT_STRUCTURE.candidateName;
    merged.candidateScore = String(merged.candidateScore || container.dataset.candidateScore || legacy.candidateScore || DEFAULT_STRUCTURE.candidateScore);
    merged.recommendation = String(merged.recommendation || container.dataset.recommendation || legacy.recommendation || DEFAULT_STRUCTURE.recommendation).toUpperCase();
    merged.controlLabel = merged.controlLabel || container.dataset.controlLabel || legacy.controlLabel || DEFAULT_STRUCTURE.controlLabel;
    merged.badgeLabel = merged.badgeLabel || container.dataset.badgeLabel || legacy.badgeLabel || DEFAULT_STRUCTURE.badgeLabel;
    merged.title = merged.title || legacy.title || DEFAULT_STRUCTURE.title;
    return merged;
  }

  function createSceneMarkup(structure) {
    const descriptor = getInteractionDescriptors(structure.targetReceptor);
    const candidateName = clampLabel(structure.candidateName, 30);
    const badgeLabel = clampLabel(structure.badgeLabel, 18);
    const scoreLabel = structure.candidateScore && structure.candidateScore !== "0.0"
      ? `Score ${structure.candidateScore}`
      : "Score pending";
    const recommendationColor = getRecommendationColor(structure.recommendation);

    return `
      <svg viewBox="0 0 960 540" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
        <defs>
          <linearGradient id="scene-bg" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stop-color="#f9fbff"></stop>
            <stop offset="55%" stop-color="#edf3fb"></stop>
            <stop offset="100%" stop-color="#dfe7f4"></stop>
          </linearGradient>
          <linearGradient id="control-panel" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stop-color="rgba(213, 232, 255, 0.78)"></stop>
            <stop offset="100%" stop-color="rgba(240, 245, 253, 0.98)"></stop>
          </linearGradient>
          <linearGradient id="ai-panel" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stop-color="rgba(237, 246, 255, 0.94)"></stop>
            <stop offset="100%" stop-color="rgba(255, 255, 255, 1)"></stop>
          </linearGradient>
          <linearGradient id="surface-strip" x1="0%" x2="100%" y1="0%" y2="0%">
            <stop offset="0%" stop-color="#6ba7ff"></stop>
            <stop offset="100%" stop-color="#1849b6"></stop>
          </linearGradient>
          <linearGradient id="ai-surface-strip" x1="0%" x2="100%" y1="0%" y2="0%">
            <stop offset="0%" stop-color="${descriptor.rightGlow}"></stop>
            <stop offset="100%" stop-color="${descriptor.rightAccent}"></stop>
          </linearGradient>
          <filter id="scene-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="rgba(16,36,62,0.16)"></feDropShadow>
          </filter>
        </defs>

        <rect x="0" y="0" width="960" height="540" fill="url(#scene-bg)"></rect>
        <rect x="34" y="62" width="388" height="414" rx="32" fill="url(#control-panel)" stroke="rgba(16,36,62,0.08)" filter="url(#scene-shadow)"></rect>
        <rect x="538" y="46" width="388" height="430" rx="34" fill="url(#ai-panel)" stroke="${descriptor.rightAccent}" stroke-opacity="0.18" filter="url(#scene-shadow)"></rect>

        <circle cx="480" cy="270" r="42" fill="#ffffff" stroke="rgba(16,36,62,0.10)"></circle>
        <text x="480" y="262" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="16" font-weight="700" fill="#60708a">AI</text>
        <text x="480" y="286" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="15" font-weight="700" fill="#2459d8">vs CONTROL</text>

        <text x="66" y="108" font-family="Calibri, Arial, sans-serif" font-size="14" font-weight="700" letter-spacing="2.5" fill="#6b7b93">CONTROL VARIABLE</text>
        <text x="66" y="142" font-family="Calibri, Arial, sans-serif" font-size="28" font-weight="700" fill="#22314b">${escapeXml(structure.controlLabel)}</text>
        <text x="66" y="170" font-family="Calibri, Arial, sans-serif" font-size="16" fill="#62738e">Baseline ECMO coating comparator</text>

        <rect x="100" y="212" width="248" height="26" rx="13" fill="rgba(255,255,255,0.56)"></rect>
        <rect x="126" y="178" width="190" height="46" rx="18" fill="rgba(255,255,255,0.32)"></rect>
        <rect x="66" y="364" width="324" height="74" rx="22" fill="rgba(255,255,255,0.76)" stroke="rgba(16,36,62,0.08)"></rect>
        <rect x="82" y="382" width="292" height="18" rx="9" fill="url(#surface-strip)"></rect>
        <rect x="82" y="398" width="292" height="18" rx="9" fill="rgba(24, 73, 182, 0.16)"></rect>
        <path d="M106 381 C106 356, 126 346, 126 320" stroke="#44a6ff" stroke-width="4" fill="none"></path>
        <path d="M144 381 C144 352, 164 340, 164 314" stroke="#44a6ff" stroke-width="4" fill="none"></path>
        <path d="M182 381 C182 354, 202 344, 202 320" stroke="#44a6ff" stroke-width="4" fill="none"></path>
        <path d="M220 381 C220 354, 240 344, 240 318" stroke="#44a6ff" stroke-width="4" fill="none"></path>
        <path d="M258 381 C258 352, 278 338, 278 312" stroke="#44a6ff" stroke-width="4" fill="none"></path>
        <path d="M296 381 C296 356, 316 344, 316 320" stroke="#44a6ff" stroke-width="4" fill="none"></path>
        <circle cx="118" cy="286" r="18" fill="rgba(255,255,255,0.88)" stroke="rgba(16,36,62,0.10)"></circle>
        <circle cx="166" cy="258" r="14" fill="rgba(255,255,255,0.88)" stroke="rgba(16,36,62,0.10)"></circle>
        <circle cx="214" cy="296" r="16" fill="rgba(255,255,255,0.88)" stroke="rgba(16,36,62,0.10)"></circle>
        <circle cx="272" cy="262" r="15" fill="rgba(255,255,255,0.88)" stroke="rgba(16,36,62,0.10)"></circle>
        <circle cx="324" cy="292" r="14" fill="rgba(255,255,255,0.88)" stroke="rgba(16,36,62,0.10)"></circle>
        <path d="M118 304 C118 324, 126 340, 130 362" stroke="rgba(120, 139, 166, 0.72)" stroke-width="2.4" stroke-dasharray="6 7" fill="none"></path>
        <path d="M214 314 C214 336, 220 346, 224 362" stroke="rgba(120, 139, 166, 0.72)" stroke-width="2.4" stroke-dasharray="6 7" fill="none"></path>
        <path d="M324 306 C324 328, 318 344, 314 362" stroke="rgba(120, 139, 166, 0.72)" stroke-width="2.4" stroke-dasharray="6 7" fill="none"></path>
        <text x="84" y="450" font-family="Calibri, Arial, sans-serif" font-size="15" font-weight="700" fill="#475a78">Heparin control behavior</text>
        <text x="84" y="474" font-family="Calibri, Arial, sans-serif" font-size="14" fill="#62738e">${escapeXml(descriptor.leftOutcome)}</text>

        <rect x="574" y="74" width="158" height="34" rx="17" fill="rgba(255,255,255,0.82)" stroke="rgba(16,36,62,0.08)"></rect>
        <text x="653" y="96" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="14" font-weight="700" letter-spacing="1.6" fill="#667897">AI-SELECTED LIGAND</text>

        <rect x="750" y="64" width="142" height="42" rx="21" fill="rgba(255, 244, 210, 0.96)" stroke="rgba(225,164,44,0.28)"></rect>
        <text x="821" y="90" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="14" font-weight="700" fill="#9a6400">${escapeXml(badgeLabel)}</text>

        <text x="570" y="144" font-family="Calibri, Arial, sans-serif" font-size="30" font-weight="700" fill="#1e2f4b">${escapeXml(candidateName)}</text>
        <text x="570" y="174" font-family="Calibri, Arial, sans-serif" font-size="16" fill="#62738e">${escapeXml(descriptor.pathwayLabel)}</text>
        <text x="570" y="202" font-family="Calibri, Arial, sans-serif" font-size="16" fill="${recommendationColor}">${escapeXml(scoreLabel)} • ${escapeXml(structure.recommendation)}</text>

        <rect x="572" y="350" width="320" height="84" rx="24" fill="rgba(255,255,255,0.84)" stroke="rgba(16,36,62,0.08)"></rect>
        <rect x="590" y="372" width="286" height="20" rx="10" fill="url(#ai-surface-strip)"></rect>
        <rect x="590" y="390" width="286" height="22" rx="11" fill="rgba(36, 89, 216, 0.12)"></rect>
        <circle cx="624" cy="370" r="8" fill="${descriptor.rightGlow}"></circle>
        <circle cx="676" cy="370" r="8" fill="${descriptor.rightGlow}"></circle>
        <circle cx="728" cy="370" r="8" fill="${descriptor.rightGlow}"></circle>
        <circle cx="780" cy="370" r="8" fill="${descriptor.rightGlow}"></circle>
        <circle cx="832" cy="370" r="8" fill="${descriptor.rightGlow}"></circle>
        <path d="M624 368 C624 330, 634 286, 670 248" stroke="${descriptor.rightAccent}" stroke-width="4" fill="none"></path>
        <path d="M676 368 C676 328, 686 284, 716 240" stroke="${descriptor.rightAccent}" stroke-width="4" fill="none"></path>
        <path d="M728 368 C728 326, 734 284, 760 240" stroke="${descriptor.rightAccent}" stroke-width="4" fill="none"></path>
        <path d="M780 368 C780 328, 786 286, 812 248" stroke="${descriptor.rightAccent}" stroke-width="4" fill="none"></path>

        <ellipse cx="742" cy="228" rx="122" ry="60" fill="rgba(255,255,255,0.86)" stroke="rgba(16,36,62,0.08)"></ellipse>
        <path d="M666 228 C676 214, 690 214, 700 228" stroke="${descriptor.rightGlow}" stroke-width="6" fill="none"></path>
        <path d="M728 228 C738 212, 752 212, 762 228" stroke="${descriptor.rightGlow}" stroke-width="6" fill="none"></path>
        <path d="M790 228 C800 214, 814 214, 824 228" stroke="${descriptor.rightGlow}" stroke-width="6" fill="none"></path>
        <path d="M700 228 C700 252, 690 262, 680 274" stroke="${descriptor.rightAccent}" stroke-width="4" fill="none"></path>
        <path d="M762 228 C762 252, 754 262, 746 274" stroke="${descriptor.rightAccent}" stroke-width="4" fill="none"></path>
        <path d="M824 228 C824 252, 816 262, 808 274" stroke="${descriptor.rightAccent}" stroke-width="4" fill="none"></path>

        <rect x="570" y="452" width="148" height="34" rx="17" fill="rgba(36, 89, 216, 0.10)" stroke="rgba(36, 89, 216, 0.14)"></rect>
        <rect x="728" y="452" width="156" height="34" rx="17" fill="rgba(17, 122, 77, 0.10)" stroke="rgba(17, 122, 77, 0.14)"></rect>
        <text x="644" y="474" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="13.5" font-weight="700" fill="${descriptor.rightAccent}">${escapeXml(descriptor.rightSignal)}</text>
        <text x="806" y="474" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="13.5" font-weight="700" fill="#1b8f5a">${escapeXml(descriptor.rightOutcome)}</text>

        <path d="M422 270 C442 250, 454 244, 462 244" stroke="rgba(120,139,166,0.48)" stroke-width="2.6" stroke-dasharray="7 8" fill="none"></path>
        <path d="M498 244 C512 244, 522 248, 536 264" stroke="${descriptor.rightAccent}" stroke-width="3.2" fill="none"></path>
        <text x="480" y="326" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="14" font-weight="700" fill="#62738e">Control benchmark</text>
        <text x="480" y="346" text-anchor="middle" font-family="Calibri, Arial, sans-serif" font-size="14" font-weight="700" fill="${descriptor.rightAccent}">AI-guided surface interaction</text>
      </svg>
    `;
  }

  function renderStructure(container, structure) {
    const resolved = resolveStructure(structure, container);
    container.innerHTML = createSceneMarkup(resolved);
    container.style.display = "block";
    container.style.padding = "0";
    container.dataset.structureId = resolved.id;
    container.dataset.structureTitle = resolved.title;
    container.dataset.candidateName = resolved.candidateName;
    container.dataset.targetReceptor = resolved.targetReceptor;
    container.dataset.candidateScore = resolved.candidateScore;
    container.dataset.recommendation = resolved.recommendation;
    container.dataset.controlLabel = resolved.controlLabel;
    container.dataset.badgeLabel = resolved.badgeLabel;
  }

  function mount(container) {
    if (!container || container.__proteinViewerMounted) {
      return;
    }
    container.__proteinViewerMounted = true;

    renderStructure(container, {
      id: container.dataset.structureId || DEFAULT_STRUCTURE.id,
      title: container.dataset.structureTitle || DEFAULT_STRUCTURE.title,
      candidateName: container.dataset.candidateName || DEFAULT_STRUCTURE.candidateName,
      targetReceptor: container.dataset.targetReceptor || DEFAULT_STRUCTURE.targetReceptor,
      candidateScore: container.dataset.candidateScore || DEFAULT_STRUCTURE.candidateScore,
      recommendation: container.dataset.recommendation || DEFAULT_STRUCTURE.recommendation,
      controlLabel: container.dataset.controlLabel || DEFAULT_STRUCTURE.controlLabel,
      badgeLabel: container.dataset.badgeLabel || DEFAULT_STRUCTURE.badgeLabel,
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
