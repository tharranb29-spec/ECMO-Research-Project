(function(){
  "use strict";
  const data=window.A2A_DASHBOARD_DATA;
  if(!data){document.body.innerHTML="<p>Dashboard bundle missing. Run build_track3_dashboard.py.</p>";return;}
  const $=(id)=>document.getElementById(id);
  const records=(name)=>data.contracts[name].records;
  const fmt=(n,d=2)=>Number(n).toFixed(d);
  const esc=(s)=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const short=(s,n=12)=>String(s).slice(0,n)+"…";
  const label=(s)=>String(s).replaceAll("_"," ");

  function setView(view){
    document.querySelectorAll(".view").forEach(p=>{const on=p.dataset.panel===view;p.classList.toggle("active",on);p.hidden=!on;});
    document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.view===view));
    document.querySelector(".sidebar").classList.remove("open");$("menu-toggle").setAttribute("aria-expanded","false");
    history.replaceState(null,"",`#${view}`);
  }
  document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>setView(b.dataset.view)));
  $("menu-toggle").addEventListener("click",()=>{const side=document.querySelector(".sidebar");const open=side.classList.toggle("open");$("menu-toggle").setAttribute("aria-expanded",String(open));});

  $("project-title").textContent=data.project.title;
  $("claim-level").textContent=data.project.claim_level;
  $("target-label").textContent=data.project.target;
  $("deadline-label").textContent=`Competition deadline · ${data.project.deadline}`;
  $("protocol-label").textContent=data.project.protocol;
  $("snapshot-time").textContent=new Date(data.snapshot_created_at_utc).toLocaleString();

  const summary=[
    ["Evidence queue",data.summary.evidence_queue,"187 require source-grounded pass 2"],
    ["Primary model R²",fmt(data.summary.primary_model_r2,3),"Development-only AB_Ridge"],
    ["Prospective docking",data.summary.docked_candidates,"Four label-blind candidates · both states"],
    ["Tier A equilibration",`${data.summary.md_runs_passed}/${data.summary.md_runs_required}`,"Tier A production and Tier B remain locked"]
  ];
  $("summary-grid").innerHTML=summary.map(x=>`<div class="metric"><span>${esc(x[0])}</span><strong>${esc(x[1])}</strong><small>${esc(x[2])}</small></div>`).join("");

  const gates=[
    ["G0–G1","Sources & development evidence","Frozen development sources; external membership pending","passed"],
    ["G2–G3","Redocking & production QC","Retrospective and four prospective candidates complete","passed"],
    ["G4–G6","Model & applicability","Development complete; external thresholds not frozen","review"],
    ["G7","MD native controls",`${data.summary.md_runs_passed}/${data.summary.md_runs_required} equilibration audits pass; production locked`,"review"],
    ["G8–G9","Candidate MD & promotion","Tier B and model promotion locked","locked"]
  ];
  $("gate-map").innerHTML=gates.map(g=>`<div class="gate-row"><div class="gate-number">${g[0]}</div><div><strong>${g[1]}</strong><span>${g[2]}</span></div><span class="status-pill ${g[3]}">${g[3]}</span></div>`).join("");

  const portfolio=records("candidate_portfolio");$("portfolio-count").textContent=`${portfolio.length} records`;
  $("portfolio-list").innerHTML=portfolio.map(p=>`<div class="portfolio-item"><div><strong>${esc(p.molecule_id.replace("LIT25-",""))}</strong><span>${esc(label(p.promotion_status))} · ${esc(label(p.md_status))}</span></div><code>Δ ${p.d_affinity_kcal_mol>0?"+":""}${fmt(p.d_affinity_kcal_mol,3)}</code></div>`).join("");

  $("evidence-total").textContent=data.summary.evidence_queue;
  $("evidence-lanes").innerHTML=records("evidence_inbox").map(e=>`<article class="lane-card ${e.disposition}"><strong>${e.count}</strong><h3>${esc(e.title)}</h3><p>${e.disposition==="quarantined"?"Held outside membership.":"Requires independent source-grounded review."} Outcomes loaded: no.</p></article>`).join("");

  $("model-grid").innerHTML=records("model_registry").map(m=>`<article class="model-card ${m.model_id==="AB_Ridge"?"primary":""}"><span class="role">${esc(m.role)}</span><span class="lock">Not served</span><h3>${esc(m.display_name)}</h3><div class="score">${fmt(m.r2,3)}</div><small>R² · RMSE ${fmt(m.rmse,3)} · n=${m.development_n}</small></article>`).join("");
  const domain=records("applicability_uncertainty")[0],total=domain.inside_n+domain.outside_n,inside=domain.inside_n/total*100;
  $("domain-panel").innerHTML=`<div class="domain-bar"><span class="inside" style="width:${inside}%"></span><span class="outside" style="width:${100-inside}%"></span></div><div class="domain-legend"><span>${domain.inside_n} inside domain</span><span>${domain.outside_n} outside</span></div><p class="domain-note">Tanimoto threshold ${domain.similarity_threshold}; descriptor-distance threshold ${fmt(domain.descriptor_distance_threshold,3)}. These thresholds describe development evaluation and are not yet frozen for external use.</p>`;
  const ci=domain.r2_interval,min=.3,max=.75,left=(ci.lower-min)/(max-min)*100,width=(ci.upper-ci.lower)/(max-min)*100,point=(ci.estimate-min)/(max-min)*100;
  $("uncertainty-panel").innerHTML=`<div class="interval"><strong>${fmt(ci.estimate,3)}</strong><span>Bootstrap R² estimate</span><div class="interval-track"><i style="left:${left}%;width:${width}%"></i><b style="left:${point}%"></b></div><span>95% interval ${fmt(ci.lower,3)}–${fmt(ci.upper,3)}</span></div><p class="domain-note">${esc(domain.calibration_warning)}</p>`;

  const docking=records("dual_state_docking"),byMolecule=Object.groupBy?Object.groupBy(docking,d=>d.molecule_id):docking.reduce((a,d)=>((a[d.molecule_id]??=[]).push(d),a),{});
  $("docking-grid").innerHTML=Object.entries(byMolecule).map(([id,rows])=>{const inactive=rows.find(r=>r.receptor_state==="inactive"),active=rows.find(r=>r.receptor_state==="active-like");return `<article class="docking-card"><header><div><span class="kicker">Label blind</span><h2>${esc(id.replace("LIT25-",""))}</h2></div><span class="shadow-tag">Shadow proposal</span></header><div class="state-pair"><div class="state-box"><span>5NM4 · inactive</span><strong>${fmt(inactive.median_affinity_kcal_mol,2)}</strong><small>kcal/mol · CNNscore ${fmt(inactive.median_cnn_score,3)}</small></div><div class="state-box active-like"><span>2YDO · active-like</span><strong>${fmt(active.median_affinity_kcal_mol,2)}</strong><small>kcal/mol · CNNscore ${fmt(active.median_cnn_score,3)}</small></div></div><div class="docking-footer"><span>3 + 3 valid seeds</span><span>Retained poses hashed</span></div></article>`}).join("");

  const md=records("md_gates");
  $("md-gates").innerHTML=md.map(g=>{const pct=g.required_runs?Math.round(g.passed_runs/g.required_runs*100):0;return `<article class="md-card locked"><div class="progress-ring" style="--progress:${pct*3.6}deg"><span>${g.passed_runs}/${g.required_runs}</span></div><span class="kicker">${esc(g.gate_id)}</span><h2>${g.gate_id.startsWith("G7")?"Native-control gate":"Candidate MD gate"}</h2><span class="status-pill locked">${esc(label(g.status))}</span><p>${esc(g.claim_limit)}</p></article>`}).join("");
  const mdSource=md[0],missing=new Set(mdSource.missing_audits.map(x=>x.split("/").slice(0,2).join(":"))),systems=["5NM4_ZMA_native","5G53_NECA_miniGs_native_nucleotide_free"],seeds=[20260914,20260915,20260916];
  let matrix=`<div class="md-cell header">System</div>${seeds.map(s=>`<div class="md-cell header">Seed ${s}</div>`).join("")}`;
  systems.forEach(system=>{matrix+=`<div class="md-cell header">${esc(system.replaceAll("_"," "))}</div>`;seeds.forEach(seed=>{const miss=missing.has(`${system}:seed-${seed}`);matrix+=`<div class="md-cell ${miss?"missing":"pass"}">${miss?"Missing audit":"Gate passed"}</div>`;});});$("md-matrix").innerHTML=matrix;

  $("audit-list").innerHTML=records("audit_log").map(a=>`<article class="audit-item"><span>#${String(a.sequence).padStart(4,"0")}</span><div><strong>${esc(label(a.action))}</strong><small>${esc(a.record_type)}</small></div><div><strong>${esc(a.record_id)}</strong><code>${esc(a.source.path)}</code></div><div><code>${short(a.entry_hash,16)}</code><small>prev ${short(a.previous_entry_hash,10)}</small></div></article>`).join("");
  const requested=location.hash.slice(1);
  setView(["overview","evidence","models","docking","md","audit"].includes(requested)?requested:"overview");
})();
