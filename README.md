# ECMO Ligand Ranking Prototype

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
export OPENAI_API_KEY="your_api_key_here"
```

2. Optional model override

```bash
export OPENAI_MODEL="gpt-5.4-mini"
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
- convert those leads into provisional candidate records
- score those provisional candidates with the existing ranking model
- refresh dashboard data in the background
- rebuild the bundled dashboard data automatically

The front-end also polls the live server for fresh bundle data while the page stays open.

The dashboard now includes:

- a `Autonomous Discovery` dataset tab
- an `Autonomous Research Leads` panel
- `outputs/autonomous_ranking_results.json`
- `outputs/autonomous_ranking_report.md`

### Using DeepSeek instead

If you want to use DeepSeek for the live assistant, set:

```bash
export AI_PROVIDER="deepseek"
export DEEPSEEK_API_KEY="your_deepseek_api_key_here"
export DEEPSEEK_MODEL="deepseek-chat"
```

Then start the same server:

```bash
python3 research_assistant_server.py
```

The dashboard backend now supports both OpenAI and DeepSeek.

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
