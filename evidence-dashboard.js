(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const asArray = (value) => Array.isArray(value) ? value : [];
  const finite = (value) => typeof value === "number" && Number.isFinite(value);
  const label = (value) => String(value || "Not available").replaceAll("_", " ");
  const format = (value, digits) => finite(Number(value)) ? Number(value).toFixed(digits) : "n/a";

  function empty(node) {
    if (node) node.replaceChildren();
  }

  function node(tag, className, text) {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text !== undefined && text !== null) item.textContent = text;
    return item;
  }

  function classifyRun(run) {
    const explicitError = run.error || run.failure_reason;
    if (explicitError) return { state: "invalid", reason: String(explicitError) };
    if (!run.pose_path) return { state: "invalid", reason: "Pose output is missing" };
    if (!finite(run.minimized_affinity_kcal_mol)) return { state: "invalid", reason: "Affinity is missing or non-finite" };
    if (run.minimized_affinity_kcal_mol === 0) return { state: "review", reason: "Zero-value anomaly: inspect the raw log and pose before exclusion" };
    return { state: "valid", reason: "Parsed pose and finite non-zero affinity are present" };
  }

  function detailMetric(labelText, valueText) {
    const item = node("div", "evidence-detail-metric");
    item.append(node("span", "", labelText), node("strong", "", valueText));
    return item;
  }

  function detailCard(kicker, titleText, copyText, metrics) {
    const card = node("article", "evidence-detail-card");
    card.append(node("div", "evidence-mini-label", kicker), node("h3", "", titleText));
    if (copyText) card.append(node("p", "", copyText));
    if (metrics && metrics.length) {
      const grid = node("div", "evidence-detail-metrics");
      metrics.forEach((metric) => grid.append(detailMetric(metric[0], metric[1])));
      card.append(grid);
    }
    return card;
  }

  function statusPill(text, tone) {
    return node("span", `evidence-status ${tone}`, text);
  }

  function qcRows(results) {
    return results.map((result) => {
      const runs = asArray(result.runs).map((run) => ({ ...run, ...classifyRun(run) }));
      const valid = runs.filter((run) => run.state === "valid");
      const review = runs.filter((run) => run.state === "review");
      const invalid = runs.filter((run) => run.state === "invalid");
      const ordered = valid.map((run) => run.minimized_affinity_kcal_mol).sort((a, b) => a - b);
      const middle = Math.floor(ordered.length / 2);
      const median = ordered.length ? (ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2) : null;
      return { result, runs, valid, review, invalid, median, publishable: valid.length >= 5 && !review.length && !invalid.length };
    });
  }

  function renderSupervisor(bundle, results, qualityRows, validation) {
    const lanes = byId("evidence-decision-lanes");
    const strip = byId("evidence-summary-strip");
    const scope = byId("evidence-scope-note");
    if (!lanes || !strip || !scope) return;
    empty(lanes); empty(strip);

    const raw = results.slice().sort((a, b) => Number(a.minimized_affinity_mean_kcal_mol) - Number(b.minimized_affinity_mean_kcal_mol))[0];
    const pose = results.filter((item) => item.pose_quality_status === "pass")
      .sort((a, b) => Number(a.minimized_affinity_mean_kcal_mol) - Number(b.minimized_affinity_mean_kcal_mol))[0];
    const matched = Number(((bundle.gnina_bridge_results || {}).experimental_validation || {}).matched_candidate_count || 0);
    const laneData = [
      ["Pose-gated lead", pose ? pose.candidate_name : "No passing candidate", pose ? `${format(pose.cnn_score_mean, 3)} CNNscore` : "Pending", "Current pose-confidence lead; still conditional until uniform multi-seed coverage and provenance review are complete.", "teal"],
      ["Raw affinity leader", raw ? raw.candidate_name : "No completed result", raw ? `${format(raw.minimized_affinity_mean_kcal_mol, 2)} kcal/mol` : "Pending", "Lowest current minimized-affinity output. This is a raw computational order, not a measured affinity rank.", "gold"],
      ["Validation state", label(validation.overall_status), `${matched} matched records`, "The matched set is too small for a general correlation or predictive-performance claim.", "navy"],
    ];
    laneData.forEach(([kicker, titleText, valueText, copyText, tone]) => {
      const card = node("article", `evidence-decision-card ${tone}`);
      card.append(node("div", "evidence-card-label", kicker), node("h3", "", titleText), node("strong", "", valueText), node("p", "", copyText));
      lanes.append(card);
    });

    const metrics = [
      ["Docked candidates", results.length],
      ["Five-run coverage", qualityRows.filter((row) => row.valid.length >= 5).length],
      ["Pose-gate passes", results.filter((item) => item.pose_quality_status === "pass").length],
      ["Experimental matches", matched],
    ];
    metrics.forEach(([metricLabel, value]) => {
      const item = node("div", "evidence-summary-metric");
      item.append(node("span", "evidence-card-label", metricLabel), node("strong", "", String(value)));
      strip.append(item);
    });
    scope.textContent = "Scope boundary: GNINA supports prioritization and pose triage. It does not establish biological affinity, ECMO surface compatibility, or immune phenotypic reprogramming without independent experimental validation.";
  }

  function renderBenchmarks(validation) {
    const board = byId("evidence-benchmark-board");
    if (!board) return;
    empty(board);
    asArray(validation.benchmarks).forEach((benchmark) => {
      const rmsd = benchmark.top_pose_rmsd_angstrom || {};
      const status = benchmark.status === "passed" ? "Passed predefined gate" : "Protocol review required";
      board.append(detailCard(
        benchmark.role || "Benchmark",
        `${benchmark.benchmark_id || "Benchmark"} · ${benchmark.ligand || "Ligand"}`,
        benchmark.note || `${benchmark.target || "Target"}. Benchmark status is reported against the predefined recovery criterion.`,
        [["Status", status], ["Seeds", `${benchmark.seed_pass_count || 0}/${benchmark.seed_count || 0} passed`], ["Mean RMSD", rmsd.mean === undefined ? "n/a" : `${format(rmsd.mean, 2)} Å`], ["Best RMSD", `${format(benchmark.best_observed_rmsd_angstrom === undefined ? rmsd.min : benchmark.best_observed_rmsd_angstrom, 2)} Å`]]
      ));
    });
    if (!board.children.length) board.append(detailCard("Benchmark", "No benchmark record", "Generate the GNINA validation payload before presenting pose-recovery performance."));
  }

  function renderQc(qualityRows, protocol) {
    const policy = byId("evidence-qc-policy");
    const wrap = byId("evidence-qc-table");
    if (!policy || !wrap) return;
    empty(policy); empty(wrap);
    policy.append(node("h3", "", "Zero-output and run-validity policy"));
    policy.append(node("p", "", "Affinity = 0 is displayed as a review anomaly, not as a weak-binding measurement and not as an automatic failure. A run is excluded only when its raw log/output records an execution or parser error, a missing pose, a non-finite metric, or a reviewed malformed structure."));
    policy.append(node("p", "", "Planned robust-ranking gate: at least five valid runs per molecule, no unresolved anomalies, median and dispersion reported, and rank-stability checked across seeds."));

    const table = node("table", "evidence-table");
    const thead = node("thead");
    const head = node("tr");
    ["Candidate", "Valid / attempted", "Median affinity", "Pose gate", "Seed audit", "Rank status"].forEach((text) => head.append(node("th", "", text)));
    thead.append(head);
    const body = node("tbody");
    qualityRows.forEach((row) => {
      const tr = node("tr");
      tr.append(node("td", "", row.result.candidate_name || "Unnamed"));
      tr.append(node("td", "", `${row.valid.length} / ${row.runs.length}`));
      tr.append(node("td", "", row.median === null ? "n/a" : `${format(row.median, 2)} kcal/mol`));
      const poseCell = node("td");
      poseCell.append(statusPill(label(row.result.pose_quality_status), row.result.pose_quality_status === "pass" ? "ok" : "warning"));
      tr.append(poseCell);
      const seedCell = node("td");
      row.runs.forEach((run) => {
        const pill = statusPill(`s${run.seed}: ${run.state}`, run.state === "valid" ? "ok" : run.state === "review" ? "warning" : "blocked");
        pill.title = run.reason;
        seedCell.append(pill, document.createTextNode(" "));
      });
      tr.append(seedCell);
      const rankCell = node("td");
      rankCell.append(statusPill(row.publishable ? "robust aggregate ready" : "preliminary only", row.publishable ? "ok" : "warning"));
      tr.append(rankCell);
      body.append(tr);
    });
    table.append(thead, body); wrap.append(table);
  }

  function renderProvenance(bridge, validation) {
    const board = byId("evidence-provenance-board");
    if (!board) return;
    empty(board);
    const protocol = bridge.protocol || {};
    const assets = validation.direct_target_assets || {};
    board.append(detailCard("Execution protocol", `GNINA ${protocol.gnina_version || "version not recorded"}`, "The current bridge includes mixed seed coverage and therefore remains preliminary.", [["Runs", String(protocol.run_count || "n/a")], ["Exhaustiveness", String(protocol.exhaustiveness || "n/a")], ["Modes", String(protocol.num_modes || "n/a")], ["Pose threshold", `CNNscore ≥ ${format(protocol.cnn_score_min, 2)}`]]));
    board.append(detailCard("Receptor provenance", label(assets.receptor_review_status), "The direct Siglec-9 model remains a provisional reconstruction rather than the exact author-deposited construct.", [["Ranking unlocked", assets.ranking_unlocked ? "Yes" : "No"], ["Direct-target state", label(assets.status)], ["Verified ligands", `${assets.verified_ligand_count || 0}/${assets.required_ligand_count || 0}`], ["Reconstructed", String(assets.reconstructed_ligand_count || 0)]]));
    asArray(assets.blocking_reasons).forEach((reason, index) => board.append(detailCard(`Open provenance gate ${index + 1}`, "Required before claim escalation", reason)));
  }

  function discoveryDisposition(lead) {
    const name = String(lead.candidate_name || "").toLowerCase();
    if (name === "siglec-7") return ["Reject extraction noise", "The extracted name is a receptor, not a ligand candidate for Siglec-9.", "blocked"];
    if (name === "cd40" || name === "fc-fusion") return ["Route to biologic review", "This mention is outside the current small-molecule/glycan GNINA lane.", "warning"];
    return ["Manual identity review", "Verify exact chemical identity and coordinates before docking enrollment.", "warning"];
  }

  function renderDiscovery(bundle) {
    const board = byId("evidence-discovery-board");
    if (!board) return;
    empty(board);
    const leads = asArray((bundle.research_leads || {}).leads);
    leads.forEach((lead) => {
      const [decision, blocker, tone] = discoveryDisposition(lead);
      const card = detailCard("Autonomous literature lead", lead.candidate_name || "Unnamed", blocker, [["Target", lead.target_receptor || "n/a"], ["Extraction", lead.source_method || "n/a"], ["Identity verified", "No"], ["Docking eligible", "No"]]);
      card.append(statusPill(decision, tone));
      if (lead.source_url) {
        const source = node("a", "research-chip", "Open literature source");
        source.href = lead.source_url; source.target = "_blank"; source.rel = "noreferrer"; card.append(document.createTextNode(" "), source);
      }
      board.append(card);
    });
    if (!leads.length) board.append(detailCard("Discovery gate", "No current leads", "Run literature discovery, then verify target alignment, chemical identity, structure provenance, and modality before docking."));
  }

  function renderHandoff(results, qualityRows) {
    const board = byId("evidence-handoff-board");
    const next = byId("evidence-next-gate");
    if (!board || !next) return;
    empty(board); empty(next);
    const roles = { MTTSNeu5Ac: "Conditional computational lead", BTCNeu5Ac: "Matched-affinity comparator", sLeX: "Natural positive control", Neu5Ac: "Weak-binding control", "3SLN": "Natural glycan benchmark", "6SLN": "Natural glycan benchmark" };
    results.filter((item) => roles[item.candidate_name]).forEach((result) => {
      const qc = qualityRows.find((row) => row.result.candidate_id === result.candidate_id);
      const blockers = [];
      if (!qc || qc.valid.length < 5) blockers.push("multi-seed rerun");
      if (String(result.structure_status || "").includes("reconstructed")) blockers.push("chemistry review");
      if (result.pose_quality_status !== "pass") blockers.push("pose review");
      board.append(detailCard(roles[result.candidate_name], result.candidate_name, blockers.length ? `Conditional: ${blockers.join(", ")} required.` : "Computational dossier complete for supervisor review; wet-lab validation remains required.", [["Affinity", `${format(result.minimized_affinity_mean_kcal_mol, 2)} kcal/mol`], ["CNNscore", format(result.cnn_score_mean, 3)], ["CNNaffinity", `${format(result.cnn_affinity_mean_pk, 2)} pK`], ["Valid seeds", String(qc ? qc.valid.length : 0)]]));
    });
    next.append(node("strong", "", "Next decision gate: "), document.createTextNode("lock the expanded seed protocol, rerun controls and leads uniformly, independently review reconstructed glycomimetic chemistry, then freeze a small wet-lab shortlist with explicit positive, weak, and non-binding controls."));
  }

  function bindTabs() {
    document.querySelectorAll("[data-evidence-tab]").forEach((button) => {
      if (button.dataset.bound === "true") return;
      button.dataset.bound = "true";
      button.addEventListener("click", () => {
        const selected = button.dataset.evidenceTab;
        document.querySelectorAll("[data-evidence-tab]").forEach((tab) => {
          const active = tab.dataset.evidenceTab === selected;
          tab.classList.toggle("active", active); tab.setAttribute("aria-selected", String(active));
        });
        document.querySelectorAll("[data-evidence-panel]").forEach((panel) => {
          const active = panel.dataset.evidencePanel === selected;
          panel.classList.toggle("active", active); panel.hidden = !active;
        });
      });
    });
  }

  function renderEvidence() {
    const bundle = window.ECMO_DASHBOARD_DATA || {};
    const bridge = bundle.gnina_bridge_results || {};
    const validation = bundle.gnina_validation || {};
    const results = asArray(bridge.results).filter((item) => item.status === "completed" && !item.simulated);
    const qualityRows = qcRows(results);
    renderSupervisor(bundle, results, qualityRows, validation);
    renderBenchmarks(validation);
    renderQc(qualityRows, bridge.protocol || {});
    renderProvenance(bridge, validation);
    renderDiscovery(bundle);
    renderHandoff(results, qualityRows);
    const status = byId("evidence-workbench-status");
    if (status) status.textContent = validation.overall_status ? label(validation.overall_status) : "Validation pending";
    bindTabs();
  }

  window.addEventListener("ecmo:bundle-updated", renderEvidence);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", renderEvidence);
  else renderEvidence();
})();
