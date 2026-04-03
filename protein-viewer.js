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

  async function mount(container) {
    if (!container || container.__proteinViewerMounted) {
      return;
    }
    container.__proteinViewerMounted = true;

    const structure = {
      id: container.dataset.structureId || DEFAULT_STRUCTURE.id,
      title: container.dataset.structureTitle || DEFAULT_STRUCTURE.title,
    };

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

      container.innerHTML = "";
      const viewer = window.$3Dmol.createViewer(container, {
        backgroundColor: "white",
        antialias: true,
      });

      viewer.addModel(pdbText, "pdb");
      viewer.setStyle({}, { cartoon: { colorscheme: "chain" } });
      viewer.zoomTo();
      viewer.render();
      viewer.spin(true);
      container.__viewer = viewer;
    } catch (error) {
      fallbackMarkup(container, structure, error.message);
    }
  }

  function mountAll() {
    document.querySelectorAll("[data-protein-viewer]").forEach((element) => mount(element));
  }

  window.ECMOProteinViewer = { mount, mountAll };
})();
