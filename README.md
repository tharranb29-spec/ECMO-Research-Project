# ECMO Ligand Ranking Prototype

## Track 3 A2A dashboard

The audited Track 3 competition interface is available at
`track3-dashboard.html` and is served at `/` by `research_assistant_server.py`.
The preserved legacy ECMO dashboard remains at `/dashboard.html`. The new interface presents versioned
contracts for evidence intake, molecule and model registries, applicability and
uncertainty, dual-state docking, MD gates, the candidate portfolio, a bounded
shadow-action workflow, an interactive Discovery Lab, and hash-chained audit logs.

Rebuild its deterministic static data bundle after audited artifacts change:

```bash
python3 build_track3_dashboard.py
python3 -m unittest tests.test_track3_dashboard
```

Autonomous records remain shadow proposals. The dashboard cannot admit labels,
promote a model, unlock Tier B, or describe a candidate as experimentally validated.
The Render blueprint disables legacy background literature automation and
prototype GNINA. The Discovery Lab is request-driven, shadow-only, and stores only
its latest ephemeral run; it cannot mutate the frozen scientific artifacts.

The **Teammate analysis** view is an attributed, provisional transcription of
aggregate figures from a supplied PDF. It is visually and computationally
separate from the frozen 240-record review queue. Its source, page references,
unresolved protocol differences, and reproducibility limits are recorded in
`track3_a2a/TEAMMATE_PDF_REFERENCE_2026-09-22.md`; the PDF itself is not published.

### Discovery Lab demo

```bash
python3 build_dashboard_bundle.py
python3 build_track3_dashboard.py
AUTO_RESEARCH_ENABLED=0 AUTO_RESEARCH_LLM_ENABLED=0 GNINA_MODE=disabled \
  python3 research_assistant_server.py
```

Open `http://127.0.0.1:8765/#discovery` and choose **Deterministic cached demo**.
No key is required. The demonstration labels cached source metadata and simulated
applicability separately, leaves AB_Ridge scores unavailable, and records a
hash-chained human disposition.

For live source retrieval, configure `DEEPSEEK_API_KEY` only on the server and use
Auto mode. Europe PMC supplies deterministic source records and citations; DeepSeek
performs structured extraction through its server-side chat API and is never used
as a potency oracle. RDKit standardization is activated when
RDKit is installed. Without RDKit or a serialized frozen AB_Ridge scorer, those
gates fail closed rather than generating substitute values.

```bash
python3 -m unittest tests.test_track3_dashboard tests.test_track3_discovery_workflow
```

This folder now contains a rough, trainable ranking prototype for the AI-driven part of your ECMO biomaterials project.

It is intentionally a seed model, not a final discovery engine.

## What is included

- `data/seed_ligands.json`
  Literature-curated seed records for `Siglec-9` and `SIRPa/CD47`-related ligands and controls.
- `ecmo_seed_ranker.py`
  A lightweight Python ranking script that trains separate target-specific hybrid linear models.
- `data/custom_candidate_template.csv`
  A simple template for scoring your own candidate ligands later.
- `outputs/`
  Generated ranking results and a markdown report after the script is run.

## What the model is doing

The script trains one small model for `Siglec-9` and one for `SIRPa`.

Each model learns from a literature-seeded feature table using these inputs:

- `affinity_strength_score`
- `specificity_score`
- `functional_immunomodulation_score`
- `surface_validation_score`
- `conjugation_feasibility_score`
- `hemocompatibility_proxy_score`
- `multivalency_or_clustering_score`
- `literature_confidence_score`

This is a hybrid model because it combines:

- prior rubric weights based on your ECMO project logic
- small-data fitting to the seed examples

That helps avoid pretending we already have enough wet-lab data for a full ML model.

## How to run

Rank the seed set itself:

```bash
python3 ecmo_seed_ranker.py
```

Rank your own candidate file:

```bash
python3 ecmo_seed_ranker.py --input data/custom_candidate_template.csv --json-out outputs/custom_results.json --report-out outputs/custom_report.md
```

## Presentable dashboard

Build the browser-friendly dashboard bundle:

```bash
python3 build_dashboard_bundle.py
```

