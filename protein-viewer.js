(function () {
  const DEFAULT_STRUCTURE = {
    id: "2JJS",
    title: "CD47 ectodomain WT bound to SIRPalpha",
    subtitle: "Human CD47-SIRPalpha complex from the ranked candidate family",
  };

  function fallbackMarkup(container, structure) {
    container.innerHTML = "";
    container.style.display = "grid";
    container.style.placeItems = "center";
    container.style.padding = "24px";

    const card = document.createElement("div");
    card.style.maxWidth = "440px";
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
    body.textContent = `Unable to load the interactive 3D viewer right now. This panel is intended to show the real PDB structure ${structure.id} (${structure.title}).`;

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
      subtitle: container.dataset.structureSubtitle || DEFAULT_STRUCTURE.subtitle,
    };

    container.innerHTML = "";
    const iframe = document.createElement("iframe");
    iframe.src = `https://www.rcsb.org/3d-view/${encodeURIComponent(structure.id)}`;
    iframe.title = structure.title;
    iframe.loading = "lazy";
    iframe.referrerPolicy = "no-referrer-when-downgrade";
    iframe.setAttribute("allowfullscreen", "true");
    iframe.style.width = "100%";
    iframe.style.height = "100%";
    iframe.style.border = "0";
    iframe.style.display = "block";
    container.append(iframe);

    const fallbackTimer = window.setTimeout(() => {
      if (!iframe.dataset.loaded) {
        fallbackMarkup(container, structure);
      }
    }, 12000);

    iframe.addEventListener("load", () => {
      iframe.dataset.loaded = "true";
      window.clearTimeout(fallbackTimer);
    });

    iframe.addEventListener("error", () => {
      window.clearTimeout(fallbackTimer);
      fallbackMarkup(container, structure);
    });
  }

  function mountAll() {
    document.querySelectorAll("[data-protein-viewer]").forEach((element) => mount(element));
  }

  window.ECMOProteinViewer = { mount, mountAll };
})();
