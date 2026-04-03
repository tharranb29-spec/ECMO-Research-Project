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
  const overviewView = document.getElementById("overview-view");
  const assistantView = document.getElementById("assistant-view");
  const metaRow = document.getElementById("meta-row");
  const statsGrid = document.getElementById("stats-grid");
  const leaderboard = document.getElementById("leaderboard");
  const directoryGrid = document.getElementById("directory-grid");
  const targetSections = document.getElementById("target-sections");
  const weightsPanel = document.getElementById("weights-panel");
  const researchLeadsPanel = document.getElementById("research-leads");
  const assistantSideHits = document.getElementById("assistant-side-hits");
  const searchInput = document.getElementById("search-input");
  const assistantMessages = document.getElementById("assistant-messages");
  const assistantStatus = document.getElementById("assistant-status");
  const assistantModeChip = document.getElementById("assistant-mode-chip");
  const assistantDatasetChip = document.getElementById("assistant-dataset-chip");
  const assistantHistoryChip = document.getElementById("assistant-history-chip");
  const contextInput = document.getElementById("context-input");
  const questionInput = document.getElementById("question-input");
  const askButton = document.getElementById("ask-button");
  const openStructureWindowButton = document.getElementById("open-structure-window");

  let activeDataset = datasets.seed ? "seed" : datasets.autonomous ? "autonomous" : datasets.custom ? "custom" : "seed";
  let activeView = "overview";
  let activeSearch = "";
  const histories = { seed: [], custom: [], autonomous: [] };
  const liveAssistant = {
    checked: false,
    connected: false,
    provider: null,
    model: null,
  };
  let bundlePollingStarted = false;

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

  function createTimestampLabel() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function updateAssistantChrome() {
    if (assistantDatasetChip) {
      assistantDatasetChip.textContent = datasetLabel(activeDataset);
    }

    if (assistantHistoryChip) {
      const questionCount = histories[activeDataset].filter((item) => item.role === "user").length;
      assistantHistoryChip.textContent = `${questionCount} prompt${questionCount === 1 ? "" : "s"}`;
    }

    if (assistantModeChip) {
      const label = liveAssistant.connected
        ? `Live ${liveAssistant.provider ? `via ${liveAssistant.provider}` : "assistant"}`
        : liveAssistant.checked
          ? "Fallback mode"
          : "Checking connection";
      assistantModeChip.textContent = label;
      assistantModeChip.classList.remove("primary", "warning");
      assistantModeChip.classList.add(liveAssistant.connected ? "primary" : "warning");
    }
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
    if (payload.research_leads) {
      bundle.research_leads = payload.research_leads;
    }
    if (payload.research_status) {
      bundle.research_status = payload.research_status;
    }
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
    overviewView.classList.toggle("active", viewName === "overview");
    assistantView.classList.toggle("active", viewName === "assistant");
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

    card.append(top, bar, tags, reasoning, evidence);

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
      head.innerHTML = `<div><strong>${target}</strong><div class="mini-exp">${targetRows.length} visible candidate${targetRows.length === 1 ? "" : "s"}</div></div><div class="mini-score">${targetRows[0].predicted_score.toFixed(1)} top score</div>`;

      const list = document.createElement("div");
      list.className = "mini-list";
      targetRows.forEach((row) => {
        const item = document.createElement("div");
        item.className = "mini-row";
        item.innerHTML = `
          <div><div class="mini-name">${row.candidate_name}</div><div class="mini-exp">${row.modality}</div></div>
          <div class="mini-exp">${row.explanation || "No explanation provided."}</div>
          <div class="mini-score">${row.predicted_score.toFixed(1)}</div>
        `;
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
      head.innerHTML = `<strong>${target} Weights</strong><div class="mini-score">Validation error: ${mae} pts</div>`;

      const list = document.createElement("div");
      list.className = "weight-list";
      Object.entries(model.weights || {})
        .sort((a, b) => b[1] - a[1])
        .forEach(([feature, weight]) => {
          const item = document.createElement("div");
          item.className = "weight-item";
          const top = document.createElement("div");
          top.className = "weight-top";
          top.innerHTML = `<span>${FEATURE_LABELS[feature] || feature}</span><strong>${weight.toFixed(3)}</strong>`;
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
    const researchStatus = getResearchStatus();

    if (!leads.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No autonomous research leads have been discovered yet. Start the live server and let the background updater run.";
      researchLeadsPanel.append(empty);
      return;
    }

    if (researchStatus.last_updated) {
      const note = document.createElement("div");
      note.className = "empty-state";
      note.textContent = `Last autonomous research update: ${formatDate(researchStatus.last_updated)}. Leads discovered: ${researchStatus.lead_count || leads.length}.`;
      researchLeadsPanel.append(note);
    }

    leads.forEach((lead) => {
      const block = document.createElement("section");
      block.className = "target-block";
      const head = document.createElement("div");
      head.className = `target-head ${receptorClass(lead.target_receptor)}`;
      head.innerHTML = `<div><strong>${lead.candidate_name}</strong><div class="mini-exp">${lead.target_receptor} • ${lead.modality_guess}</div></div><div class="mini-score">${lead.lead_score}</div>`;

      const list = document.createElement("div");
      list.className = "weight-list";

      const rationale = document.createElement("p");
      rationale.className = "candidate-copy";
      rationale.textContent = lead.rationale || "Literature lead discovered by autonomous update.";

      const source = document.createElement("p");
      source.className = "candidate-copy";
      source.textContent = `Source: ${lead.source_title || "Unknown article"}${lead.publication_date ? ` • ${lead.publication_date}` : ""}`;

      list.append(rationale, source);
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

  function renderAll() {
    const rows = getFilteredRows(activeDataset);
    renderMeta(rows);
    renderStats(rows);
    renderLeaderboard(rows);
    renderDirectory(rows);
    renderTargetSections(rows);
    renderWeights();
    renderResearchLeads();
    renderAssistantSideHits(rows);
  }

  function findCandidateMatches(question) {
    const rows = getRows(activeDataset);
    const compactQuestion = normalize(question).replace(/\s+/g, "");
    return rows.filter((row) => {
      const compactName = normalize(row.candidate_name).replace(/\s+/g, "");
      return compactName && compactQuestion.includes(compactName);
    });
  }

  function formatInlineCode(text) {
    const fragment = document.createDocumentFragment();
    const parts = String(text).split(/(`[^`]+`)/g);
    parts.forEach((part) => {
      if (!part) {
        return;
      }
      if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
        const code = document.createElement("code");
        code.textContent = part.slice(1, -1);
        fragment.append(code);
      } else {
        fragment.append(document.createTextNode(part));
      }
    });
    return fragment;
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

    const lines = trimmed.split("\n").map((line) => line.trim()).filter(Boolean);
    const bulletLike = lines.length > 0 && lines.every((line) => /^[-*•]\s+/.test(line));
    if (bulletLike) {
      const ul = document.createElement("ul");
      lines.forEach((line) => {
        const li = document.createElement("li");
        li.append(formatInlineCode(line.replace(/^[-*•]\s+/, "")));
        ul.append(li);
      });
      container.append(ul);
      return;
    }

    const paragraph = document.createElement("p");
    const joined = lines.join(" ");
    paragraph.append(formatInlineCode(joined));
    container.append(paragraph);
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
    badge.textContent = role === "user" ? "Q" : "AI";
    const labelText = document.createElement("span");
    labelText.textContent = role === "user" ? "You" : "Research Assistant";
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
      if (!response.ok) {
        throw new Error("Status endpoint unavailable");
      }
      const payload = await response.json();
      liveAssistant.checked = true;
      liveAssistant.connected = Boolean(payload.live_assistant_enabled);
      liveAssistant.provider = payload.provider || null;
      liveAssistant.model = payload.model || null;

      if (liveAssistant.connected) {
        setAssistantStatus(`Live assistant connected via ${payload.provider || "API"} / ${payload.model}. Broader questions and reasoning over pasted notes are enabled.`, true);
        startBundlePolling();
      } else {
        setAssistantStatus("Dashboard server detected, but no live model key is configured. Using local fallback answers only.", false);
        startBundlePolling();
      }
    } catch (err) {
      liveAssistant.checked = true;
      liveAssistant.connected = false;
      setAssistantStatus("Static dashboard mode. Run research_assistant_server.py for the full live assistant.", false);
    }
  }

  async function pollBundle() {
    try {
      const response = await fetch("/api/bundle", { headers: { Accept: "application/json" } });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      if (payload.ok) {
        applyBundlePayload(payload);
      }
    } catch (err) {
      // Ignore polling errors in static mode.
    }
  }

  function startBundlePolling() {
    if (bundlePollingStarted) {
      return;
    }
    bundlePollingStarted = true;
    pollBundle();
    setInterval(pollBundle, 300000);
  }

  async function askLive(question) {
    const history = histories[activeDataset];
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset: activeDataset,
        question,
        extra_context: contextInput.value.trim(),
        history,
      }),
    });

    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Live assistant request failed.");
    }

    if (payload.provider || payload.model) {
      setAssistantStatus(`Live assistant connected via ${(payload.provider || liveAssistant.provider || "API")} / ${payload.model || liveAssistant.model}.`, true);
    }

    return payload.answer;
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

  setBranding();
  if (window.ECMOProteinViewer && typeof window.ECMOProteinViewer.mountAll === "function") {
    window.ECMOProteinViewer.mountAll();
  }
  renderAll();
  setView("overview");
  updateAssistantChrome();
  checkLiveAssistant().finally(resetAssistant);
})();