Then open:

- `dashboard.html`

This page reads the bundled model outputs and shows the rankings as a presentation-friendly dashboard.

You can edit dashboard branding in:

- `dashboard-config.json`

## Full live research assistant

For a real conversational assistant inside the dashboard, use:

- `research_assistant_server.py`
- `assistant.env.example`

Recommended setup:

1. Set your API key in the shell

```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key_here"
```

2. Optional model override

```bash
export DEEPSEEK_MODEL="deepseek-chat"
```

3. Make sure the latest dashboard bundle exists

```bash
python3 build_dashboard_bundle.py
```

4. Start the local server

```bash
python3 research_assistant_server.py
```

5. Open the dashboard in your browser

```text
http://127.0.0.1:8765/dashboard.html
```

The live assistant can answer broader questions and reason over fresh pasted notes from the dashboard context box.

## Autonomous updating

The dashboard can now run with a background literature updater.

When the live server is running with `AUTO_RESEARCH_ENABLED=1`, it will:

- search recent literature for Siglec-9 and SIRPa/CD47 ligand-related papers
- extract literature candidate leads
- optionally use DeepSeek to improve lead extraction and filter out generic biology terms
- convert those leads into provisional candidate records
- score those provisional candidates with the existing ranking model
- refresh dashboard data in the background
- rebuild the bundled dashboard data automatically

The front-end also polls the live server for fresh bundle data while the page stays open.

The dashboard now includes:

- a `Autonomous Discovery` dataset tab
- an `Autonomous Research Leads` panel
- autonomous runtime status cards and a manual `Refresh Now` action in the live dashboard
- `outputs/autonomous_ranking_results.json`
- `outputs/autonomous_ranking_report.md`

Default cadence:

- `AUTO_RESEARCH_INTERVAL_SECONDS=3600` for hourly refreshes

Useful environment variables:

- `AUTO_RESEARCH_ENABLED=1`
- `AUTO_RESEARCH_INTERVAL_SECONDS=3600`
- `AUTO_RESEARCH_LLM_ENABLED=1`
- `AUTO_RESEARCH_MAX_ARTICLES=12`

### DeepSeek configuration

DeepSeek is the only live LLM provider. Set:

```bash
export AI_PROVIDER="deepseek"
export DEEPSEEK_API_KEY="your_deepseek_api_key_here"
export DEEPSEEK_MODEL="deepseek-chat"
export AUTO_RESEARCH_ENABLED="1"
export AUTO_RESEARCH_INTERVAL_SECONDS="3600"
export AUTO_RESEARCH_LLM_ENABLED="1"
```

Then start the same server:

```bash
python3 research_assistant_server.py
```

The dashboard backend, Discovery Lab, and optional autonomous extraction all use
DeepSeek. No API key is included in browser code or committed configuration.

Important hosting note:

- if your host sleeps inactive services, the autonomous updater cannot truly run unattended while the service is asleep
- the live server now triggers a stale refresh when the dashboard is opened again, so the data can catch up automatically after inactivity

Fastest option:

```bash
./launch_deepseek_dashboard.sh
```

That launcher will securely prompt for your DeepSeek API key in Terminal, refresh the outputs, and start the server for you.

If you want the dashboard to keep running in the background, use:

```bash
./start_dashboard_background.sh
```

To stop it later:

```bash
./stop_dashboard_background.sh
```

## Hosting for your team

There are two different hosting paths depending on what you want to share.

### Option 1: Static dashboard only

Use this if your team only needs to view the ranked dashboard pages and bundled data.

Good fit:

- GitHub Pages

Limitation:

- no live assistant backend
- no autonomous updater running on the host

### Option 2: Full live app

Use this if your team needs:

- the conversational assistant
- autonomous literature updates
- live dashboard refreshes

Good fit:

- Render Web Service

This repo includes:

- `render.yaml`

That gives you a straightforward route to deploy the Python server as a web app.

## Ask questions in the dashboard

The dashboard includes a local question box for focused result questions.

Example prompts:

- `What is the top candidate overall?`
- `What is the top candidate for Siglec-9?`
- `Why is pS9L ranked high?`
- `Compare pS9L and MTTSNeu5Ac.`
- `Show all advance candidates.`
- `Given these new docking notes, where would this candidate likely sit in the ranking?`

