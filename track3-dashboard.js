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
  const views=["overview","evidence","molecules","models","applicability","docking","md","portfolio","discovery","shadow","teammate","audit"];
  let moleculeFilter="all",moleculeQuery="",evidenceFilter="all",modelMetric="r2";

  function setView(view){
    const selected=views.includes(view)?view:"overview";
    document.querySelectorAll(".view").forEach(panel=>{const on=panel.dataset.panel===selected;panel.hidden=!on;panel.classList.toggle("active",on);});
    document.querySelectorAll(".nav-item").forEach(button=>button.classList.toggle("active",button.dataset.view===selected));
    const activeNav=document.querySelector(`.nav-item[data-view="${selected}"]`);
    if(activeNav?.closest("#nav-more"))$("nav-more").open=true;
    document.querySelector(".sidebar").classList.remove("open");$("menu-toggle").setAttribute("aria-expanded","false");
    history.replaceState(null,"",`#${selected}`);window.scrollTo({top:0,behavior:"instant"});
  }
  document.querySelectorAll(".nav-item").forEach(button=>button.addEventListener("click",()=>setView(button.dataset.view)));
  document.querySelectorAll("[data-jump]").forEach(button=>button.addEventListener("click",()=>setView(button.dataset.jump)));
  $("menu-toggle").addEventListener("click",()=>{const sidebar=document.querySelector(".sidebar"),open=sidebar.classList.toggle("open");$("menu-toggle").setAttribute("aria-expanded",String(open));});

  $("project-title").textContent="A2A Evidence Command Center";$("project-full-title").textContent=data.project.title;$("claim-level").textContent=data.project.claim_level;$("target-label").textContent=data.project.target;$("deadline-label").textContent=`Deadline · ${data.project.deadline}`;$("protocol-label").textContent=data.project.protocol;$("snapshot-time").textContent=new Date(data.snapshot_created_at_utc).toLocaleString();

  const summary=[
    ["External cohort","0 / 60","Frozen floor failure"],
    ["Primary model",fmt(data.summary.primary_model_r2,3),"AB_Ridge development R²"],
    ["Promoted models","0","Development-only scorer; release locked"]
  ];
  $("summary-grid").innerHTML=summary.map(item=>`<div class="metric"><span>${esc(item[0])}</span><strong>${esc(item[1])}</strong><small>${esc(item[2])}</small></div>`).join("");

  const overviewModels=records("model_registry");
  let overviewMetric="r2";
  function renderOverviewModels(){
    const values=overviewModels.map(row=>Number(row[overviewMetric]));
    const high=Math.max(...values),low=Math.min(...values),span=Math.max(high-low,.001);
    const controls=[["r2","R²"],["rmse","RMSE"],["mae","MAE"]].map(([key,name])=>`<button type="button" data-overview-metric="${key}" class="${overviewMetric===key?"active":""}" aria-pressed="${overviewMetric===key}">${name}</button>`).join("");
    const bars=overviewModels.map(row=>{const value=Number(row[overviewMetric]),width=overviewMetric==="r2"?Math.max(0,value)/Math.max(.6,high)*100:(high-value)/span*100;return `<div class="overview-bar-row"><span>${esc(row.display_name)}</span><span class="overview-bar-track"><i style="width:${width}%"></i></span><strong>${fmt(value,3)}</strong></div>`;}).join("");
    $("overview-model-chart").innerHTML=`<div class="chart-switch" role="group" aria-label="Model metric">${controls}</div>${bars}<p class="chart-note">Grouped development evaluation only. ${overviewMetric==="r2"?"R² bars use a 0–0.6 axis; negative values show no positive bar.":"Error bars are relative to this comparison; lower is better."} No model is served.</p>`;
    $("overview-model-chart").querySelectorAll("[data-overview-metric]").forEach(button=>button.addEventListener("click",()=>{overviewMetric=button.dataset.overviewMetric;renderOverviewModels();}));
  }
  renderOverviewModels();

  // PDF-reported aggregate reference only. This object is never used by queue,
  // discovery, model, admission, or promotion logic.
  const teammatePdf={
    source_kind:"team_supplied_pdf_aggregate_transcription",
    status:"provisional_not_independently_reproduced",
    claim_limit:"not_external_validation_not_frozen_queue_not_molecule_level_data",
    source_pages:[5,7,9,10,12],
    sha256:"5308b8041c28657c9234b9a5a0f8b50b886ebe6146affa0b877a21f73fb9145f",
    funnel:[["Library",2963],["Inside PDF domain",423],["Antagonist class",335],["Screen-eligible",276]],
    scaffolds:{antagonist:149,screenEligible:120},
    pairwise:{total:55945,separable:2770,fraction:4.95,requiredGap:2.5176,largestAdjacentGap:0.3230},
    developmentStress:{n:74,calibrated:{separablePercent:4.2,coverage:0.8919},narrowed:{separablePercent:56.8,coverage:0.3649}},
    interval:{halfWidth:1.2588,hitBar:8.0,upperBoundCutoff:6.7412},
    precision:[[10,0.9600,0.4808,1.997],[20,0.7950,0.4808,1.654],[40,0.6200,0.4808,1.290]],
    literature:{compoundsWithStrippedValues:155,deliveredCompounds:276,strippedValues:310,uniqueDocuments:65},
    decisions:[
      ["Endpoint","Strict Ki-only R² 0.5685 vs pooled R² 0.4768; D1 unresolved."],
      ["Domain floor","PDF delivery 0.50 vs frozen plan 0.55; D2 unresolved. The 276 count depends on this choice."],
      ["Interval width","Delivered half-width 1.2588 vs plan 1.299; one must be retired before promotion."],
      ["Our frozen pipeline","Different 78-molecule development comparison, 2,048-bit fingerprint, and 240 held / 0 eligible external queue."]
    ]
  };
  let overviewPrecisionN=10;
  function renderOverviewPrecision(){
    const rows=teammatePdf.precision;
    const x=index=>44+index*136,y=value=>145-value*1.15;
    const precisionPoints=rows.map((row,index)=>`${x(index)},${y(row[1]*100)}`).join(" ");
    const basePoints=rows.map((row,index)=>`${x(index)},${y(row[2]*100)}`).join(" ");
    const dots=rows.map((row,index)=>`<circle cx="${x(index)}" cy="${y(row[1]*100)}" r="${row[0]===overviewPrecisionN?7:5}" class="${row[0]===overviewPrecisionN?"selected":""}"/><text x="${x(index)}" y="165" text-anchor="middle">N=${row[0]}</text>`).join("");
    const selected=rows.find(row=>row[0]===overviewPrecisionN);
    $("overview-precision-chart").innerHTML=`<svg viewBox="0 0 360 180" role="img" aria-label="Teammate PDF reported precision declines from 96 percent at N 10 to 62 percent at N 40; reported base rate is 48.08 percent"><line x1="44" y1="145" x2="316" y2="145" class="axis"/><line x1="44" y1="87" x2="316" y2="87" class="grid"/><text x="8" y="90">50%</text><polyline points="${basePoints}" class="base-line"/><polyline points="${precisionPoints}" class="precision-line"/>${dots}</svg><div class="chart-switch" role="group" aria-label="Reported set size">${rows.map(row=>`<button type="button" data-overview-n="${row[0]}" class="${row[0]===overviewPrecisionN?"active":""}" aria-pressed="${row[0]===overviewPrecisionN}">N=${row[0]}</button>`).join("")}</div><p class="chart-note"><b>${fmt(selected[1]*100,1)}%</b> reported precision at N=${overviewPrecisionN}; PDF base rate ${fmt(selected[2]*100,2)}%. Not a prospective probability.</p>`;
    $("overview-precision-chart").querySelectorAll("[data-overview-n]").forEach(button=>button.addEventListener("click",()=>{overviewPrecisionN=Number(button.dataset.overviewN);renderOverviewPrecision();}));
  }
  renderOverviewPrecision();
  $("teammate-source-hash").textContent=teammatePdf.sha256;
  $("teammate-metrics").innerHTML=[
    ["PDF screen-eligible",teammatePdf.funnel[3][1].toLocaleString(),"Provisional; not our queue"],
    ["PDF scaffolds",teammatePdf.scaffolds.screenEligible,"One reported review set"],
    ["Separable pairs",`${fmt(teammatePdf.pairwise.fraction,2)}%`,"No defensible ordinal positions"],
    ["Our eligible queue",data.summary.uncertainty_queue_eligible,"Frozen and independently governed"]
  ].map(([name,value,note])=>`<div class="reference-metric"><span>${esc(name)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`).join("");
  const libraryCount=teammatePdf.funnel[0][1];
  const stageDescriptions=[
    "The PDF reports 2,963 library rows after its deterministic intake pass.",
    "423 rows meet the PDF's applicability rule; its 0.50 similarity threshold remains disputed.",
    "335 in-domain rows are assigned to the antagonist class across 149 scaffolds. The other 88 are not ordered.",
    "276 rows across 120 scaffolds meet the PDF's non-exclusion rule. They are not certified hits or members of our frozen queue."
  ];
  let funnelMode="count",selectedFunnelStage=3;
  function renderTeammateFunnel(){
    $("teammate-funnel").innerHTML=teammatePdf.funnel.map(([name,count],index)=>`<button type="button" class="reference-bar-row ${selectedFunnelStage===index?"selected":""}" data-stage="${index}" aria-pressed="${selectedFunnelStage===index}"><span><strong>${esc(name)}</strong><b>${funnelMode==="count"?Number(count).toLocaleString():`${fmt(count/libraryCount*100,1)}%`}</b></span><span class="reference-track"><i style="width:${count/libraryCount*100}%"></i></span></button>`).join("");
    $("teammate-funnel-detail").textContent=stageDescriptions[selectedFunnelStage];
    document.querySelectorAll("#teammate-funnel [data-stage]").forEach(button=>button.addEventListener("click",()=>{selectedFunnelStage=Number(button.dataset.stage);renderTeammateFunnel();}));
  }
  document.querySelectorAll("#teammate-funnel-mode [data-mode]").forEach(button=>button.addEventListener("click",()=>{funnelMode=button.dataset.mode;document.querySelectorAll("#teammate-funnel-mode button").forEach(item=>{const active=item===button;item.classList.toggle("active",active);item.setAttribute("aria-pressed",String(active));});renderTeammateFunnel();}));
  renderTeammateFunnel();
  $("teammate-separability").innerHTML=`<div class="reference-big-number">${fmt(teammatePdf.pairwise.fraction,2)}%</div><p class="reference-note">${teammatePdf.pairwise.separable.toLocaleString()} of ${teammatePdf.pairwise.total.toLocaleString()} PDF candidate pairs had non-overlapping calibrated 90% intervals. The largest adjacent prediction gap was ${fmt(teammatePdf.pairwise.largestAdjacentGap,4)} pKi, below the ${fmt(teammatePdf.pairwise.requiredGap,4)} separation requirement.</p><div class="reference-rule"><b>Admission ≠ hit prediction</b><span>PDF rule: predicted pKi ≥ ${fmt(teammatePdf.interval.upperBoundCutoff,4)} only means the upper 90% bound reaches ${fmt(teammatePdf.interval.hitBar,1)}. It does not certify a hit.</span></div>`;
  function comparisonBar(name,value,percent,tone="primary"){return `<div class="reference-comparison-row"><span>${esc(name)}</span><strong>${esc(value)}</strong><div class="reference-comparison-track"><i class="${tone}" style="width:${Math.max(0,Math.min(100,percent))}%"></i></div></div>`;}
  function renderSeparation(mode){
    if(mode==="development"){
      const stress=teammatePdf.developmentStress;
      $("teammate-separation-chart").innerHTML=`<p class="reference-note">Separate ${stress.n}-molecule development population. Narrowing intervals fourfold changes both separability and coverage:</p>${comparisonBar("Calibrated separability",`${fmt(stress.calibrated.separablePercent,1)}%`,stress.calibrated.separablePercent)}${comparisonBar("Fourfold-narrowed separability",`${fmt(stress.narrowed.separablePercent,1)}%`,stress.narrowed.separablePercent,"warning")}${comparisonBar("Calibrated coverage",`${fmt(stress.calibrated.coverage*100,2)}%`,stress.calibrated.coverage*100)}${comparisonBar("Narrowed coverage",`${fmt(stress.narrowed.coverage*100,2)}%`,stress.narrowed.coverage*100,"warning")}<p class="reference-note">Higher apparent separation is bought by losing interval coverage. These 74 molecules are not the 335-candidate pool.</p>`;
    }else{
      $("teammate-separation-chart").innerHTML=`${comparisonBar("Pairs distinguishable",`${fmt(teammatePdf.pairwise.fraction,2)}%`,teammatePdf.pairwise.fraction)}${comparisonBar("Pairs overlapping",`${fmt(100-teammatePdf.pairwise.fraction,2)}%`,100-teammatePdf.pairwise.fraction,"muted")}<p class="reference-note">Population: 335 PDF antagonist candidates; ${teammatePdf.pairwise.total.toLocaleString()} possible pairs. The PDF reports one connected interval-overlap component, so no ordinal list is presented.</p>`;
    }
  }
  document.querySelectorAll("[data-separation]").forEach(button=>button.addEventListener("click",()=>{document.querySelectorAll("[data-separation]").forEach(item=>{const active=item===button;item.classList.toggle("active",active);item.setAttribute("aria-pressed",String(active));});renderSeparation(button.dataset.separation);}));
  renderSeparation("candidates");
  function renderPrecision(size){
    const [n,precision,base,ef]=teammatePdf.precision.find(row=>row[0]===size);
    $("teammate-precision-chart").innerHTML=`${comparisonBar(`N=${n} reported precision`,`${fmt(precision*100,2)}%`,precision*100)}${comparisonBar("Reference base rate",`${fmt(base*100,2)}%`,base*100,"muted")}<div class="reference-ef"><b>${fmt(ef,3)}×</b><span>reported enrichment factor at N=${n}</span></div>`;
    $("teammate-precision").innerHTML=`<div class="reference-precision-head"><span>Set size</span><span>Precision</span><span>Base rate</span><span>Enrichment</span></div>`+teammatePdf.precision.map(([rowN,rowPrecision,rowBase,rowEf])=>`<div class="reference-precision-row ${rowN===n?"selected":""}"><b>N = ${rowN}</b><span>${fmt(rowPrecision,4)}</span><span>${fmt(rowBase,4)}</span><span>${fmt(rowEf,3)}×</span></div>`).join("");
  }
  document.querySelectorAll("#teammate-precision-selector [data-size]").forEach(button=>button.addEventListener("click",()=>{document.querySelectorAll("#teammate-precision-selector button").forEach(item=>{const active=item===button;item.classList.toggle("active",active);item.setAttribute("aria-pressed",String(active));});renderPrecision(Number(button.dataset.size));}));
  renderPrecision(10);
  const literature=teammatePdf.literature;
  $("teammate-literature").innerHTML=`<div><strong>${literature.compoundsWithStrippedValues}/${literature.deliveredCompounds}</strong><span>PDF compounds with stripped published potency values</span><div class="reference-comparison-track"><i class="primary" style="width:${literature.compoundsWithStrippedValues/literature.deliveredCompounds*100}%"></i></div></div><div><strong>${literature.strippedValues}</strong><span>values removed before extraction</span></div><div><strong>${literature.uniqueDocuments}</strong><span>unique documents reported</span></div>`;
  $("teammate-decisions").innerHTML=teammatePdf.decisions.map(([name,detail])=>`<div class="reference-decision"><strong>${esc(name)}</strong><span>${esc(detail)}</span></div>`).join("");
  $("teammate-download").addEventListener("click",()=>{
    const payload=JSON.stringify(teammatePdf,null,2)+"\n";
    const url=URL.createObjectURL(new Blob([payload],{type:"application/json"}));
    const link=document.createElement("a");link.href=url;link.download="a2a_teammate_pdf_reported_aggregates.json";document.body.append(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  });

  const gates=[
    ["G0–G1","Sources & evidence admission","Development evidence frozen; external pass 2 froze at zero","passed"],
    ["G4–G6","Governed eligibility","Prediction, interval, threshold, provenance, and identity must all be verified","review"],
    ["Review","Unordered human queue","Membership and scaffold composition only; no scientific ordering","review"],
    ["Release","Human authority","Blocked: external floors failed and human approval is absent","blocked"]
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

  const sprint=records("shadow_evidence_sprint")[0];
  if(sprint){
    const counts=sprint.counts;
    $("shadow-evidence-summary").innerHTML=`<div><strong>${counts.publication_groups_checked}/${counts.publication_groups_with_missing_text}</strong><span>source groups checked</span></div><div><strong>${counts.affected_candidates_in_checked_groups}</strong><span>linked records needing source text</span></div><div><strong>${counts.metadata_verified}</strong><span>citations verified</span></div><div><strong>${counts.open_access_metadata_flags}</strong><span>open-access flags</span></div>`;
    $("shadow-evidence-publications").innerHTML=sprint.checked_publications.map(item=>`<article class="evidence-sprint-card"><div><span class="status-pill ${item.title_target_flag==="other_receptor_focus_in_title"?"blocked":"review"}">${esc(item.title_target_flag==="other_receptor_focus_in_title"?"Check receptor focus":label(item.access_status))}</span><strong>${item.affected_count} linked records</strong></div><h3>${esc(item.title_from_frozen_packet||item.source_key)}</h3><p>${esc(item.source_key)} · DOI ${esc(item.doi||"unresolved")}</p><small>${esc(item.title_target_flag==="other_receptor_focus_in_title"?"Title focuses on another receptor subtype; inspect source before A2A use.":item.open_access===true?"Open access indicated; source review pending":"No open-access flag; source text remains missing")}</small>${item.source_url?`<a href="${esc(safeUrl(item.source_url))}" target="_blank" rel="noopener noreferrer">Check publication ↗</a>`:""}</article>`).join("");
    const reviewRecords=sprint.source_grounded_review||[];
    function renderReviewPacket(){
      const query=$("review-packet-search").value.trim().toLowerCase();
      const rows=reviewRecords.filter(item=>`${item.candidate_id} ${item.publication_title} ${item.source_ids.join(" ")} ${item.unresolved_fields.join(" ")}`.toLowerCase().includes(query));
      $("review-packet-count").textContent=`${rows.length} of ${reviewRecords.length} unresolved records`;
      $("review-packet-list").innerHTML=rows.map(item=>`<details class="review-packet-card"><summary><strong>${esc(item.candidate_id)}</strong><span>${esc(item.publication_title)}</span><small>${item.unresolved_fields.length} unresolved fields</small></summary><div class="review-packet-body"><p><b>Missing:</b> ${esc(item.unresolved_fields.map(label).join(", "))}</p><p><b>Action:</b> ${esc(item.review_action)}</p><p><b>Frozen reasons:</b> ${esc(item.frozen_quarantine_reasons.map(label).join(", "))}</p><div class="review-packet-sources">${item.source_urls.map((url,index)=>`<a href="${esc(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${esc(item.source_ids[index]||"Source")} ↗</a>`).join("")}</div><div class="source-line">Source XML SHA-256 · ${esc(Object.entries(item.source_xml_sha256).map(([id,hash])=>`${id}: ${hash}`).join(" · "))}<br>InChIKey · ${esc(item.inchikey)}<br>Frozen external cohort unchanged · no numeric outcome extracted</div></div></details>`).join("")||'<p class="empty-state">No records match this search.</p>';
    }
    $("review-packet-search").addEventListener("input",renderReviewPacket);renderReviewPacket();
  }

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
    $("model-grid").innerHTML=models.map(row=>`<article class="model-card ${row.model_id==="AB_Ridge"?"primary":""}"><span class="kicker">${esc(row.role)}</span><span class="lock">${row.model_id==="AB_Ridge"?"Shadow scorer only":"Not deployed"}</span><h3>${esc(row.display_name)}</h3><div class="score">${fmt(row.r2,3)}</div><small>R² · RMSE ${fmt(row.rmse,3)} · MAE ${fmt(row.mae,3)}</small><div class="source-line">${esc(row.source.path)}</div></article>`).join("");
  }
  document.querySelectorAll("#metric-toggle button").forEach(button=>button.addEventListener("click",()=>{modelMetric=button.dataset.metric;document.querySelectorAll("#metric-toggle button").forEach(item=>item.classList.toggle("active",item===button));renderModels();}));renderModels();

  const domain=records("applicability_uncertainty")[0],domainTotal=domain.inside_n+domain.outside_n,insidePercent=domain.inside_n/domainTotal*100;
  $("domain-panel").innerHTML=`<div class="domain-visual"><div class="donut" style="--inside:${insidePercent*3.6}deg"><div><strong>${fmt(insidePercent,1)}%</strong><span>inside domain</span></div></div><div class="domain-copy"><dl><dt>Inside</dt><dd>${domain.inside_n}</dd><dt>Outside</dt><dd>${domain.outside_n}</dd><dt>Tanimoto floor</dt><dd>${domain.similarity_threshold}</dd><dt>Descriptor distance</dt><dd>${fmt(domain.descriptor_distance_threshold,3)}</dd></dl><p>Development grouped out-of-fold scope only.</p></div></div>`;
  const ci=domain.r2_interval,scaleMin=.3,scaleMax=.75,left=(ci.lower-scaleMin)/(scaleMax-scaleMin)*100,width=(ci.upper-ci.lower)/(scaleMax-scaleMin)*100,point=(ci.estimate-scaleMin)/(scaleMax-scaleMin)*100;
  $("uncertainty-panel").innerHTML=`<div class="interval"><strong>${fmt(ci.estimate,3)}</strong><span>bootstrap estimate</span><div class="interval-track"><i style="left:${left}%;width:${width}%"></i><b style="left:${point}%"></b></div><span>95% interval · ${fmt(ci.lower,3)}–${fmt(ci.upper,3)}</span></div><div class="source-line">${esc(domain.source.path)} · ${short(domain.source.sha256)}</div>`;

  const dockingRows=records("dual_state_docking");
  function dockingGroups(){return dockingRows.reduce((acc,row)=>{(acc[row.molecule_id]??=[]).push(row);return acc;},{});}
  function renderDocking(){
    const groups=Object.entries(dockingGroups()).map(([id,rows])=>{const inactive=rows.find(row=>row.receptor_state==="inactive"),active=rows.find(row=>row.receptor_state==="active-like");return{id,inactive,active,delta:active.median_affinity_kcal_mol-inactive.median_affinity_kcal_mol};}).sort((a,b)=>a.id.localeCompare(b.id));
    $("docking-grid").innerHTML=groups.map(group=>`<article class="docking-card"><header><div><span class="kicker">Label blind · historical structural context</span><h2>${esc(group.id.replace("LIT25-",""))}</h2></div><span class="status-pill shadow">No queue effect</span></header><div class="state-pair"><div class="state-box"><span>5NM4 inactive</span><strong>${fmt(group.inactive.median_affinity_kcal_mol,2)}</strong><small>kcal/mol · CNN ${fmt(group.inactive.median_cnn_score,3)}</small></div><div class="state-box active"><span>2YDO active-like</span><strong>${fmt(group.active.median_affinity_kcal_mol,2)}</strong><small>kcal/mol · CNN ${fmt(group.active.median_cnn_score,3)}</small></div></div><div class="delta-line"><span>Descriptive state difference</span><b>${group.delta>0?"+":""}${fmt(group.delta,3)} kcal/mol</b></div><p>Not an admission, priority, ordering, or release signal.</p><div class="source-line">${esc(group.inactive.source.path)} · retained poses hashed</div></article>`).join("");
  }
  renderDocking();

  const md=records("md_gates");
  $("md-gates").innerHTML=md.map(gate=>{const isEquil=gate.gate_id.includes("equilibration"),isProduction=gate.gate_id.includes("production"),tone=isEquil?"passed":isProduction?"authorized":"locked",pct=isProduction?Math.round((gate.completion_fraction_by_reported_ns||0)*100):(gate.required_runs?Math.round(gate.passed_runs/gate.required_runs*100):0);return `<article class="md-card ${tone}"><div class="progress-ring" style="--progress:${pct*3.6}deg"><span>${isProduction?`${pct}%`:`${gate.passed_runs}/${gate.required_runs}`}</span></div><span class="kicker">Optional mechanistic context</span><h2>${isEquil?"Historical equilibration complete":isProduction?"Historical pilot incomplete":"Historical Tier B locked"}</h2><span class="status-pill ${tone}">${esc(label(gate.status))}</span><p>${esc(gate.claim_limit)}</p><p>Not required for review-queue membership, dashboard operation, or release.</p><div class="source-line">${esc(gate.source.path)}</div></article>`;}).join("");
  $("production-progress-copy").textContent=`${data.summary.tier_a_production_observed_replicas}/6 replicas observed, ${data.summary.tier_a_production_completed_replicas} complete, ${data.summary.tier_a_production_reported_ns}/${data.summary.tier_a_production_required_ns} ns reported at cutoff. Historical Tier B remains locked; this does not affect the review queue or release.`;
  const mdSource=md[0],missing=new Set(mdSource.missing_audits.map(path=>path.split("/").slice(0,2).join(":"))),systems=["5NM4_ZMA_native","5G53_NECA_miniGs_native_nucleotide_free"],seeds=[20260914,20260915,20260916];
  let matrix=`<div class="md-cell header">System</div>${seeds.map(seed=>`<div class="md-cell header">Seed ${seed}</div>`).join("")}`;systems.forEach(system=>{matrix+=`<div class="md-cell header">${esc(label(system))}</div>`;seeds.forEach(seed=>{const absent=missing.has(`${system}:seed-${seed}`);matrix+=`<div class="md-cell ${absent?"missing":"pass"}">${absent?"Missing audit":"Gate passed"}</div>`;});});$("md-matrix").innerHTML=matrix;

  const reviewQueue=records("candidate_portfolio")[0],composition=Object.entries(reviewQueue.scaffold_composition);
  $("portfolio-board").innerHTML=`<article class="portfolio-card"><header><div><span class="kicker">Unordered composition only</span><h2>Human-review evidence queue</h2></div><span class="status-pill blocked">${esc(label(reviewQueue.status))}</span></header><div class="portfolio-metrics"><div><span>Records reviewed</span><strong>${reviewQueue.record_count}</strong></div><div><span>Eligible</span><strong>${reviewQueue.eligible_count}</strong></div><div><span>Scaffolds</span><strong>${reviewQueue.scaffold_count}</strong></div></div><p>Admission basis: governed eligibility contract only. Docking is separate structural context; MD is optional mechanistic context. Neither can admit, order, or release a record.</p>${composition.map(([scaffold,count])=>`<div class="scaffold-row"><code>${esc(scaffold)}</code><b>${count}</b></div>`).join("")}<div class="source-line">${esc(reviewQueue.source.path)} · ${short(reviewQueue.source.sha256)}</div></article>`;

  let currentDiscoveryRun=null,discoveryCapabilities=null;
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
    const oldRun=Boolean(run&&capabilities?.ab_ridge_scorer==="development_only"&&(run.molecules||[]).some(item=>item.standardization_state==="cached_precomputed"));
    const providerNote=run?`Latest run: ${esc(label(run.workflow_state))} · requested ${esc(label(run.provider?.requested_mode||"unknown"))} · cached fallback ${run.provider?.cached_fallback_allowed?"allowed":"disabled"}${oldRun?" · predates active RDKit/Ridge; rerun to inspect current gates":""}`:"API keys remain server-side. Explicit live mode never falls back; auto mode may use the cached demo.";
    banner.innerHTML=`<span class="state-dot"></span><div><strong>${live?"Live DeepSeek extraction available":"Cached demo ready · live DeepSeek unavailable"}</strong><small>${providerNote}</small></div><div class="capability-row">${capabilityBadge("RDKit",capabilities?.rdkit||"unavailable")}${capabilityBadge("AB Ridge",capabilities?.ab_ridge_scorer||"unavailable")}</div>`;
  }
  function renderDiscovery(run){
    if(!run)return;currentDiscoveryRun=run;$("discovery-results").hidden=false;$("discovery-run-id").textContent=run.run_id;
    const stateTone=run.workflow_state==="live"?"passed":"shadow";
    const detailValue=value=>value&&typeof value==="object"?`${Object.keys(value).length} resolved contracts`:String(value);
    $("discovery-stages").innerHTML=run.audit_log.map(item=>`<div class="discovery-stage"><span>${String(item.sequence).padStart(2,"0")}</span><div><strong>${esc(label(item.event_type))}</strong><small>${esc(Object.entries(item.details).map(([key,value])=>`${label(key)}: ${detailValue(value)}`).join(" · "))}</small></div><i class="status-pill ${stateTone}">${run.workflow_state==="live"?"live":"cached"}</i></div>`).join("");
    $("source-count").textContent=`${run.sources.length} cited records · ${label(run.workflow_state)}`;
    $("discovery-sources").innerHTML=run.sources.map(source=>{const extraction=run.extractions.find(item=>item.source_id===source.source_id)||{};return `<article class="source-card"><div class="source-badges"><span class="status-pill ${source.retrieval_state==="live"?"passed":"shadow"}">${esc(source.retrieval_state)}</span><span class="status-pill ${extraction.evidence_quality==="quarantine"?"blocked":"review"}">${esc(extraction.evidence_quality||"unresolved")}</span></div><h3>${esc(source.title)}</h3><p>${esc(extraction.reason||"No extraction rationale returned.")}</p><a href="${esc(safeUrl(source.url))}" target="_blank" rel="noopener noreferrer">${esc(source.source_id)} · source ↗</a><small>DOI ${esc(source.doi||"unresolved")} · full text ${esc(source.full_text_state||"unresolved")}</small></article>`;}).join("")||'<p class="empty-state">No citable sources returned.</p>';
    const queue=run.screen_eligible_queue,eligibility=queue.eligibility_contract||records("uncertainty_review_queue")[0].eligibility_contract;$("queue-count").textContent=`${queue.count} ${eligibility.display_label}`;
    $("discovery-queue").innerHTML=`<div class="queue-summary"><strong>${queue.count}</strong><span>${esc(eligibility.display_label)} records</span><dl><dt>Scaffolds</dt><dd>${queue.scaffold_count}</dd><dt>Ordering</dt><dd>Composition only</dd><dt>Decision rule</dt><dd>Validated 90% upper bound ≥ verified threshold</dd></dl><p>${esc(eligibility.claim_limit)}</p></div>${Object.entries(queue.scaffold_composition).map(([scaffold,count])=>`<div class="scaffold-row"><code>${esc(scaffold)}</code><b>${count}</b></div>`).join("")}`;
    $("discovery-molecule-grid").innerHTML=run.molecules.map(molecule=>`<article class="registry-card ${molecule.screen_eligible?"control":"candidate"}"><header><span class="tag">${esc(molecule.state_label)}</span><span class="status-pill ${molecule.screen_eligible?"passed":"blocked"}">${esc(molecule.screen_eligible?eligibility.display_label:label(molecule.eligibility_state))}</span></header><h2>${esc(molecule.name)}</h2><small>${esc(molecule.molecule_id)}</small><p>Identity · ${esc(label(molecule.standardization_state))}<br>Domain · ${esc(label(molecule.applicability))}<br>Uncertainty · ${esc(label(molecule.uncertainty))}<br>AB Ridge · ${esc(label(molecule.score_state))}${Number.isFinite(molecule.provisional_score)?`<br>Exploratory development-fit pKi · ${fmt(molecule.provisional_score,3)} <small>(not a validated interval or rank)</small>`:""}</p><div class="eligibility-note">${esc(molecule.eligibility_reasons.join(" ")||"No gate rationale recorded.")}</div><div class="source-line">${esc(molecule.canonical_smiles||molecule.input_smiles)}${molecule.model_artifact_sha256?` · scorer ${esc(short(molecule.model_artifact_sha256,12))}`:""}</div></article>`).join("")||'<p class="empty-state">No molecule records were submitted.</p>';
    $("disposition-state").textContent=label(run.human_disposition.status);$("disposition-state").className=`status-pill ${run.human_disposition.status==="pending"?"review":"passed"}`;
  }
  function parseMoleculeInput(value){return value.split(/\n+/).map(line=>{const [name,...smilesParts]=line.split("|");return{name:(name||"").trim(),smiles:smilesParts.join("|").trim()};}).filter(item=>item.smiles);}
  let activeDiscoveryJob=null,discoveryPoll=null;
  function showDiscoveryJob(job){
    activeDiscoveryJob=job;
    const busy=job&&["queued","running"].includes(job.status);
    $("discovery-run").disabled=Boolean(busy);$("discovery-run").textContent=busy?"Run in progress…":"Run shadow workflow";
    $("discovery-cancel").hidden=!busy;
    $("discovery-job-status").textContent=job?`${job.run_id} · ${label(job.status)} · ${label(job.stage)}${job.error?` · ${job.error}`:""}`:"No active run.";
    if(job&&job.status!=="completed"&&job.run_id!==currentDiscoveryRun?.run_id){currentDiscoveryRun=null;$("discovery-results").hidden=true;$("discovery-run-id").textContent=job.run_id;$("discovery-stages").innerHTML=`<p class="${job.status==="failed"?"error-state":"empty-state"}">${esc(job.error||`Run ${label(job.status)} · ${label(job.stage)}`)}</p>`;}
    if(job?.status==="completed"&&job.result){renderDiscovery(job.result);updateDiscoveryBanner(discoveryCapabilities,job.result);}
  }
  async function pollDiscoveryJob(runId){
    clearTimeout(discoveryPoll);
    try{const payload=await apiJson(`/api/discovery/runs/${encodeURIComponent(runId)}`);showDiscoveryJob(payload.job);if(["queued","running"].includes(payload.job.status))discoveryPoll=setTimeout(()=>pollDiscoveryJob(runId),1500);}
    catch(error){$("discovery-job-status").textContent=`Run status unavailable: ${error.message}`;discoveryPoll=setTimeout(()=>pollDiscoveryJob(runId),4000);}
  }
  $("discovery-form").addEventListener("submit",async event=>{
    event.preventDefault();const button=$("discovery-run");button.disabled=true;button.textContent="Starting run…";
    try{const payload=await apiJson("/api/discovery/run",{method:"POST",body:JSON.stringify({query:$("discovery-query").value,provider_mode:$("discovery-provider").value,molecules:parseMoleculeInput($("discovery-molecules").value)})});showDiscoveryJob(payload.job);pollDiscoveryJob(payload.job.run_id);}
    catch(error){$("discovery-stages").innerHTML=`<p class="error-state">${esc(error.message)}</p>`;}
    finally{if(!activeDiscoveryJob||!["queued","running"].includes(activeDiscoveryJob.status)){button.disabled=false;button.textContent="Run shadow workflow";}}
  });
  $("discovery-cancel").addEventListener("click",async()=>{if(!activeDiscoveryJob)return;try{const payload=await apiJson(`/api/discovery/runs/${encodeURIComponent(activeDiscoveryJob.run_id)}/cancel`,{method:"POST",body:"{}"});clearTimeout(discoveryPoll);showDiscoveryJob(payload.job);}catch(error){$("discovery-job-status").textContent=`Cancellation failed: ${error.message}`;}});
  $("disposition-form").addEventListener("submit",async event=>{
    event.preventDefault();if(!currentDiscoveryRun)return;
    try{const payload=await apiJson("/api/discovery/disposition",{method:"POST",body:JSON.stringify({run_id:currentDiscoveryRun.run_id,status:$("disposition-choice").value,reviewer:$("disposition-reviewer").value,note:$("disposition-note").value})});renderDiscovery(payload.run);}
    catch(error){$("disposition-state").textContent=error.message;$("disposition-state").className="status-pill blocked";}
  });
  apiJson("/api/discovery/status").then(payload=>{discoveryCapabilities=payload.capabilities;updateDiscoveryBanner(discoveryCapabilities,payload.latest_run);if(payload.latest_run)renderDiscovery(payload.latest_run);if(payload.latest_job){showDiscoveryJob(payload.latest_job);if(["queued","running"].includes(payload.latest_job.status))pollDiscoveryJob(payload.latest_job.run_id);}}).catch(error=>{$("discovery-state-banner").innerHTML=`<span class="state-dot"></span><div><strong>Discovery endpoint unavailable</strong><small>${esc(error.message)}</small></div>`;});

  $("shadow-workflow").innerHTML=shadowActions.map((action,index)=>`<article class="shadow-card ${esc(action.status)}"><span class="kicker">Step ${String(index+1).padStart(2,"0")}</span><h2>${esc(action.stage)}</h2><div class="executor">${esc(action.executor)} · ${esc(label(action.status))}</div><p>${esc(action.authority)}</p><div class="gate"><b>Required gate</b><br>${esc(action.required_gate)}</div><div class="source-line">${esc(action.source.path)}<br>${short(action.source.sha256,16)}</div></article>`).join("");
  const prohibited=[...new Set(shadowActions.flatMap(action=>action.prohibited_actions))];$("prohibited-grid").innerHTML=prohibited.map(item=>`<span>${esc(label(item))}</span>`).join("");

  const audit=records("audit_log");$("audit-count").textContent=`${audit.length} linked entries`;
  $("audit-list").innerHTML=audit.map(entry=>`<article class="audit-item"><span>#${String(entry.sequence).padStart(4,"0")}</span><div><strong>${esc(label(entry.action))}</strong><small>${esc(entry.record_type)}</small></div><div><strong>${esc(entry.record_id)}</strong><code>${esc(entry.source.path)}</code></div><div><code>${short(entry.entry_hash,16)}</code><small>prev ${short(entry.previous_entry_hash,10)}</small></div></article>`).join("");

  const requested=location.hash.slice(1);setView(views.includes(requested)?requested:"overview");
})();
