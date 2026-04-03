(function () {
  const MOLSTAR_CSS = "https://unpkg.com/molstar/build/viewer/molstar.css";
  const MOLSTAR_JS = "https://unpkg.com/molstar/build/viewer/molstar.js";
  const DEFAULT_STRUCTURE = {
    id: "2JJS",
    title: "CD47 ectodomain WT bound to SIRPalpha",
    subtitle: "Human CD47-SIRPalpha complex from the ranked candidate family",
  };

  let molstarLoaderPromise = null;

  function ensureMolstarAssets() {
    if (window.molstar && window.molstar.Viewer) {
      return Promise.resolve(window.molstar);
    }

    if (molstarLoaderPromise) {
      return molstarLoaderPromise;
    }

    molstarLoaderPromise = new Promise((resolve, reject) => {
      if (!document.querySelector('link[data-molstar-css="true"]')) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = MOLSTAR_CSS;
        link.dataset.molstarCss = "true";
        document.head.append(link);
      }

      const existingScript = document.querySelector('script[data-molstar-js="true"]');
      if (existingScript) {
        existingScript.addEventListener("load", () => resolve(window.molstar));
        existingScript.addEventListener("error", () => reject(new Error("Failed to load Mol* script.")));
        return;
      }

      const script = document.createElement("script");
      script.src = MOLSTAR_JS;
      script.async = true;
      script.dataset.molstarJs = "true";
      script.onload = () => {
        if (window.molstar && window.molstar.Viewer) {
          resolve(window.molstar);
        } else {
          reject(new Error("Mol* loaded, but the viewer API was not found."));
        }
      };
      script.onerror = () => reject(new Error("Failed to load Mol* assets."));
      document.head.append(script);
    });

    return molstarLoaderPromise;
  }

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

    try {
      await ensureMolstarAssets();
      const viewer = new window.molstar.Viewer(container, {
        layoutIsExpanded: false,
        layoutShowControls: false,
        layoutShowRemoteState: false,
        layoutShowSequence: false,
        layoutShowLog: false,
        viewportShowExpand: false,
        viewportShowSelectionMode: false,
        viewportShowAnimation: true,
        pdbProvider: "rcsb",
      });

      container.__molstarViewer = viewer;

      await viewer.loadPdb(structure.id, {
        representationParams: {
          theme: {
            globalName: "chain-id",
          },
        },
      });

      if (viewer.plugin && viewer.plugin.managers && viewer.plugin.managers.camera) {
        viewer.plugin.managers.camera.reset();
      }

      if (viewer.plugin && viewer.plugin.canvas3d) {
        viewer.plugin.canvas3d.setProps({
          trackball: {
            animate: { name: "spin", params: { speed: 0.6 } },
          },
          renderer: {
            backgroundColor: 0xf6f9ff,
          },
        });
      }
    } catch (error) {
      fallbackMarkup(container, structure);
    }
  }

  function mountAll() {
    document.querySelectorAll("[data-protein-viewer]").forEach((element) => mount(element));
  }

  window.ECMOProteinViewer = { mount, mountAll };
})();
