(function () {
  const FEATURE_LABELS = {
    affinity_strength_score: "Affinity",
    specificity_score: "Specificity",
    functional_immunomodulation_score: "Immune Effect",
    surface_validation_score: "Surface Support",
    conjugation_feasibility_score: "Conjugation",
    hemocompatibility_proxy_score: "Hemocompatibility",
    multivalency_or_clustering_score: "Clustering",
    literature_confidence_score: "Literature Confidence",
  };

  const bundle = window.ECMO_DASHBOARD_DATA || {};
  const config = bundle.config || {};
  const datasets = {
    seed: bundle.seed || null,
    custom: bundle.custom || null,
    autonomous: bundle.autonomous || null,
  };

  const datasetButtons = Array.from(document.querySelectorAll("[data-dataset]"));
  const viewButtons = Array.from(document.querySelectorAll("[data-view]"));
  const quickPrompts = Array.from(document.querySelectorAll("[data-prompt]"));
  const homeView = document.getElementById("home-view");
  const overviewView = document.getElementById("overview-view");
  const autonomousView = document.getElementById("autonomous-view");
  const structureView = document.getElementById("structure-view");
  const assistantView = document.getElementById("assistant-view");
  const settingsView = document.getElementById("settings-view");
  const workspaceTopbar = document.getElementById("workspace-topbar");
  const metaRow = document.getElementById("meta-row");
  const statsGrid = document.getElementById("stats-grid");
  const leaderboard = document.getElementById("leaderboard");
  const directoryGrid = document.getElementById("directory-grid");
  const targetSections = document.getElementById("target-sections");
  const weightsPanel = document.getElementById("weights-panel");
  const researchLeadsPanel = document.getElementById("research-leads");
  const researchRuntimeGrid = document.getElementById("research-runtime-grid");
  const researchRuntimeChips = document.getElementById("research-runtime-chips");
  const researchRefreshButton = document.getElementById("research-refresh-button");
  const promotedOverviewSection = document.getElementById("promoted-overview-section");
  const promotedCandidateBoard = document.getElementById("promoted-candidate-board");
  const promotedOverviewCopy = document.getElementById("promoted-overview-copy");
  const assistantSideHits = document.getElementById("assistant-side-hits");
  const searchInput = document.getElementById("search-input");
  const assistantMessages = document.getElementById("assistant-messages");
  const assistantStatus = document.getElementById("assistant-status");
  const assistantModeChip = document.getElementById("assistant-mode-chip");
  const assistantDatasetChip = document.getElementById("assistant-dataset-chip");
  const assistantHistoryChip = document.getElementById("assistant-history-chip");
  const briefingDatasetValue = document.getElementById("briefing-dataset-value");
  const briefingDatasetCopy = document.getElementById("briefing-dataset-copy");
  const briefingDatasetChip = document.getElementById("briefing-dataset-chip");
  const briefingHitValue = document.getElementById("briefing-hit-value");
  const briefingHitCopy = document.getElementById("briefing-hit-copy");
  const briefingHitChip = document.getElementById("briefing-hit-chip");
  const briefingAssistantValue = document.getElementById("briefing-assistant-value");
  const briefingAssistantCopy = document.getElementById("briefing-assistant-copy");
  const briefingAssistantChip = document.getElementById("briefing-assistant-chip");
  const briefingResearchValue = document.getElementById("briefing-research-value");
  const briefingResearchCopy = document.getElementById("briefing-research-copy");
  const briefingResearchChip = document.getElementById("briefing-research-chip");
  const contextInput = document.getElementById("context-input");
  const questionInput = document.getElementById("question-input");
  const askButton = document.getElementById("ask-button");
  const openStructureWindowButton = document.getElementById("open-structure-window");
  const logoutButton = document.getElementById("logout-button");
  const sessionGreetingCard = document.getElementById("session-greeting-card");
  const sessionGreetingText = document.getElementById("session-greeting-text");
  const sessionGreetingSubtext = document.getElementById("session-greeting-subtext");
  const homeBrandLogo = document.getElementById("home-brand-logo");
  const homeBrandInstitution = document.getElementById("home-brand-institution");
  const homeBrandProgram = document.getElementById("home-brand-program");
  const homeMissionCopy = document.getElementById("home-mission-copy");
  const settingsSignalGrid = document.getElementById("settings-signal-grid");
  const settingsAlertBox = document.getElementById("settings-alert-box");
  const settingsSessionNote = document.getElementById("settings-session-note");

  let activeDataset = datasets.seed ? "seed" : datasets.autonomous ? "autonomous" : datasets.custom ? "custom" : "seed";
  let activeView = "home";
  let activeSearch = "";
  const histories = { seed: [], custom: [], autonomous: [] };
  const autoResearch = {
    enabled: Boolean((bundle.research_runtime && bundle.research_runtime.auto_research_enabled) || (bundle.research_status && bundle.research_status.auto_research_enabled)),
    intervalSeconds: 3600,
    runtime: bundle.research_runtime || null,
  };
  const liveAssistant = {
    checked: false,
    connected: false,
    provider: null,
    model: null,
  };
  const authState = {
    mode: "none",
    appLoginEnabled: false,
    sessionUser: null,
  };
  let bundlePollingStarted = false;
  let autonomousWatchdogStarted = false;

  const viewPanels = {
    home: homeView,
    overview: overviewView,
    autonomous: autonomousView,
    structure: structureView,
    assistant: assistantView,
    settings: settingsView,
  };

  function normalize(text) {
    return (text || "")
      .toLowerCase()
      .replace(/α/g, "a")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function clear(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function receptorClass(target) {
    return target === "Siglec-9" ? "siglec" : "sirpa";
  }

  function scoreClass(label) {
    return ["advance", "secondary", "hold", "reject"].includes(label) ? label : "hold";
  }

  function datasetLabel(datasetKey) {
    if (datasetKey === "custom") {
      return "Custom candidates";
    }
    if (datasetKey === "autonomous") {
      return "Autonomous discovery";
    }
    return "Seed dataset";
  }

  function viewLabel(viewName) {
    if (viewName === "home") {
      return "Home";
    }
    if (viewName === "assistant") {
      return "Live assistant";
    }
    if (viewName === "autonomous") {
      return "Autonomous discovery";
    }
    if (viewName === "structure") {
      return "Structure review";
    }
    if (viewName === "settings") {
      return "Settings";
    }
    return "Review board";
  }

  function createTimestampLabel() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function updateAssistantChrome() {
    if (assistantDatasetChip) {
      assistantDatasetChip.textContent = datasetLabel(activeDataset);
    }

    if (assistantHistoryChip) {
      const questionCount = histories[activeDataset].filter((item) => item.role === "user").length;
      assistantHistoryChip.textContent = `${questionCount} turn${questionCount === 1 ? "" : "s"}`;
    }

    if (assistantModeChip) {
      const label = liveAssistant.connected
        ? "Live assistant"
        : liveAssistant.checked
          ? "Static fallback"
          : "Checking live mode";
      assistantModeChip.textContent = label;
      assistantModeChip.classList.remove("primary", "warning");
      assistantModeChip.classList.add(liveAssistant.connected ? "primary" : "warning");
    }

    renderBriefing(getFilteredRows(activeDataset));
  }

  function createMetaChip(text) {
    const chip = document.createElement("span");
    chip.className = "meta-chip";
    chip.textContent = text;
    return chip;
  }

  function setBranding() {
    const setText = (id, value, fallback) => {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = value || fallback;
      }
    };

    const logo = document.getElementById("brand-logo");
    setText("brand-institution", config.institution_name, "University Research Group");
    setText("brand-program", config.program_name, "Biomedical AI and Surface Engineering");
    setText("brand-english", config.english_title, config.short_title || "ECMO Research Assistant Dashboard");
    setText("brand-chinese", config.chinese_title, "人工智能驱动的高亲和力配体筛选及其介导的ECMO仿生界面免疫重塑研究");
    setText("brand-note", config.branding_note, "Internal project dashboard for group review, candidate triage, and discussion support.");
    if (logo && config.logo_path) {
      logo.src = config.logo_path;
      logo.alt = `${config.institution_name || "University"} logo`;
    }
    if (homeBrandLogo && config.logo_path) {
      homeBrandLogo.src = config.logo_path;
      homeBrandLogo.alt = `${config.institution_name || "University"} logo`;
    }
    if (homeBrandInstitution) {
      homeBrandInstitution.textContent = config.institution_name || "University Research Group";
    }
    if (homeBrandProgram) {
      homeBrandProgram.textContent = config.program_name || "AI-Driven ECMO Interface Research Project";
    }
    if (homeMissionCopy) {
      homeMissionCopy.textContent = config.mission_statement || "Transform ECMO interface research into a guided decision system that ranks, explains, and continuously discovers immune-modulating ligand candidates suitable for real biomaterial translation.";
    }
  }

  function applyBundlePayload(payload) {
    if (!payload || typeof payload !== "object") {
      return;
    }
    if (payload.config) {
      bundle.config = payload.config;
    }
    if (payload.seed) {
      bundle.seed = payload.seed;
      datasets.seed = payload.seed;
    }
    if (payload.custom) {
      bundle.custom = payload.custom;
      datasets.custom = payload.custom;
    }
    if (payload.autonomous) {
      bundle.autonomous = payload.autonomous;
      datasets.autonomous = payload.autonomous;
    }
    if (payload.autonomous_promoted) {
      bundle.autonomous_promoted = payload.autonomous_promoted;
    }
    if (payload.research_leads) {
      bundle.research_leads = payload.research_leads;
    }
    if (payload.research_status) {
      bundle.research_status = payload.research_status;
    }
    updateAutoResearchState(payload);
    setBranding();
    renderAll();
    updateAssistantChrome();
  }

  function getData(datasetKey) {
    return datasets[datasetKey] || null;
  }

  function getRows(datasetKey) {
    const data = getData(datasetKey);
    return data && Array.isArray(data.ranked) ? data.ranked : [];
  }

  function getResearchStatus() {
    return bundle.research_status || {};
  }

  function getResearchLeads() {
    const payload = bundle.research_leads || {};
    return Array.isArray(payload.leads) ? payload.leads : [];
  }

  function getPromotedAutonomousRows() {
    const payload = bundle.autonomous_promoted || {};
    return Array.isArray(payload.ranked) ? payload.ranked : [];
  }

  function formatDate(value) {
    if (!value) {
      return "n/a";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  }

  function formatInterval(seconds) {
    const numeric = Number(seconds || 0);
    if (!numeric) {
      return "n/a";
    }
    if (numeric % 3600 === 0) {
      const hours = numeric / 3600;
      return `${hours} hour${hours === 1 ? "" : "s"}`;
    }
    if (numeric % 60 === 0) {
      const minutes = numeric / 60;
      return `${minutes} minute${minutes === 1 ? "" : "s"}`;
    }
    return `${numeric} sec`;
  }

  function canUseLiveEndpoints() {
    return window.location.protocol !== "file:";
  }

  function timeGreeting(date) {
    const hour = (date || new Date()).getHours();
    if (hour >= 5 && hour < 12) {
      return "Good morning";
    }
    if (hour >= 12 && hour < 18) {
      return "Good afternoon";
    }
    if (hour >= 18 && hour < 23) {
      return "Good evening";
    }
    return "Good night";
  }

  function currentAppPath() {
    return `${window.location.pathname || "/"}${window.location.search || ""}`;
  }

  function redirectToLogin(nextPath) {
    if (!canUseLiveEndpoints()) {
      return;
    }
    const target = nextPath || currentAppPath();
    window.location.href = `/login.html?next=${encodeURIComponent(target)}`;
  }

  function createAuthError() {
    const error = new Error("Login required.");
    error.code = "AUTH_REQUIRED";
    return error;
  }

  async function fetchWithAuth(input, init, nextPath) {
    const response = await fetch(input, init);
    if (response.status === 401) {
      redirectToLogin(nextPath);
      throw createAuthError();
    }
    return response;
  }

  function updateAuthChrome() {
    if (logoutButton) {
      logoutButton.hidden = !(authState.appLoginEnabled && canUseLiveEndpoints());
      logoutButton.textContent = authState.sessionUser ? `Sign Out ${authState.sessionUser.display_name || authState.sessionUser.username}` : "Sign Out";
    }

    if (!sessionGreetingCard || !sessionGreetingText || !sessionGreetingSubtext) {
      return;
    }
    const visible = Boolean(authState.appLoginEnabled && authState.sessionUser);
    sessionGreetingCard.hidden = !visible;
    if (!visible) {
      return;
    }
    const displayName = authState.sessionUser.display_name || authState.sessionUser.username || "Research User";
    sessionGreetingText.textContent = `${timeGreeting(new Date())}, ${displayName}.`;
    sessionGreetingSubtext.textContent = `Signed in as ${authState.sessionUser.username} for the ECMO research workspace.`;
  }

  function updateAutoResearchState(payload) {
    if (!payload || typeof payload !== "object") {
      return;
    }
    if (typeof payload.auto_research_enabled === "boolean") {
      autoResearch.enabled = payload.auto_research_enabled;
    }
    if (typeof payload.auto_research_interval_seconds === "number") {
      autoResearch.intervalSeconds = payload.auto_research_interval_seconds;
    }
    if (payload.research_runtime) {
      autoResearch.runtime = payload.research_runtime;
    }
  }

  function getAutoResearchRuntime() {
    return autoResearch.runtime || bundle.research_runtime || {};
  }

  function getAutoResearchStatus() {
    return bundle.research_status || {};
  }

  function runtimeHealthClass(health) {
    if (health === "ok") {
      return "ok";
    }
    if (health === "warning") {
      return "warning";
    }
    return "error";
  }

  function humanizeRuntimeState(runtime) {
    if (!runtime) {
      return "Unavailable";
    }
    if (runtime.in_progress) {
      return "Running now";
    }
    if (runtime.last_error) {
      return "Needs attention";
    }
    if (runtime.last_success_at) {
      return "Healthy";
    }
    return "Waiting";
  }

  function describeAge(value) {
    if (!value) {
      return "n/a";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    const diff = Math.max(0, Date.now() - date.getTime());
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    if (days > 0) {
      return `${days} day${days === 1 ? "" : "s"} ago`;
    }
    if (hours > 0) {
      return `${hours} hour${hours === 1 ? "" : "s"} ago`;
    }
    if (minutes > 0) {
      return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
    }
    return "just now";
  }

  function parseDateMs(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date.getTime();
  }

  function startAutonomousWatchdog() {
    if (autonomousWatchdogStarted) {
      return;
    }
    autonomousWatchdogStarted = true;

    const tick = () => {
      if (!canUseLiveEndpoints()) {
        return;
      }
      const runtime = getAutoResearchRuntime();
      const status = getAutoResearchStatus();
      if (!autoResearch.enabled || runtime.in_progress) {
        return;
      }

      const lastSuccess = runtime.last_success_at || status.last_updated;
      const lastSuccessMs = parseDateMs(lastSuccess);
      if (!lastSuccessMs) {
        refreshAutonomousResearch();
        return;
      }

      const ageMs = Date.now() - lastSuccessMs;
      const targetMs = Math.max(60, Number(runtime.interval_seconds || autoResearch.intervalSeconds || 3600)) * 1000;
      if (ageMs >= targetMs && !researchRefreshButton?.disabled) {
        refreshAutonomousResearch();
      }
    };

    tick();
    setInterval(tick, 300000);
  }

  function renderResearchRuntime() {
    if (!researchRuntimeGrid) {
      return;
    }
    clear(researchRuntimeGrid);
    const runtime = getAutoResearchRuntime();
    const status = getAutoResearchStatus();
    const intervalLabel = formatInterval(runtime.interval_seconds || autoResearch.intervalSeconds || 3600);
    const nextRunLabel = runtime.next_run_at ? formatDate(runtime.next_run_at) : "n/a";
    const lastSuccessLabel = runtime.last_success_at || status.last_updated || null;
    const health = status.health || (runtime.last_error ? "error" : runtime.in_progress ? "warning" : "ok");
    const chips = [
      { text: autoResearch.enabled ? "Auto research enabled" : "Auto research disabled", health: null },
      { text: canUseLiveEndpoints() ? "Live sync available" : "Static bundle mode", health: null },
      { text: runtime.llm_enabled ? "DeepSeek discovery on" : "Heuristic discovery only", health: null },
      { text: `Refresh every ${intervalLabel}`, health: null },
      { text: status.using_cached_results ? "Showing cached leads" : "Fresh discovery snapshot", health: status.using_cached_results ? "warning" : "ok" },
      { text: `${status.new_article_count || 0} new articles`, health: null },
      { text: `${status.new_lead_count || 0} new leads`, health: null },
      { text: health === "ok" ? "Health ok" : health === "warning" ? "Health warning" : "Health error", health },
    ];

    if (researchRuntimeChips) {
      clear(researchRuntimeChips);
      chips.forEach((chipData) => {
        const chip = document.createElement("span");
        chip.className = `research-chip ${chipData.health ? runtimeHealthClass(chipData.health) : ""}`.trim();
        chip.textContent = chipData.text;
        researchRuntimeChips.append(chip);
      });
    }

    if (researchRefreshButton) {
      researchRefreshButton.disabled = Boolean(runtime.in_progress) || !autoResearch.enabled || !canUseLiveEndpoints();
      if (runtime.in_progress) {
        researchRefreshButton.textContent = "Refreshing...";
      } else if (!canUseLiveEndpoints()) {
        researchRefreshButton.textContent = "Run on Live Server";
      } else {
        researchRefreshButton.textContent = "Refresh Now";
      }
    }

    const cards = [
      [
        "Health",
        humanizeRuntimeState(runtime),
        status.using_cached_results
          ? "The latest refresh could not reach the literature endpoints, so the dashboard is preserving the last successful discovery snapshot."
          : runtime.last_error
            ? runtime.last_error
          : health === "ok"
            ? "Autonomous discovery is producing fresh leads and the dashboard should refresh automatically."
            : health === "warning"
              ? "A refresh is running or a partial issue was reported. Check the status alert below."
              : "Autonomous discovery has not produced a clean successful update yet.",
      ],
      [
        "Last data update",
        lastSuccessLabel ? formatDate(lastSuccessLabel) : "No successful update yet",
        lastSuccessLabel
          ? `${describeAge(lastSuccessLabel)}${status.using_cached_results ? " (cached snapshot still active)" : ""}`
          : "Waiting for the first successful discovery cycle.",
      ],
      [
        "Last attempt",
        status.last_attempted_at ? formatDate(status.last_attempted_at) : "No refresh attempt yet",
        status.last_attempted_at ? describeAge(status.last_attempted_at) : "No autonomous refresh attempt has been recorded.",
      ],
      [
        "Next run",
        nextRunLabel,
        runtime.in_progress ? "A refresh is already running." : `Scheduled refresh cadence: ${intervalLabel}.`,
      ],
      [
        "Lead counts",
        `${status.lead_count || 0} leads`,
        `${status.article_count || 0} articles screened, ${status.relevant_article_count || 0} judged discovery-relevant${status.llm_lead_count ? `, ${status.llm_lead_count} DeepSeek leads` : ""}.`,
      ],
      [
        "What changed",
        `${status.new_article_count || 0} new articles / ${status.new_lead_count || 0} new leads`,
        status.new_lead_names && status.new_lead_names.length
          ? `Newest leads: ${status.new_lead_names.join(", ")}.`
          : status.using_cached_results
            ? "The latest attempt fell back to the last successful dataset because live literature retrieval was unavailable."
          : status.new_article_count
            ? "Fresh articles were found, but no brand-new candidate lead passed the ranking filters this cycle."
            : "No newly surfaced articles or candidate leads compared with the previous cycle.",
      ],
    ];

    cards.forEach(([label, value, copy]) => {
      const card = document.createElement("article");
      card.className = "research-runtime-card";
      const labelNode = document.createElement("div");
      labelNode.className = "research-runtime-label";
      labelNode.textContent = label;
      const valueNode = document.createElement("div");
      valueNode.className = "research-runtime-value";
      valueNode.textContent = value;
      const copyNode = document.createElement("p");
      copyNode.className = "research-runtime-copy";
      copyNode.textContent = copy;
      card.append(labelNode, valueNode, copyNode);
      researchRuntimeGrid.append(card);
    });
  }

  function renderResearchRuntimeAlert() {
    const status = getAutoResearchStatus();
    const runtime = getAutoResearchRuntime();
    const runtimeState = runtime.last_error
      ? "error"
      : runtime.in_progress
        ? "warning"
        : status.health === "warning"
          ? "warning"
          : "info";
    let alert = document.querySelector(".research-runtime-alert");
    if (!alert) {
      alert = document.createElement("div");
      alert.className = "research-runtime-alert info";
      const parent = researchRuntimeGrid ? researchRuntimeGrid.parentElement : null;
      if (parent) {
        parent.insertBefore(alert, researchRuntimeGrid.nextSibling);
      }
    }
    alert.className = `research-runtime-alert ${runtimeState}`;
    const lastUpdate = status.last_updated ? formatDate(status.last_updated) : "n/a";
    const nextRun = runtime.next_run_at ? formatDate(runtime.next_run_at) : "n/a";
    const errorText = runtime.last_error || (Array.isArray(status.errors) && status.errors.length ? status.errors[0] : "");
    const modeText = runtime.llm_enabled
      ? "DeepSeek-assisted discovery is enabled for literature extraction."
      : "The updater is running in heuristic mode only.";
    const hostingText = canUseLiveEndpoints()
      ? "If your hosting service sleeps idle apps, reopening the dashboard will trigger a catch-up refresh."
      : "Open the dashboard through the live server to enable automatic refreshes and manual discovery runs.";
    const stateText = runtime.in_progress
      ? "A discovery cycle is currently running."
      : status.health === "warning"
        ? "The last cycle completed with warnings."
        : status.health === "error"
          ? "The last cycle reported an error."
          : "The last cycle completed cleanly.";
    const freshnessText = status.new_article_count || status.new_lead_count
      ? ` It surfaced ${status.new_article_count || 0} new articles and ${status.new_lead_count || 0} new leads in the latest cycle.`
      : " No brand-new articles or leads were added in the latest cycle.";
    const cacheText = status.using_cached_results
      ? ` The dashboard is currently showing the last successful discovery snapshot from ${lastUpdate}.`
      : "";
    alert.textContent = `${stateText} Last successful update: ${lastUpdate}. Next run: ${nextRun}. ${modeText}${freshnessText}${cacheText} ${hostingText}${errorText ? ` Latest issue: ${errorText}` : ""}`;
  }

  function setResearchRuntimeAlert(message, tone = "info") {
    let alert = document.querySelector(".research-runtime-alert");
    if (!alert) {
      renderResearchRuntimeAlert();
      alert = document.querySelector(".research-runtime-alert");
    }
    if (!alert) {
      return;
    }
    alert.className = `research-runtime-alert ${tone}`;
    alert.textContent = message;
  }

  function renderBriefing(rows) {
    const visibleRows = Array.isArray(rows) ? rows : getFilteredRows(activeDataset);
    const top = visibleRows[0] || null;
    const runtime = getAutoResearchRuntime();
    const status = getAutoResearchStatus();

    if (briefingDatasetValue) {
      briefingDatasetValue.textContent = datasetLabel(activeDataset);
    }
    if (briefingDatasetCopy) {
      briefingDatasetCopy.textContent = activeSearch
        ? `${visibleRows.length} candidates match the current filter for "${activeSearch}".`
        : `${visibleRows.length} visible candidates are currently in scope for review.`;
    }
    if (briefingDatasetChip) {
      briefingDatasetChip.textContent = viewLabel(activeView);
    }

    if (briefingHitValue) {
      briefingHitValue.textContent = top ? top.candidate_name : "No visible candidate";
    }
    if (briefingHitCopy) {
      briefingHitCopy.textContent = top
        ? `${top.target_receptor} • ${top.modality} • score ${top.predicted_score.toFixed(1)}. Current recommendation: ${top.recommendation.toUpperCase()}.`
        : "Adjust filters or switch datasets to surface a candidate in the current workspace.";
    }
    if (briefingHitChip) {
      briefingHitChip.textContent = top ? top.recommendation.toUpperCase() : "Awaiting match";
    }

    const questionCount = histories[activeDataset].filter((item) => item.role === "user").length;
    if (briefingAssistantValue) {
      briefingAssistantValue.textContent = liveAssistant.connected
        ? (liveAssistant.model || liveAssistant.provider || "Live assistant ready")
        : liveAssistant.checked
          ? "Fallback mode"
          : "Checking connection";
    }
    if (briefingAssistantCopy) {
      briefingAssistantCopy.textContent = liveAssistant.connected
        ? `Connected through ${liveAssistant.provider || "API"}${liveAssistant.model ? ` using ${liveAssistant.model}` : ""}. Suitable for broader reasoning and live discussion support.`
        : "The dashboard remains usable in local fallback mode, but broader open-ended reasoning is limited until the live model backend is available.";
    }
    if (briefingAssistantChip) {
      briefingAssistantChip.textContent = `${questionCount} turn${questionCount === 1 ? "" : "s"}`;
    }

    let researchValue = "Waiting";
    if (!autoResearch.enabled) {
      researchValue = "Disabled";
    } else if (runtime.in_progress) {
      researchValue = "Refreshing now";
    } else if (runtime.last_error) {
      researchValue = "Needs attention";
    } else if (runtime.last_success_at || status.last_updated) {
      researchValue = "Healthy";
    }
    if (briefingResearchValue) {
      briefingResearchValue.textContent = researchValue;
    }
    if (briefingResearchCopy) {
      const lastSuccess = runtime.last_success_at || status.last_updated;
      if (!autoResearch.enabled) {
        briefingResearchCopy.textContent = "Autonomous literature discovery is currently disabled for this dashboard session.";
      } else if (status.using_cached_results) {
        briefingResearchCopy.textContent = `The latest refresh attempt could not reach literature sources, so the dashboard is still showing the last successful discovery snapshot from ${describeAge(lastSuccess)}.`;
      } else if (runtime.last_error) {
        briefingResearchCopy.textContent = `Last issue: ${runtime.last_error}. The dashboard will retry on the next refresh window or when the live server is reopened.`;
      } else if (lastSuccess) {
        briefingResearchCopy.textContent = `${status.lead_count || 0} leads from ${status.article_count || 0} articles (${status.new_article_count || 0} new articles, ${status.new_lead_count || 0} new leads this cycle). Last successful update ${describeAge(lastSuccess)} with a ${formatInterval(runtime.interval_seconds || autoResearch.intervalSeconds || 3600)} cadence.`;
      } else {
        briefingResearchCopy.textContent = "Waiting for the first successful autonomous discovery cycle to populate recent literature leads.";
      }
    }
    if (briefingResearchChip) {
      briefingResearchChip.textContent = runtime.llm_enabled ? "DeepSeek assisted" : "Heuristic mode";
    }
  }

  function renderSettingsView() {
    if (settingsSignalGrid) {
      clear(settingsSignalGrid);
      const runtime = getAutoResearchRuntime();
      const status = getAutoResearchStatus();
      const sessionUser = authState.sessionUser;
      const signalCards = [
        {
          label: "Session",
          value: sessionUser ? `${timeGreeting(new Date())}, ${sessionUser.display_name || sessionUser.username}` : "Not identified",
          copy: sessionUser ? `Signed in as ${sessionUser.username}. Session access is active for the ECMO research workspace.` : "Login identity could not be confirmed in the current browser session.",
        },
        {
          label: "Live Assistant",
          value: liveAssistant.connected ? (liveAssistant.model || liveAssistant.provider || "Connected") : (liveAssistant.checked ? "Fallback mode" : "Checking"),
          copy: liveAssistant.connected
            ? `The discussion assistant is connected through ${liveAssistant.provider || "API"}${liveAssistant.model ? ` using ${liveAssistant.model}` : ""}.`
            : "The assistant is not currently connected to the live model backend and will answer in local fallback mode.",
        },
        {
          label: "Autonomous Research",
          value: humanizeRuntimeState(runtime),
          copy: status.last_updated
            ? `Last successful discovery snapshot: ${formatDate(status.last_updated)}. Current cadence: ${formatInterval(runtime.interval_seconds || autoResearch.intervalSeconds || 3600)}.`
            : "No successful autonomous discovery cycle has been recorded yet.",
        },
        {
          label: "Discovery Yield",
          value: `${status.lead_count || 0} leads`,
          copy: `${status.article_count || 0} articles screened, ${status.relevant_article_count || 0} considered relevant, ${status.new_lead_count || 0} new leads in the latest cycle.`,
        },
      ];

      signalCards.forEach((item) => {
        const card = document.createElement("article");
        card.className = "research-runtime-card";
        const label = document.createElement("div");
        label.className = "research-runtime-label";
        label.textContent = item.label;
        const value = document.createElement("div");
        value.className = "research-runtime-value";
        value.textContent = item.value;
        const copy = document.createElement("p");
        copy.className = "research-runtime-copy";
        copy.textContent = item.copy;
        card.append(label, value, copy);
        settingsSignalGrid.append(card);
      });
    }

    if (settingsAlertBox) {
      const runtime = getAutoResearchRuntime();
      const status = getAutoResearchStatus();
      let tone = "info";
      if (runtime.last_error || status.health === "error") {
        tone = "error";
      } else if (runtime.in_progress || status.health === "warning" || status.using_cached_results) {
        tone = "warning";
      }
      settingsAlertBox.className = `research-runtime-alert ${tone}`;
      const parts = [];
      if (runtime.in_progress) {
        parts.push("A discovery cycle is currently running.");
      } else if (status.using_cached_results) {
        parts.push("The latest research refresh fell back to cached discovery results because a live literature source was unavailable.");
      } else if (runtime.last_error || (status.errors && status.errors.length)) {
        parts.push(`Latest issue: ${runtime.last_error || status.errors[0]}`);
      } else {
        parts.push("No active system issue is currently reported by the live research services.");
      }
      if (status.last_updated) {
        parts.push(`Last successful update: ${formatDate(status.last_updated)}.`);
      }
      if (runtime.next_run_at) {
        parts.push(`Next scheduled refresh: ${formatDate(runtime.next_run_at)}.`);
      }
      settingsAlertBox.textContent = parts.join(" ");
    }

    if (settingsSessionNote) {
      const promotedCount = getPromotedAutonomousRows().length;
      settingsSessionNote.textContent = promotedCount
        ? `${promotedCount} autonomous candidate${promotedCount === 1 ? "" : "s"} are currently promoted into the main review workspace.`
        : "No autonomous candidates are currently promoted into the main review workspace.";
    }
  }

  function getFilteredRows(datasetKey) {
    const rows = getRows(datasetKey);
    if (!activeSearch) {
      return rows.slice();
    }
    const query = normalize(activeSearch);
    return rows.filter((row) => {
      const haystack = normalize(
        [
          row.candidate_name,
          row.target_receptor,
          row.modality,
          row.recommendation,
          row.explanation,
          row.evidence_summary,
        ].join(" ")
      );
      return haystack.includes(query);
    });
  }

  function setView(viewName) {
    activeView = viewName;
    viewButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.view === viewName);
    });
    if (workspaceTopbar) {
      workspaceTopbar.hidden = viewName === "home";
      workspaceTopbar.setAttribute("aria-hidden", viewName === "home" ? "true" : "false");
    }
    Object.entries(viewPanels).forEach(([name, panel]) => {
      if (!panel) {
        return;
      }
      const showing = name === viewName;
      panel.classList.toggle("active", showing);
      panel.hidden = !showing;
      panel.setAttribute("aria-hidden", showing ? "false" : "true");
    });
  }

  function renderMeta(rows) {
    clear(metaRow);
    metaRow.append(
      createMetaChip(
        activeDataset === "seed"
          ? "Showing seed literature set"
          : activeDataset === "custom"
            ? "Showing custom candidate set"
            : "Showing autonomous discovery set"
      ),
      createMetaChip(`${rows.length} visible candidate${rows.length === 1 ? "" : "s"}`)
    );
    if (rows[0]) {
      metaRow.append(createMetaChip(`Top visible hit: ${rows[0].candidate_name}`));
    }
    if (activeSearch) {
      metaRow.append(createMetaChip(`Filtered by: ${activeSearch}`));
    }
    const researchStatus = getResearchStatus();
    if (researchStatus.last_updated) {
      metaRow.append(createMetaChip(`Research updated: ${formatDate(researchStatus.last_updated)}`));
    }
    const promotedCount = getPromotedAutonomousRows().length;
    if (promotedCount && activeView === "overview") {
      metaRow.append(createMetaChip(`${promotedCount} autonomous promotion${promotedCount === 1 ? "" : "s"} on main review`));
    }
  }

  function renderStats(rows) {
    clear(statsGrid);
    const top = rows[0];
    const targetCount = new Set(rows.map((row) => row.target_receptor)).size;
    const advanceCount = rows.filter((row) => row.recommendation === "advance").length;
    const meanScore = rows.length ? (rows.reduce((sum, row) => sum + row.predicted_score, 0) / rows.length).toFixed(1) : "0.0";

    const stats = [
      ["Visible Candidates", String(rows.length)],
      ["Targets Covered", String(targetCount)],
      ["Top Visible Candidate", top ? top.candidate_name : "n/a"],
      [activeSearch ? "Mean Visible Score" : "Advance Tier", activeSearch ? meanScore : String(advanceCount)],
    ];

    stats.forEach(([label, value]) => {
      const card = document.createElement("article");
      card.className = "stat";
      const p = document.createElement("p");
      p.className = "stat-label";
      p.textContent = label;
      const h = document.createElement("h2");
      h.className = "stat-value";
      h.textContent = value;
      card.append(p, h);
      statsGrid.append(card);
    });
  }

  function populateCandidateCard(container, row) {
    const card = document.createElement("article");
    card.className = `candidate-card ${receptorClass(row.target_receptor)}`;

    const top = document.createElement("div");
    top.className = "candidate-top";

    const left = document.createElement("div");
    const title = document.createElement("h3");
    title.className = "candidate-title";
    title.textContent = row.candidate_name;
    const sub = document.createElement("p");
    sub.className = "candidate-sub";
    sub.textContent = `${row.target_receptor} • ${row.modality}`;
    left.append(title, sub);

    const scoreBlock = document.createElement("div");
    scoreBlock.className = "score-block";
    const score = document.createElement("p");
    score.className = "score";
    score.textContent = row.predicted_score.toFixed(1);
    const label = document.createElement("p");
    label.className = "score-label";
    label.textContent = row.recommendation.toUpperCase();
    scoreBlock.append(score, label);

    top.append(left, scoreBlock);

    const bar = document.createElement("div");
    bar.className = "bar";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = `${Math.max(4, Math.min(100, row.predicted_score))}%`;
    bar.append(fill);

    const tags = document.createElement("div");
    tags.className = "tag-row";
    if (row.promoted_to_main_view) {
      const promotedTag = document.createElement("span");
      promotedTag.className = "tag advance";
      promotedTag.textContent = "AUTO PROMOTED";
      tags.append(promotedTag);
    }
    const tier = document.createElement("span");
    tier.className = `tag ${scoreClass(row.recommendation)}`;
    tier.textContent = row.recommendation.toUpperCase();
    const target = document.createElement("span");
    target.className = "tag target-tag";
    target.textContent = row.target_receptor;
    tags.append(tier, target);

    const reasoning = document.createElement("p");
    reasoning.className = "candidate-copy";
    reasoning.textContent = row.explanation || "No explanation provided.";

    const evidence = document.createElement("p");
    evidence.className = "candidate-copy";
    evidence.textContent = row.evidence_summary || "No evidence summary provided.";

    card.append(top, bar, tags);
    if (row.promotion_reason) {
      const promotion = document.createElement("p");
      promotion.className = "candidate-copy";
      promotion.textContent = row.promotion_reason;
      card.append(promotion);
    }
    card.append(reasoning, evidence);

    if (Array.isArray(row.source_urls) && row.source_urls.length) {
      const sources = document.createElement("div");
      sources.className = "source-list";
      row.source_urls.forEach((url, index) => {
        const link = document.createElement("a");
        link.href = url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = `Source ${index + 1}`;
        sources.append(link);
      });
      card.append(sources);
    }

    container.append(card);
  }

  function renderLeaderboard(rows) {
    clear(leaderboard);
    const topRows = rows.slice(0, 5);
    if (!topRows.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No candidates match the current search.";
      leaderboard.append(empty);
      return;
    }
    topRows.forEach((row) => populateCandidateCard(leaderboard, row));
  }

  function renderAssistantSideHits(rows) {
    clear(assistantSideHits);
    const topRows = rows.slice(0, 3);
    if (!topRows.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No candidates to show.";
      assistantSideHits.append(empty);
      return;
    }
    topRows.forEach((row) => populateCandidateCard(assistantSideHits, row));
  }

  function renderDirectory(rows) {
    clear(directoryGrid);
    if (!rows.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No candidates match the current search.";
      directoryGrid.append(empty);
      return;
    }

    rows.forEach((row) => {
      const card = document.createElement("article");
      card.className = "directory-card";

      const head = document.createElement("div");
      head.className = "directory-head";
      const left = document.createElement("div");
      const title = document.createElement("h4");
      title.className = "directory-title";
      title.textContent = row.candidate_name;
      const sub = document.createElement("div");
      sub.className = "mini-exp";
      sub.textContent = `${row.target_receptor} • ${row.modality}`;
      left.append(title, sub);
      const score = document.createElement("div");
      score.className = "mini-score";
      score.textContent = row.predicted_score.toFixed(1);
      head.append(left, score);

      const tags = document.createElement("div");
      tags.className = "tag-row";
      const tier = document.createElement("span");
      tier.className = `tag ${scoreClass(row.recommendation)}`;
      tier.textContent = row.recommendation.toUpperCase();
      tags.append(tier);

      const summary = document.createElement("p");
      summary.className = "candidate-copy";
      summary.textContent = row.explanation || row.evidence_summary || "No summary available.";

      card.append(head, tags, summary);
      directoryGrid.append(card);
    });
  }

  function renderTargetSections(rows) {
    clear(targetSections);
    if (!rows.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No target-specific rows to show for this filter.";
      targetSections.append(empty);
      return;
    }

    const grouped = rows.reduce((acc, row) => {
      acc[row.target_receptor] = acc[row.target_receptor] || [];
      acc[row.target_receptor].push(row);
      return acc;
    }, {});

    Object.entries(grouped).forEach(([target, targetRows]) => {
      const block = document.createElement("section");
      block.className = "target-block";
      const head = document.createElement("div");
      head.className = `target-head ${receptorClass(target)}`;

      const left = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = target;
      const subtitle = document.createElement("div");
      subtitle.className = "mini-exp";
      subtitle.textContent = `${targetRows.length} visible candidate${targetRows.length === 1 ? "" : "s"}`;
      left.append(title, subtitle);

      const score = document.createElement("div");
      score.className = "mini-score";
      score.textContent = `${targetRows[0].predicted_score.toFixed(1)} top score`;
      head.append(left, score);

      const list = document.createElement("div");
      list.className = "mini-list";
      targetRows.forEach((row) => {
        const item = document.createElement("div");
        item.className = "mini-row";

        const nameBlock = document.createElement("div");
        const name = document.createElement("div");
        name.className = "mini-name";
        name.textContent = row.candidate_name;
        const modality = document.createElement("div");
        modality.className = "mini-exp";
        modality.textContent = row.modality;
        nameBlock.append(name, modality);

        const explanation = document.createElement("div");
        explanation.className = "mini-exp";
        explanation.textContent = row.explanation || "No explanation provided.";

        const rowScore = document.createElement("div");
        rowScore.className = "mini-score";
        rowScore.textContent = row.predicted_score.toFixed(1);

        item.append(nameBlock, explanation, rowScore);
        list.append(item);
      });

      block.append(head, list);
      targetSections.append(block);
    });
  }

  function renderWeights() {
    clear(weightsPanel);
    const data = getData(activeDataset);
    const models = (data && data.models) || {};

    Object.entries(models).forEach(([target, model]) => {
      const block = document.createElement("section");
      block.className = "weight-block";

      const head = document.createElement("div");
      head.className = `target-head ${receptorClass(target)}`;
      const mae = data.metrics && typeof data.metrics[target] === "number" ? data.metrics[target].toFixed(1) : "n/a";
      const title = document.createElement("strong");
      title.textContent = `${target} Weights`;
      const score = document.createElement("div");
      score.className = "mini-score";
      score.textContent = `Validation error: ${mae} pts`;
      head.append(title, score);

      const list = document.createElement("div");
      list.className = "weight-list";
      Object.entries(model.weights || {})
        .sort((a, b) => b[1] - a[1])
        .forEach(([feature, weight]) => {
          const item = document.createElement("div");
          item.className = "weight-item";
          const top = document.createElement("div");
          top.className = "weight-top";
          const featureLabel = document.createElement("span");
          featureLabel.textContent = FEATURE_LABELS[feature] || feature;
          const weightValue = document.createElement("strong");
          weightValue.textContent = weight.toFixed(3);
          top.append(featureLabel, weightValue);
          const bar = document.createElement("div");
          bar.className = "bar";
          const fill = document.createElement("div");
          fill.className = "bar-fill";
          fill.style.width = `${Math.max(4, Math.min(100, weight * 100))}%`;
          bar.append(fill);
          item.append(top, bar);
          list.append(item);
        });

      block.append(head, list);
      weightsPanel.append(block);
    });
  }

  function renderResearchLeads() {
    clear(researchLeadsPanel);
    const leads = getResearchLeads().slice(0, 8);
    const researchStatus = getAutoResearchStatus();
    const runtime = getAutoResearchRuntime();

    if (!leads.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = runtime.in_progress
        ? "The autonomous discovery loop is running right now. Fresh leads should appear once the refresh completes."
        : "No autonomous research leads have been discovered yet. Start the live server and let the background updater run.";
      researchLeadsPanel.append(empty);
      return;
    }

    if (researchStatus.last_updated) {
      const note = document.createElement("div");
      note.className = "empty-state";
      note.textContent = researchStatus.using_cached_results
        ? `The latest autonomous refresh is using the cached discovery snapshot from ${formatDate(researchStatus.last_updated || runtime.last_success_at)} because the literature endpoints were unavailable during the newest attempt.`
        : `Last autonomous research update: ${formatDate(researchStatus.last_updated || runtime.last_success_at)}. Leads discovered: ${researchStatus.lead_count || leads.length}. New this cycle: ${researchStatus.new_lead_count || 0} leads from ${researchStatus.new_article_count || 0} newly surfaced articles.`;
      researchLeadsPanel.append(note);
    }

    leads.forEach((lead) => {
      const block = document.createElement("section");
      block.className = "target-block";
      const head = document.createElement("div");
      head.className = `target-head ${receptorClass(lead.target_receptor)}`;
      const left = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = lead.candidate_name;
      const subtitle = document.createElement("div");
      subtitle.className = "mini-exp";
      subtitle.textContent = `${lead.target_receptor} • ${lead.modality_guess}`;
      left.append(title, subtitle);
      const score = document.createElement("div");
      score.className = "mini-score";
      score.textContent = String(lead.lead_score);
      head.append(left, score);

      const list = document.createElement("div");
      list.className = "weight-list";

      const meta = document.createElement("div");
      meta.className = "lead-meta-row";
      const statusChip = document.createElement("span");
      statusChip.className = `research-chip ${lead.source_method === "deepseek" ? "ok" : ""}`.trim();
      statusChip.textContent = lead.source_method === "deepseek" ? "DeepSeek extracted" : "Heuristic extraction";
      const discoveryChip = document.createElement("span");
      discoveryChip.className = `research-chip ${lead.discovery_status === "known_reference" ? "ok" : "warning"}`;
      discoveryChip.textContent = lead.discovery_status === "known_reference" ? "Known reference" : "New literature lead";
      const freshnessChip = document.createElement("span");
      freshnessChip.className = `research-chip ${lead.is_new ? "ok" : ""}`.trim();
      freshnessChip.textContent = lead.is_new ? "New this cycle" : "Seen previously";
      const dateChip = document.createElement("span");
      dateChip.className = "research-chip";
      dateChip.textContent = lead.publication_date ? formatDate(lead.publication_date) : "No date";
      meta.append(statusChip, discoveryChip, freshnessChip, dateChip);

      const rationale = document.createElement("p");
      rationale.className = "candidate-copy";
      rationale.textContent = lead.rationale || "Literature lead discovered by autonomous update.";

      const source = document.createElement("p");
      source.className = "candidate-copy";
      source.textContent = `Source: ${lead.source_title || "Unknown article"}${lead.publication_date ? ` • ${lead.publication_date}` : ""}`;

      list.append(meta, rationale, source);
      if (lead.source_url) {
        const links = document.createElement("div");
        links.className = "source-list";
        const link = document.createElement("a");
        link.href = lead.source_url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = "Open article";
        links.append(link);
        list.append(links);
      }

      block.append(head, list);
      researchLeadsPanel.append(block);
    });
  }

  function renderPromotedOverview() {
    if (!promotedOverviewSection || !promotedCandidateBoard) {
      return;
    }
    const promotedRows = getPromotedAutonomousRows();
    promotedOverviewSection.hidden = !promotedRows.length;
    clear(promotedCandidateBoard);
    if (!promotedRows.length) {
      if (promotedOverviewCopy) {
        promotedOverviewCopy.textContent = "High-signal candidates elevated by the autonomous literature pipeline for direct review on the main workspace.";
      }
      return;
    }
    const status = getAutoResearchStatus();
    if (promotedOverviewCopy) {
      promotedOverviewCopy.textContent = status.last_updated
        ? `${promotedRows.length} autonomous candidate${promotedRows.length === 1 ? "" : "s"} currently meet promotion criteria and are surfaced here from the latest discovery snapshot (${formatDate(status.last_updated)}).`
        : `${promotedRows.length} autonomous candidate${promotedRows.length === 1 ? "" : "s"} are currently promoted into the main review workspace.`;
    }
    promotedRows.forEach((row) => populateCandidateCard(promotedCandidateBoard, row));
  }

  function renderAll() {
    const rows = getFilteredRows(activeDataset);
    renderPromotedOverview();
    renderBriefing(rows);
    renderMeta(rows);
    renderStats(rows);
    renderLeaderboard(rows);
    renderDirectory(rows);
    renderTargetSections(rows);
    renderWeights();
    renderResearchRuntime();
    renderResearchRuntimeAlert();
    renderResearchLeads();
    renderAssistantSideHits(rows);
    renderSettingsView();
  }

  function findCandidateMatches(question) {
    const rows = getRows(activeDataset);
    const compactQuestion = normalize(question).replace(/\s+/g, "");
    return rows.filter((row) => {
      const compactName = normalize(row.candidate_name).replace(/\s+/g, "");
      return compactName && compactQuestion.includes(compactName);
    });
  }

  function appendInlineMarkdown(container, text) {
    const source = String(text || "");
    const tokenRegex = /(`[^`]+`|\*\*[^*]+?\*\*|__[^_]+?__|<br\s*\/?>)/gi;
    let lastIndex = 0;
    let match;

    while ((match = tokenRegex.exec(source)) !== null) {
      if (match.index > lastIndex) {
        container.append(document.createTextNode(source.slice(lastIndex, match.index)));
      }

      const token = match[0];
      if (/^<br\s*\/?>$/i.test(token)) {
        container.append(document.createElement("br"));
      } else if ((token.startsWith("**") && token.endsWith("**")) || (token.startsWith("__") && token.endsWith("__"))) {
        const strong = document.createElement("strong");
        strong.textContent = token.slice(2, -2);
        container.append(strong);
      } else if (token.startsWith("`") && token.endsWith("`")) {
        const code = document.createElement("code");
        code.textContent = token.slice(1, -1);
        container.append(code);
      }

      lastIndex = tokenRegex.lastIndex;
    }

    if (lastIndex < source.length) {
      container.append(document.createTextNode(source.slice(lastIndex)));
    }
  }

  function isHeadingLine(line) {
    return /^#{1,6}\s+/.test(line);
  }

  function isOrderedListLine(line) {
    return /^\d+\.\s+/.test(line);
  }

  function isBulletListLine(line) {
    return /^[-*•]\s+/.test(line);
  }

  function isTableSeparatorLine(line) {
    return /^[\s|:-]+$/.test(line.trim()) && line.includes("-");
  }

  function splitTableRow(line) {
    return line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim());
  }

  function appendTableBlock(container, lines) {
    if (lines.length < 2 || !lines[0].includes("|") || !isTableSeparatorLine(lines[1])) {
      return false;
    }

    const headerCells = splitTableRow(lines[0]);
    if (!headerCells.length) {
      return false;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "message-table-wrap";

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headerCells.forEach((cell) => {
      const th = document.createElement("th");
      appendInlineMarkdown(th, cell);
      headerRow.append(th);
    });
    thead.append(headerRow);
    table.append(thead);

    const bodyLines = lines.slice(2).filter(Boolean);
    if (bodyLines.length) {
      const tbody = document.createElement("tbody");
      bodyLines.forEach((line) => {
        const row = document.createElement("tr");
        const cells = splitTableRow(line);
        const paddedCells = headerCells.map((_, index) => cells[index] || "");
        paddedCells.forEach((cell) => {
          const td = document.createElement("td");
          appendInlineMarkdown(td, cell);
          row.append(td);
        });
        tbody.append(row);
      });
      table.append(tbody);
    }

    wrapper.append(table);
    container.append(wrapper);
    return true;
  }

  function appendStructuredLines(container, lines) {
    let index = 0;

    while (index < lines.length) {
      const line = lines[index].trim();
      if (!line) {
        index += 1;
        continue;
      }

      if (isHeadingLine(line)) {
        const depth = Math.min(4, Math.max(1, (line.match(/^#+/) || ["#"])[0].length));
        const heading = document.createElement(`h${Math.min(depth + 1, 4)}`);
        appendInlineMarkdown(heading, line.replace(/^#{1,6}\s+/, "").trim());
        container.append(heading);
        index += 1;
        continue;
      }

      if (isOrderedListLine(line)) {
        const ol = document.createElement("ol");
        while (index < lines.length && isOrderedListLine(lines[index].trim())) {
          const li = document.createElement("li");
          appendInlineMarkdown(li, lines[index].trim().replace(/^\d+\.\s+/, ""));
          ol.append(li);
          index += 1;
        }
        container.append(ol);
        continue;
      }

      if (isBulletListLine(line)) {
        const ul = document.createElement("ul");
        while (index < lines.length && isBulletListLine(lines[index].trim())) {
          const li = document.createElement("li");
          appendInlineMarkdown(li, lines[index].trim().replace(/^[-*•]\s+/, ""));
          ul.append(li);
          index += 1;
        }
        container.append(ul);
        continue;
      }

      const paragraphLines = [];
      while (index < lines.length) {
        const current = lines[index].trim();
        if (!current) {
          index += 1;
          break;
        }
        if (isHeadingLine(current) || isOrderedListLine(current) || isBulletListLine(current)) {
          break;
        }
        paragraphLines.push(current);
        index += 1;
      }

      if (paragraphLines.length) {
        const paragraph = document.createElement("p");
        appendInlineMarkdown(paragraph, paragraphLines.join(" "));
        container.append(paragraph);
      }
    }
  }

  function appendFormattedBlock(container, block) {
    const trimmed = block.trim();
    if (!trimmed) {
      return;
    }

    if (trimmed.startsWith("```") && trimmed.endsWith("```")) {
      const pre = document.createElement("pre");
      pre.textContent = trimmed.replace(/^```[a-zA-Z0-9_-]*\n?/, "").replace(/\n?```$/, "");
      container.append(pre);
      return;
    }

    const lines = trimmed.split("\n").map((line) => line.trim());
    if (appendTableBlock(container, lines.filter(Boolean))) {
      return;
    }

    appendStructuredLines(container, lines);
  }

  function createMessageBody(content) {
    const body = document.createElement("div");
    body.className = "message-body";
    const normalized = String(content || "").replace(/\r/g, "").trim();
    if (!normalized) {
      const p = document.createElement("p");
      p.textContent = "No content.";
      body.append(p);
      return body;
    }

    const codeAwareBlocks = normalized.split(/\n\s*\n/);
    codeAwareBlocks.forEach((block) => appendFormattedBlock(body, block));
    return body;
  }

  function createPendingBody() {
    const body = document.createElement("div");
    body.className = "message-body";

    const paragraph = document.createElement("p");
    paragraph.textContent = "Reviewing the current dataset and any pasted context before answering.";

    const dots = document.createElement("div");
    dots.className = "typing-dots";
    dots.append(document.createElement("span"), document.createElement("span"), document.createElement("span"));

    body.append(paragraph, dots);
    return body;
  }

  function createMessageElement(role, content, options = {}) {
    const bubble = document.createElement("div");
    bubble.className = `message ${role}${options.pending ? " pending" : ""}`;

    const meta = document.createElement("div");
    meta.className = "message-meta";

    const label = document.createElement("strong");
    const badge = document.createElement("span");
    badge.className = "message-badge";
    badge.setAttribute("aria-hidden", "true");
    const labelText = document.createElement("span");
    labelText.textContent = role === "user" ? "You" : "Assistant";
    label.append(badge, labelText);

    const time = document.createElement("span");
    time.className = "message-time";
    time.textContent = options.pending ? "Thinking..." : options.timestamp || createTimestampLabel();

    meta.append(label, time);
    bubble.append(meta, options.pending ? createPendingBody() : createMessageBody(content));
    return bubble;
  }

  function addMessage(role, content, options = {}) {
    const bubble = createMessageElement(role, content, options);
    assistantMessages.append(bubble);
    assistantMessages.scrollTop = assistantMessages.scrollHeight;
    updateAssistantChrome();
    return bubble;
  }

  function setAssistantStatus(message, live) {
    assistantStatus.textContent = message;
    assistantStatus.classList.remove("live", "fallback");
    assistantStatus.classList.add(live ? "live" : "fallback");
    updateAssistantChrome();
  }

  function localAnswer(question) {
    const data = getData(activeDataset);
    const rows = data ? data.ranked || [] : [];
    const q = normalize(question);
    const matches = findCandidateMatches(question);

    if (!rows.length) {
      return "No ranking data is loaded for this dataset yet.";
    }

    if ((q.includes("top") || q.includes("best")) && q.includes("siglec")) {
      const row = rows.find((item) => item.target_receptor === "Siglec-9");
      return row
        ? `For Siglec-9, the current top candidate is ${row.candidate_name} with a score of ${row.predicted_score.toFixed(1)} and a ${row.recommendation} recommendation.\n\n- Main rationale: ${row.explanation}\n- Evidence summary: ${row.evidence_summary}`
        : "I could not find a Siglec-9 candidate in the current dataset.";
    }

    if ((q.includes("top") || q.includes("best")) && q.includes("sirp")) {
      const row = rows.find((item) => item.target_receptor === "SIRPa");
      return row
        ? `For SIRPa, the current top candidate is ${row.candidate_name} with a score of ${row.predicted_score.toFixed(1)} and a ${row.recommendation} recommendation.\n\n- Main rationale: ${row.explanation}\n- Evidence summary: ${row.evidence_summary}`
        : "I could not find a SIRPa candidate in the current dataset.";
    }

    if (q.includes("top") || q.includes("best")) {
      const row = rows[0];
      return `The top candidate overall is ${row.candidate_name} for ${row.target_receptor}, scoring ${row.predicted_score.toFixed(1)}.\n\n- Recommendation: ${row.recommendation}\n- Why it stands out: ${row.explanation}`;
    }

    if (q.includes("advance")) {
      const advanceRows = rows.filter((row) => row.recommendation === "advance");
      if (!advanceRows.length) {
        return "There are no advance-tier candidates in the current dataset.";
      }
      return `Advance-tier candidates in the current dataset:\n\n${advanceRows.map((row) => `- ${row.candidate_name} (${row.target_receptor}, ${row.predicted_score.toFixed(1)})`).join("\n")}`;
    }

    if ((q.includes("why") || q.includes("explain")) && matches.length) {
      const row = matches[0];
      return `${row.candidate_name} is currently scored at ${row.predicted_score.toFixed(1)} for ${row.target_receptor}.\n\n- Ranking explanation: ${row.explanation}\n- Evidence summary: ${row.evidence_summary}\n- Recommendation tier: ${row.recommendation}`;
    }

    if (q.includes("compare") && matches.length >= 2) {
      const first = matches[0];
      const second = matches[1];
      const winner = first.predicted_score >= second.predicted_score ? first : second;
      return `Comparison summary:\n\n- ${first.candidate_name}: ${first.predicted_score.toFixed(1)} (${first.recommendation})\n- ${second.candidate_name}: ${second.predicted_score.toFixed(1)} (${second.recommendation})\n- Higher-ranked candidate: ${winner.candidate_name}`;
    }

    if (q.includes("validation") || q.includes("mae") || q.includes("error")) {
      const metrics = data.metrics || {};
      const parts = Object.entries(metrics).map(([target, value]) => `- ${target}: ${value.toFixed(1)} points`);
      return `Current leave-one-out validation error:\n\n${parts.join("\n")}`;
    }

    return "The live backend is not connected, so I can only answer focused dashboard questions in fallback mode.\n\nTry asking about:\n\n- top candidates\n- target-specific leaders\n- advance-tier candidates\n- candidate comparisons\n- validation error";
  }

  async function checkLiveAssistant() {
    try {
      const response = await fetch("/api/status", { headers: { Accept: "application/json" } });
      if (response.status === 401) {
        redirectToLogin(currentAppPath());
        return;
      }
      if (!response.ok) {
        throw new Error("Status endpoint unavailable");
      }
      const payload = await response.json();
      updateAutoResearchState(payload);
      if (payload.research_status) {
        bundle.research_status = payload.research_status;
      }
      if (payload.research_runtime) {
        bundle.research_runtime = payload.research_runtime;
      }
      liveAssistant.checked = true;
      liveAssistant.connected = Boolean(payload.live_assistant_enabled);
      liveAssistant.provider = payload.provider || null;
      liveAssistant.model = payload.model || null;
      authState.appLoginEnabled = Boolean(payload.app_login_enabled);
      authState.mode = payload.auth_mode || "none";
      authState.sessionUser = payload.session_user || null;
      updateAuthChrome();

      if (liveAssistant.connected) {
        setAssistantStatus(`Live assistant connected via ${payload.provider || "API"} / ${payload.model}. Broader questions and reasoning over pasted notes are enabled.`, true);
        startBundlePolling();
      } else {
        setAssistantStatus("Dashboard server detected, but no live model key is configured. Using local fallback answers only.", false);
        startBundlePolling();
      }
    } catch (err) {
      if (err && err.code === "AUTH_REQUIRED") {
        return;
      }
      liveAssistant.checked = true;
      liveAssistant.connected = false;
      authState.sessionUser = null;
      updateAuthChrome();
      setAssistantStatus("Static dashboard mode. Run research_assistant_server.py for the full live assistant.", false);
    }
  }

  async function pollBundle() {
    try {
      const response = await fetchWithAuth("/api/bundle", { headers: { Accept: "application/json" } }, currentAppPath());
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      if (payload.ok) {
        applyBundlePayload(payload);
      }
    } catch (err) {
      if (err && err.code === "AUTH_REQUIRED") {
        return;
      }
      // Ignore polling errors in static mode.
    }
  }

  function startBundlePolling() {
    if (bundlePollingStarted) {
      return;
    }
    bundlePollingStarted = true;
    pollBundle();
    setInterval(pollBundle, 60000);
  }

  async function refreshAutonomousResearch() {
    if (!researchRefreshButton) {
      return;
    }
    if (!canUseLiveEndpoints()) {
      setResearchRuntimeAlert(
        "Autonomous discovery refresh requires the live dashboard server. Open the hosted URL or run research_assistant_server.py first.",
        "warning"
      );
      return;
    }
    const originalLabel = researchRefreshButton.textContent;
    researchRefreshButton.disabled = true;
    researchRefreshButton.textContent = "Refreshing...";
    try {
      const response = await fetchWithAuth("/api/research/refresh", {
        method: "POST",
        headers: { Accept: "application/json" },
      }, currentAppPath());
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || "Manual autonomous refresh failed.");
      }
      updateAutoResearchState(payload);
      if (payload.research_status) {
        bundle.research_status = payload.research_status;
      }
      if (payload.research_runtime) {
        bundle.research_runtime = payload.research_runtime;
      }
      renderAll();
      setResearchRuntimeAlert(
        payload.message || "Autonomous discovery refresh triggered.",
        payload.started ? "info" : "warning"
      );
      if (payload.started) {
        researchRefreshButton.disabled = true;
        const resetRefreshButton = () => {
          const runtime = getAutoResearchRuntime();
          if (runtime.in_progress) {
            setTimeout(resetRefreshButton, 4000);
            return;
          }
          researchRefreshButton.disabled = false;
          researchRefreshButton.textContent = originalLabel;
          pollBundle();
        };
        setTimeout(resetRefreshButton, 4000);
      } else {
        setTimeout(pollBundle, 4000);
      }
    } catch (err) {
      if (err && err.code === "AUTH_REQUIRED") {
        return;
      }
      setResearchRuntimeAlert(`Autonomous refresh could not start: ${err.message}`, "error");
    } finally {
      if (!researchRefreshButton.disabled) {
        researchRefreshButton.textContent = originalLabel;
      }
    }
  }

  async function askLive(question) {
    const history = histories[activeDataset];
    const response = await fetchWithAuth("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset: activeDataset,
        question,
        extra_context: contextInput.value.trim(),
        history,
      }),
    }, currentAppPath());

    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Live assistant request failed.");
    }

    if (payload.provider || payload.model) {
      setAssistantStatus(`Live assistant connected via ${(payload.provider || liveAssistant.provider || "API")} / ${payload.model || liveAssistant.model}.`, true);
    }

    return payload.answer;
  }

  async function handleLogout() {
    if (!canUseLiveEndpoints()) {
      return;
    }
    if (logoutButton) {
      logoutButton.disabled = true;
      logoutButton.textContent = "Signing out...";
    }
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: { Accept: "application/json" },
      });
    } catch (err) {
      // Ignore network issues here and still redirect to the login page.
    } finally {
      redirectToLogin("/");
    }
  }

  async function handleAsk(rawQuestion) {
    const question = String(rawQuestion || "").trim();
    if (!question) {
      return;
    }

    setView("assistant");
    addMessage("user", question);
    histories[activeDataset].push({ role: "user", content: question });
    questionInput.value = "";
    askButton.disabled = true;
    questionInput.disabled = true;
    contextInput.disabled = true;
    askButton.textContent = "Analyzing...";
    const pendingMessage = addMessage("assistant", "", { pending: true });

    try {
      let answer;
      if (liveAssistant.connected) {
        answer = await askLive(question);
      } else {
        answer = localAnswer(question);
      }
      pendingMessage.remove();
      addMessage("assistant", answer);
      histories[activeDataset].push({ role: "assistant", content: answer });
    } catch (err) {
      if (err && err.code === "AUTH_REQUIRED") {
        pendingMessage.remove();
        return;
      }
      pendingMessage.remove();
      const fallback = `${err.message}\n\nFalling back to local dashboard answer:\n\n${localAnswer(question)}`;
      setAssistantStatus("Live assistant request failed. Using local fallback answers.", false);
      addMessage("assistant", fallback);
      histories[activeDataset].push({ role: "assistant", content: fallback });
      liveAssistant.connected = false;
    } finally {
      askButton.disabled = false;
      questionInput.disabled = false;
      contextInput.disabled = false;
      askButton.textContent = "Ask";
      questionInput.focus();
      updateAssistantChrome();
    }
  }

  function resetAssistant() {
    clear(assistantMessages);
    histories[activeDataset] = [];
    const intro = liveAssistant.connected
      ? "Live research assistant is ready.\n\nAsk broader project questions, compare candidates, or paste new docking and assay notes into the context box before asking.\n\n- It can synthesize the current dataset with pasted context.\n- It works best for comparisons, explanations, and next-step planning."
      : "Fallback mode is active.\n\nYou can still ask focused questions about the current ranking results, but broader reasoning will be limited until the live backend is running.\n\n- Ask about top candidates or target-specific leaders.\n- Use the live backend for open-ended scientific reasoning.";
    addMessage("assistant", intro);
    updateAssistantChrome();
  }

  function openStructureWindow() {
    const showcaseUrl = window.location.protocol === "file:" ? "structure-showcase.html" : "/structure-showcase.html";
    const features = "popup=yes,width=1280,height=820,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes";
    const popup = window.open(showcaseUrl, "ecmo-structure-showcase", features);
    if (!popup) {
      window.location.href = showcaseUrl;
    }
  }

  datasetButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeDataset = button.dataset.dataset;
      datasetButtons.forEach((node) => node.classList.toggle("active", node === button));
      renderAll();
      resetAssistant();
    });
  });

  viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setView(button.dataset.view);
    });
  });

  quickPrompts.forEach((button) => {
    button.addEventListener("click", () => handleAsk(button.dataset.prompt));
  });

  searchInput.addEventListener("input", () => {
    activeSearch = searchInput.value.trim();
    renderAll();
  });

  askButton.addEventListener("click", () => handleAsk(questionInput.value));
  questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      handleAsk(questionInput.value);
    }
  });

  if (openStructureWindowButton) {
    openStructureWindowButton.addEventListener("click", openStructureWindow);
  }

  if (researchRefreshButton) {
    researchRefreshButton.addEventListener("click", refreshAutonomousResearch);
  }

  if (logoutButton) {
    logoutButton.addEventListener("click", handleLogout);
  }

  setBranding();
  updateAuthChrome();
  if (window.ECMOProteinViewer && typeof window.ECMOProteinViewer.mountAll === "function") {
    window.ECMOProteinViewer.mountAll();
  }
  renderAll();
  setView("home");
  updateAssistantChrome();
  checkLiveAssistant().finally(() => {
    resetAssistant();
    startAutonomousWatchdog();
  });
})();
