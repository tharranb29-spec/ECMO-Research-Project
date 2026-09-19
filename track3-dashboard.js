(function(){
  "use strict";
  const data=window.A2A_DASHBOARD_DATA;
  if(!data){document.body.innerHTML="<p>Dashboard data is unavailable. Run build_track3_dashboard.py.</p>";return;}
  const $=id=>document.getElementById(id), records=name=>data.contracts[name].records;
  const esc=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
  const safeUrl=value=>{try{const url=new URL(String(value));return url.protocol==="https:"?url.href:"#";}catch{return "#";}};
  const label=value=>String(value??"").replaceAll("_"," ");
  const fmt=(value,digits=2)=>Number(value).toFixed(digits);
  const short=(value,length=12)=>String(value).slice(0,length)+"…";
  const views=["overview","evidence","molecules","models","applicability","docking","md","portfolio","discovery","shadow","audit"];
  let moleculeFilter="all",moleculeQuery="",evidenceFilter="all",modelMetric="r2",dockingSort="name";

  function setView(view){
    const selected=views.includes(view)?view:"overview";
    document.querySelectorAll(".view").forEach(panel=>{const on=panel.dataset.panel===selected;panel.hidden=!on;panel.classList.toggle("active",on);});
    document.querySelectorAll(".nav-item").forEach(button=>button.classList.toggle("active",button.dataset.view===selected));
    document.querySelector(".sidebar").classList.remove("open");$("menu-toggle").setAttribute("aria-expanded","false");
    history.replaceState(null,"",`#${selected}`);window.scrollTo({top:0,behavior:"instant"});
  }
  document.querySelectorAll(".nav-item").forEach(button=>button.addEventListener("click",()=>setView(button.dataset.view)));
  document.querySelectorAll("[data-jump]").forEach(button=>button.addEventListener("click",()=>setView(button.dataset.jump)));
  $("menu-toggle").addEventListener("click",()=>{const sidebar=document.querySelector(".sidebar"),open=sidebar.classList.toggle("open");$("menu-toggle").setAttribute("aria-expanded",String(open));});

  $("project-title").textContent=data.project.title;$("claim-level").textContent=data.project.claim_level;$("target-label").textContent=data.project.target;$("deadline-label").textContent=`Deadline · ${data.project.deadline}`;$("protocol-label").textContent=data.project.protocol;$("snapshot-time").textContent=new Date(data.snapshot_created_at_utc).toLocaleString();

  const summary=[
    ["External cohort","0 / 60","Frozen floor failure"],
    ["Primary model",fmt(data.summary.primary_model_r2,3),"AB_Ridge development R²"],
    ["Dual-state candidates",data.summary.docked_candidates,"4 blinded proposals"],
    ["Tier A production",`${data.summary.tier_a_production_reported_ns}/${data.summary.tier_a_production_required_ns} ns`,"1/6 observed · 0 complete"],
    ["Served models","0","Shadow-only; release locked"]
  ];
  $("summary-grid").innerHTML=summary.map(item=>`<div class="metric"><span>${esc(item[0])}</span><strong>${esc(item[1])}</strong><small>${esc(item[2])}</small></div>`).join("");

  const gates=[
    ["G0–G1","Sources & evidence admission","Development evidence frozen; external pass 2 froze at zero","passed"],
    ["G2–G3","Redocking & docking QC","Primary receptors and prospective dual-state runs complete","passed"],
    ["G4–G6","Models & applicability","AB_Ridge leads development; no external confirmation","review"],
    ["G7","Tier A native controls","Equilibration 6/6; production 1/6 observed, 0 complete","authorized"],
    ["G8","Candidate MD","Locked until both controls pass 2/3 production replicas","locked"],
    ["G9","Model promotion","Blocked: external floors failed and human release absent","blocked"]
  ];
  $("gate-map").innerHTML=gates.map(g=>`<div class="gate-row"><div class="gate-number">${g[0]}</div><div><strong>${g[1]}</strong><small>${g[2]}</small></div><span class="status-pill ${g[3]}">${g[3]}</span></div>`).join("");

  const shadowActions=records("shadow_actions");
  $("shadow-mini").innerHTML=shadowActions.map((action,index)=>`<div class="mini-step"><i>${String(index+1).padStart(2,"0")}</i><strong>${esc(action.stage)}</strong><span>${esc(label(action.status))}</span></div>`).join("");

  const pass1=records("evidence_inbox").filter(item=>item.stage==="pass_1_historical"),pass2=records("evidence_inbox").find(item=>item.record_id.includes("pass-2"));
  const funnel=[["Initial queue",data.summary.evidence_queue,"outcome blind"],["Pass 2 required",data.summary.pass_2_required,"source review"],["Source grounded",pass2.count,"retrieved full text"],["Admitted",data.summary.external_admitted,"membership frozen"],["Outcome join",0,"prohibited"]];
  $("evidence-funnel").innerHTML=funnel.map(item=>`<div class="funnel-step"><span>${item[0]}</span><strong>${item[1]}</strong><small>${item[2]}</small></div>`).join("");
  function renderEvidence(){
    const rows=records("evidence_inbox").filter(row=>evidenceFilter==="all"||row.disposition===evidenceFilter||(evidenceFilter==="review"&&["reviewed","review"].includes(row.disposition)));
    $("evidence-lanes").innerHTML=rows.map(row=>`<div class="lane-card ${esc(row.disposition)}"><strong>${row.count}</strong><h3>${esc(row.title)}</h3><p>${esc(label(row.stage))} · ${esc(label(row.status))}</p></div>`).join("")||"<p>No lanes match this filter.</p>";
  }
  document.querySelectorAll("#evidence-filter button").forEach(button=>button.addEventListener("click",()=>{evidenceFilter=button.dataset.filter;document.querySelectorAll("#evidence-filter button").forEach(item=>item.classList.toggle("active",item===button));renderEvidence();}));renderEvidence();

  const molecules=records("molecule_registry");$("molecule-count").textContent=molecules.length;
  function renderMolecules(){
    const query=moleculeQuery.toLowerCase(),rows=molecules.filter(row=>{const type=row.role.includes("control")?"control":"candidate";return (moleculeFilter==="all"||type===moleculeFilter)&&`${row.molecule_id} ${row.display_name} ${row.role}`.toLowerCase().includes(query);});
    $("molecule-grid").innerHTML=rows.map(row=>{const type=row.role.includes("control")?"control":"candidate";return `<article class="registry-card ${type}"><header><span class="tag">${type}</span><span class="tag">${row.functional_label_blinded?"label blind":"native control"}</span></header><h2>${esc(row.display_name)}</h2><small>${esc(row.molecule_id)}</small><p>${esc(row.role)}<br>${esc(row.identity_status)}</p><div class="source-line">${esc(row.source.path)} · ${short(row.source.sha256)}</div></article>`;}).join("")||"<p>No registry records match.</p>";
  }
  $("molecule-search").addEventListener("input",event=>{moleculeQuery=event.target.value;renderMolecules();});document.querySelectorAll("#molecule-filter button").forEach(button=>button.addEventListener("click",()=>{moleculeFilter=button.dataset.filter;document.querySelectorAll("#molecule-filter button").forEach(item=>item.classList.toggle("active",item===button));renderMolecules();}));renderMolecules();

  const models=records("model_registry");
  function renderModels(){
    const values=models.map(row=>Number(row[modelMetric])),max=Math.max(...values),min=Math.min(...values),range=Math.max(max-min,.001),lowerBetter=modelMetric!=="r2";
    $("model-comparison").innerHTML=models.map(row=>{const value=Number(row[modelMetric]),width=lowerBetter?(max-value)/range*80+20:(value-min)/range*80+20;return `<div class="bar-row ${row.model_id==="AB_Ridge"?"primary":""}"><label>${esc(row.display_name)}</label><div class="bar-track"><i style="width:${width}%"></i></div><strong>${fmt(value,3)}</strong></div>`;}).join("");
    $("model-grid").innerHTML=models.map(row=>`<article class="model-card ${row.model_id==="AB_Ridge"?"primary":""}"><span class="kicker">${esc(row.role)}</span><span class="lock">Not served</span><h3>${esc(row.display_name)}</h3><div class="score">${fmt(row.r2,3)}</div><small>R² · RMSE ${fmt(row.rmse,3)} · MAE ${fmt(row.mae,3)}</small><div class="source-line">${esc(row.source.path)}</div></article>`).join("");
  }
  document.querySelectorAll("#metric-toggle button").forEach(button=>button.addEventListener("click",()=>{modelMetric=button.dataset.metric;document.querySelectorAll("#metric-toggle button").forEach(item=>item.classList.toggle("active",item===button));renderModels();}));renderModels();

  const domain=records("applicability_uncertainty")[0],domainTotal=domain.inside_n+domain.outside_n,insidePercent=domain.inside_n/domainTotal*100;
  $("domain-panel").innerHTML=`<div class="domain-visual"><div class="donut" style="--inside:${insidePercent*3.6}deg"><div><strong>${fmt(insidePercent,1)}%</strong><span>inside domain</span></div></div><div class="domain-copy"><dl><dt>Inside</dt><dd>${domain.inside_n}</dd><dt>Outside</dt><dd>${domain.outside_n}</dd><dt>Tanimoto floor</dt><dd>${domain.similarity_threshold}</dd><dt>Descriptor distance</dt><dd>${fmt(domain.descriptor_distance_threshold,3)}</dd></dl><p>Development grouped out-of-fold scope only.</p></div></div>`;
  const ci=domain.r2_interval,scaleMin=.3,scaleMax=.75,left=(ci.lower-scaleMin)/(scaleMax-scaleMin)*100,width=(ci.upper-ci.lower)/(scaleMax-scaleMin)*100,point=(ci.estimate-scaleMin)/(scaleMax-scaleMin)*100;
  $("uncertainty-panel").innerHTML=`<div class="interval"><strong>${fmt(ci.estimate,3)}</strong><span>bootstrap estimate</span><div class="interval-track"><i style="left:${left}%;width:${width}%"></i><b style="left:${point}%"></b></div><span>95% interval · ${fmt(ci.lower,3)}–${fmt(ci.upper,3)}</span></div><div class="source-line">${esc(domain.source.path)} · ${short(domain.source.sha256)}</div>`;

  const dockingRows=records("dual_state_docking");
  function dockingGroups(){return dockingRows.reduce((acc,row)=>{(acc[row.molecule_id]??=[]).push(row);return acc;},{});}
  function renderDocking(){
    let groups=Object.entries(dockingGroups()).map(([id,rows])=>{const inactive=rows.find(row=>row.receptor_state==="inactive"),active=rows.find(row=>row.receptor_state==="active-like");return{id,inactive,active,delta:active.median_affinity_kcal_mol-inactive.median_affinity_kcal_mol,mean:(active.median_affinity_kcal_mol+inactive.median_affinity_kcal_mol)/2};});
    groups.sort((a,b)=>dockingSort==="delta"?Math.abs(b.delta)-Math.abs(a.delta):dockingSort==="affinity"?a.mean-b.mean:a.id.localeCompare(b.id));
    $("docking-grid").innerHTML=groups.map(group=>`<article class="docking-card"><header><div><span class="kicker">Label blind · 3+3 seeds</span><h2>${esc(group.id.replace("LIT25-",""))}</h2></div><span class="status-pill shadow">Shadow</span></header><div class="state-pair"><div class="state-box"><span>5NM4 inactive</span><strong>${fmt(group.inactive.median_affinity_kcal_mol,2)}</strong><small>kcal/mol · CNN ${fmt(group.inactive.median_cnn_score,3)}</small></div><div class="state-box active"><span>2YDO active-like</span><strong>${fmt(group.active.median_affinity_kcal_mol,2)}</strong><small>kcal/mol · CNN ${fmt(group.active.median_cnn_score,3)}</small></div></div><div class="delta-line"><span>State difference</span><b>${group.delta>0?"+":""}${fmt(group.delta,3)} kcal/mol</b></div><div class="source-line">${esc(group.inactive.source.path)} · retained poses hashed</div></article>`).join("");
  }
  document.querySelectorAll("#docking-sort button").forEach(button=>button.addEventListener("click",()=>{dockingSort=button.dataset.sort;document.querySelectorAll("#docking-sort button").forEach(item=>item.classList.toggle("active",item===button));renderDocking();}));renderDocking();

  const md=records("md_gates");
  $("md-gates").innerHTML=md.map(gate=>{const isEquil=gate.gate_id.includes("equilibration"),isProduction=gate.gate_id.includes("production"),tone=isEquil?"passed":isProduction?"authorized":"locked",pct=isProduction?Math.round((gate.completion_fraction_by_reported_ns||0)*100):(gate.required_runs?Math.round(gate.passed_runs/gate.required_runs*100):0);return `<article class="md-card ${tone}"><div class="progress-ring" style="--progress:${pct*3.6}deg"><span>${isProduction?`${pct}%`:`${gate.passed_runs}/${gate.required_runs}`}</span></div><span class="kicker">${esc(gate.gate_id)}</span><h2>${isEquil?"Equilibration passed":isProduction?"Pilot running, incomplete":"Candidate MD locked"}</h2><span class="status-pill ${tone}">${esc(label(gate.status))}</span><p>${esc(gate.claim_limit)}</p><div class="source-line">${esc(gate.source.path)}</div></article>`;}).join("");
  $("production-progress-copy").textContent=`${data.summary.tier_a_production_observed_replicas}/6 replicas observed, ${data.summary.tier_a_production_completed_replicas} complete, ${data.summary.tier_a_production_reported_ns}/${data.summary.tier_a_production_required_ns} ns reported at cutoff. Tier B remains locked.`;
  const mdSource=md[0],missing=new Set(mdSource.missing_audits.map(path=>path.split("/").slice(0,2).join(":"))),systems=["5NM4_ZMA_native","5G53_NECA_miniGs_native_nucleotide_free"],seeds=[20260914,20260915,20260916];
  let matrix=`<div class="md-cell header">System</div>${seeds.map(seed=>`<div class="md-cell header">Seed ${seed}</div>`).join("")}`;systems.forEach(system=>{matrix+=`<div class="md-cell header">${esc(label(system))}</div>`;seeds.forEach(seed=>{const absent=missing.has(`${system}:seed-${seed}`);matrix+=`<div class="md-cell ${absent?"missing":"pass"}">${absent?"Missing audit":"Gate passed"}</div>`;});});$("md-matrix").innerHTML=matrix;

  const portfolio=records("candidate_portfolio"),dockingById=dockingGroups();
  $("portfolio-board").innerHTML=portfolio.map(item=>{const rows=dockingById[item.molecule_id],inactive=rows.find(row=>row.receptor_state==="inactive"),active=rows.find(row=>row.receptor_state==="active-like");return `<article class="portfolio-card"><header><div><span class="kicker">Computationally prioritized</span><h2>${esc(item.molecule_id.replace("LIT25-",""))}</h2></div><span class="status-pill blocked">Not releasable</span></header><div class="portfolio-metrics"><div><span>5NM4</span><strong>${fmt(inactive.median_affinity_kcal_mol,2)}</strong></div><div><span>2YDO</span><strong>${fmt(active.median_affinity_kcal_mol,2)}</strong></div><div><span>Δ score</span><strong>${item.d_affinity_kcal_mol>0?"+":""}${fmt(item.d_affinity_kcal_mol,2)}</strong></div></div><p>${esc(item.next_gate)} Label status: ${esc(item.label_status)}. MD state: ${esc(label(item.md_status))}.</p><div class="source-line">${esc(item.source.path)} · ${short(item.source.sha256)}</div></article>`;}).join("");

  let currentDiscoveryRun=null;
  async function apiJson(path,options={}){
    const response=await fetch(path,{headers:{"Content-Type":"application/json"},...options});
    const payload=await response.json().catch(()=>({ok:false,error:"The server returned an unreadable response."}));
    if(!response.ok||payload.ok===false)throw new Error(payload.error||`Request failed (${response.status})`);
    return payload;
  }
  function capabilityBadge(name,value){const tone=value==="available"?"passed":value==="sealed"||value==="locked"||value==="disabled"?"blocked":"shadow";return `<span class="status-pill ${tone}">${esc(label(name))}: ${esc(label(value))}</span>`;}
  function updateDiscoveryBanner(capabilities,run){
    const banner=$("discovery-state-banner"),live=capabilities?.live_provider==="available";
    banner.classList.toggle("live",live);banner.classList.toggle("cached",!live);
    banner.innerHTML=`<span class="state-dot"></span><div><strong>${live?"Live DeepSeek extraction available":"Cached demo ready · live DeepSeek unavailable"}</strong><small>${run?`Latest run: ${esc(label(run.workflow_state))}`:"API keys remain server-side. Missing capabilities fail closed."}</small></div><div class="capability-row">${capabilityBadge("RDKit",capabilities?.rdkit||"unavailable")}${capabilityBadge("AB Ridge",capabilities?.ab_ridge_scorer||"unavailable")}</div>`;
  }
  function renderDiscovery(run){
    if(!run)return;currentDiscoveryRun=run;$("discovery-results").hidden=false;$("discovery-run-id").textContent=run.run_id;
    const stateTone=run.workflow_state==="live"?"passed":"shadow";
    const detailValue=value=>value&&typeof value==="object"?`${Object.keys(value).length} resolved contracts`:String(value);
    $("discovery-stages").innerHTML=run.audit_log.map(item=>`<div class="discovery-stage"><span>${String(item.sequence).padStart(2,"0")}</span><div><strong>${esc(label(item.event_type))}</strong><small>${esc(Object.entries(item.details).map(([key,value])=>`${label(key)}: ${detailValue(value)}`).join(" · "))}</small></div><i class="status-pill ${stateTone}">${run.workflow_state==="live"?"live":"cached"}</i></div>`).join("");
    $("source-count").textContent=`${run.sources.length} cited records · ${label(run.workflow_state)}`;
    $("discovery-sources").innerHTML=run.sources.map(source=>{const extraction=run.extractions.find(item=>item.source_id===source.source_id)||{};return `<article class="source-card"><div><span class="status-pill ${source.retrieval_state==="live"?"passed":"shadow"}">${esc(source.retrieval_state)}</span><span class="status-pill ${extraction.evidence_quality==="quarantine"?"blocked":"review"}">${esc(extraction.evidence_quality||"unresolved")}</span></div><h3>${esc(source.title)}</h3><p>${esc(extraction.reason||"No extraction rationale returned.")}</p><a href="${esc(safeUrl(source.url))}" target="_blank" rel="noopener noreferrer">${esc(source.source_id)} · source ↗</a><small>DOI ${esc(source.doi||"unresolved")} · full text ${esc(source.full_text_state||"unresolved")}</small></article>`;}).join("")||'<p class="empty-state">No citable sources returned.</p>';
    const queue=run.screen_eligible_queue;$("queue-count").textContent=`${queue.count} eligible`;
    $("discovery-queue").innerHTML=`<div class="queue-summary"><strong>${queue.count}</strong><span>unordered records</span><dl><dt>Scaffolds</dt><dd>${queue.scaffold_count}</dd><dt>Ordering</dt><dd>Composition only</dd><dt>AB_Ridge scores</dt><dd>Unavailable</dd></dl><p>${esc(queue.claim_limit)}</p></div>${Object.entries(queue.scaffold_composition).map(([scaffold,count])=>`<div class="scaffold-row"><code>${esc(scaffold)}</code><b>${count}</b></div>`).join("")}`;
    $("discovery-molecule-grid").innerHTML=run.molecules.map(molecule=>`<article class="registry-card ${molecule.screen_eligible?"control":"candidate"}"><header><span class="tag">${esc(molecule.state_label)}</span><span class="status-pill ${molecule.screen_eligible?"passed":"blocked"}">${molecule.screen_eligible?"screen eligible":"held"}</span></header><h2>${esc(molecule.name)}</h2><small>${esc(molecule.molecule_id)}</small><p>Identity · ${esc(label(molecule.standardization_state))}<br>Domain · ${esc(label(molecule.applicability))}<br>Uncertainty · ${esc(label(molecule.uncertainty))}<br>AB_Ridge · ${esc(label(molecule.score_state))}</p><div class="eligibility-note">${esc(molecule.eligibility_reasons.join(" ")||"No gate rationale recorded.")}</div><div class="source-line">${esc(molecule.canonical_smiles||molecule.input_smiles)}</div></article>`).join("")||'<p class="empty-state">No molecule records were submitted.</p>';
    $("disposition-state").textContent=label(run.human_disposition.status);$("disposition-state").className=`status-pill ${run.human_disposition.status==="pending"?"review":"passed"}`;
  }
  function parseMoleculeInput(value){return value.split(/\n+/).map(line=>{const [name,...smilesParts]=line.split("|");return{name:(name||"").trim(),smiles:smilesParts.join("|").trim()};}).filter(item=>item.smiles);}
  $("discovery-form").addEventListener("submit",async event=>{
    event.preventDefault();const button=$("discovery-run");button.disabled=true;button.textContent="Running gates…";
    try{const payload=await apiJson("/api/discovery/run",{method:"POST",body:JSON.stringify({query:$("discovery-query").value,provider_mode:$("discovery-provider").value,molecules:parseMoleculeInput($("discovery-molecules").value)})});renderDiscovery(payload.run);updateDiscoveryBanner({live_provider:payload.run.workflow_state==="live"?"available":"unavailable",rdkit:payload.run.molecules.some(item=>item.standardization_engine==="RDKit")?"available":"unavailable",ab_ridge_scorer:"unavailable"},payload.run);}
    catch(error){$("discovery-stages").innerHTML=`<p class="error-state">${esc(error.message)}</p>`;}
    finally{button.disabled=false;button.textContent="Run shadow workflow";}
  });
  $("disposition-form").addEventListener("submit",async event=>{
    event.preventDefault();if(!currentDiscoveryRun)return;
    try{const payload=await apiJson("/api/discovery/disposition",{method:"POST",body:JSON.stringify({run_id:currentDiscoveryRun.run_id,status:$("disposition-choice").value,reviewer:$("disposition-reviewer").value,note:$("disposition-note").value})});renderDiscovery(payload.run);}
    catch(error){$("disposition-state").textContent=error.message;$("disposition-state").className="status-pill blocked";}
  });
  apiJson("/api/discovery/status").then(payload=>{updateDiscoveryBanner(payload.capabilities,payload.latest_run);if(payload.latest_run)renderDiscovery(payload.latest_run);}).catch(error=>{$("discovery-state-banner").innerHTML=`<span class="state-dot"></span><div><strong>Discovery endpoint unavailable</strong><small>${esc(error.message)}</small></div>`;});

  $("shadow-workflow").innerHTML=shadowActions.map((action,index)=>`<article class="shadow-card ${esc(action.status)}"><span class="kicker">Step ${String(index+1).padStart(2,"0")}</span><h2>${esc(action.stage)}</h2><div class="executor">${esc(action.executor)} · ${esc(label(action.status))}</div><p>${esc(action.authority)}</p><div class="gate"><b>Required gate</b><br>${esc(action.required_gate)}</div><div class="source-line">${esc(action.source.path)}<br>${short(action.source.sha256,16)}</div></article>`).join("");
  const prohibited=[...new Set(shadowActions.flatMap(action=>action.prohibited_actions))];$("prohibited-grid").innerHTML=prohibited.map(item=>`<span>${esc(label(item))}</span>`).join("");

  const audit=records("audit_log");$("audit-count").textContent=`${audit.length} linked entries`;
  $("audit-list").innerHTML=audit.map(entry=>`<article class="audit-item"><span>#${String(entry.sequence).padStart(4,"0")}</span><div><strong>${esc(label(entry.action))}</strong><small>${esc(entry.record_type)}</small></div><div><strong>${esc(entry.record_id)}</strong><code>${esc(entry.source.path)}</code></div><div><code>${short(entry.entry_hash,16)}</code><small>prev ${short(entry.previous_entry_hash,10)}</small></div></article>`).join("");

  const requested=location.hash.slice(1);setView(views.includes(requested)?requested:"overview");
})();