## Important limitations

- The seed dataset is small and partly qualitative.
- Some feature scores are expert priors derived from published evidence, not direct measurements.
- The current model is best used for `project planning`, `candidate triage`, and `group discussion`.
- Once your preliminary lab experiments start, those data should replace many of the current proxy scores.

## Best next upgrade

The strongest next improvement would be to add your own assay table with:

- ligand sequence or structure
- receptor target
- docking score
- measured affinity if available
- grafting chemistry success
- ROS or NETs readout
- TNF-a and IL-10 change
- hemolysis and platelet adhesion
- final expert decision

Once you have 30 to 100 internally consistent records, we can upgrade this into a much better ranking system.


## GNINA docking prototype

The autonomous discovery workspace now demonstrates this pipeline:

1. Europe PMC literature search finds recent candidate leads.
2. DeepSeek can assist with candidate extraction, but it is instructed not to invent chemical structures.
3. A modality and structure gate routes GNINA-compatible small molecules and glycomimetics into docking.
4. Five seeded runs are aggregated as mean plus standard deviation for minimized affinity, CNNscore, and CNNaffinity.
5. CNNscore acts as a pose-quality gate. Passing candidates rank within each receptor by mean minimized affinity with uncertainty groups.
6. The existing 0-100 model remains a separate translational suitability score and is not presented as binding affinity.
7. Promoted candidates, including their docking evidence, are synchronized into the main review workspace.

GNINA_MODE=prototype is the safe team-demo default. Its numerical outputs are deterministic simulations and are visibly labeled as non-scientific. They prove that the queue, aggregation, ranking, API, and dashboard handoff work end to end.

For real GNINA execution on a Linux worker, set GNINA_MODE=local, install a pinned GNINA binary, and configure prepared target files:

- GNINA_BINARY
- GNINA_RECEPTOR_SIGLEC_9
- GNINA_AUTOBOX_SIGLEC_9
- GNINA_RECEPTOR_SIRPA
- GNINA_AUTOBOX_SIRPA

Each eligible candidate must also have a verified prepared SDF path in ligand_sdf_path. Proteins, antibodies, and large peptides are deliberately not scored by GNINA; they require a suitable protein or peptide docking workflow.

Run the current prototype manually:

    python3 gnina_pipeline.py --from-existing --mode prototype
    python3 build_dashboard_bundle.py
    python3 research_assistant_server.py

The dashboard's Autonomous Discovery workspace includes a Run Docking Pipeline button for the same server-side flow.

### Five-ligand experimental validation batch

Use docking_inputs/siglec9/five_ligand_batch.template.json as the intake schema. For every ligand, replace the placeholder name and path, record the exact structure provenance, add the experimental Kd with its unit and source, and set approved_for_docking to true only after stereochemistry and protonation review.

The teammate's draft command must not use the receptor as --autobox_ligand: GNINA expects a ligand pose or reference ligand for that option. This project also does not use gnina --prepare_receptor, because that option is absent from the pinned GNINA 1.3.3 CLI. Receptor preparation and binding-site validation are separate provenance-controlled steps. If pS9L denotes the full glycopolypeptide rather than a defined small glycan or glycomimetic fragment, it must remain outside this small-molecule GNINA route.

Run the reviewed batch on the Mac Studio with Docker Desktop active:

    GNINA_BINARY=./scripts/gnina-docker \
    GNINA_MODE=local \
    GNINA_EXHAUSTIVENESS=64 \
    GNINA_RUN_COUNT=5 \
    GNINA_SEED_BASE=42 \
    python3 gnina_pipeline.py --manifest docking_inputs/siglec9/five_ligand_batch.json --mode local

Then rebuild the static dashboard data:

    python3 build_dashboard_bundle.py

The dashboard reports minimized affinity in kcal/mol, CNNscore as pose confidence, and CNNaffinity in pK units as separate quantities. Experimental Kd values are converted to pKd before an exploratory Spearman comparison. Prototype values are excluded automatically, and a five-compound analysis must not be presented as general model validation.
