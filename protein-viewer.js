(function () {
  const DEFAULT_STRUCTURE = {
    id: "2JJS",
    title: "CD47 ectodomain WT bound to SIRPalpha",
  };

  function fallbackMarkup(container, structure, detail) {
    container.innerHTML = "";
    container.style.display = "grid";
    container.style.placeItems = "center";
    container.style.padding = "24px";

    const card = document.createElement("div");
    card.style.maxWidth = "460px";
    card.style.padding = "18px";
    card.style.borderRadius = "18px";
    card.style.background = "rgba(255,255,255,0.82)";
    card.style.border = "1px solid rgba(19, 37, 64, 0.08)";
    card.style.color = "#5e6f88";
    card.style.fontFamily = "Arial, Calibri, sans-serif";
    card.style.lineHeight = "1.55";

    const title = document.createElement("strong");
    title.style.display = "block";
    title.style.marginBottom = "10px";
    title.style.color = "#145df2";
    title.textContent = structure.title;

    const body = document.createElement("p");
    body.style.margin = "0 0 10px";
    body.textContent = detail || `Unable to render the live 3D model for ${structure.id} right now.`;

    const link = document.createElement("a");
    link.href = `https://www.rcsb.org/structure/${structure.id}`;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = `Open PDB ${structure.id} on RCSB`;
    link.style.color = "#0c43af";
    link.style.fontWeight = "700";

    card.append(title, body, link);
    container.append(card);
  }

  async function renderStructure(container, structure) {
    if (!window.$3Dmol || typeof window.$3Dmol.createViewer !== "function") {
      fallbackMarkup(container, structure, "The local 3D viewer library did not load.");
      return;
    }

    try {
      const response = await fetch(`/api/structure?pdb=${encodeURIComponent(structure.id)}`, {
        headers: { Accept: "chemical/x-pdb,text/plain" },
      });
      if (!response.ok) {
        throw new Error(`Structure request failed with status ${response.status}.`);
      }
      const pdbText = await response.text();
      if (!pdbText || !pdbText.trim()) {
        throw new Error("The structure response was empty.");
      }

      let viewer = container.__viewer;
      if (!viewer) {
        container.innerHTML = "";
        viewer = window.$3Dmol.createViewer(container, {
          backgroundColor: "white",
          antialias: true,
        });
        container.__viewer = viewer;
      } else {
        viewer.clear();
      }

      viewer.addModel(pdbText, "pdb");
      viewer.setStyle({}, { cartoon: { colorscheme: "chain" } });
      viewer.zoomTo();
      viewer.render();
      viewer.spin(true);
      container.dataset.structureId = structure.id;
      container.dataset.structureTitle = structure.title;
    } catch (error) {
      fallbackMarkup(container, structure, error.message);
    }
  }

  async function mount(container) {
    if (!container || container.__proteinViewerMounted) {
      return;
    }
    container.__proteinViewerMounted = true;

    await renderStructure(container, {
      id: container.dataset.structureId || DEFAULT_STRUCTURE.id,
      title: container.dataset.structureTitle || DEFAULT_STRUCTURE.title,
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
