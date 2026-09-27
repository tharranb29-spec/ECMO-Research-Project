---
version: alpha
name: "A2A Track 3 evidence dashboard"
description: "A quiet scientific control plane that makes evidence status and claim boundaries legible to competition judges."
colors:
  ink: "#14211e"
  muted: "#68746f"
  paper: "#f2f1eb"
  surface: "#fffefa"
  line: "#d9ddd4"
  primary: "#123c33"
  chart-primary: "#276a59"
  chart-outside: "#c99b56"
  highlight: "#c9ef72"
  danger: "#b64b45"
typography:
  display:
    fontFamily: "Georgia, 'Times New Roman', serif"
  body:
    fontFamily: "Inter, 'Avenir Next', 'Segoe UI', sans-serif"
  data:
    fontFamily: "ui-monospace, monospace"
rounded:
  control: "6px"
  overview-panel: "12px"
spacing:
  dashboard-grid-gap: "22px"
  page-padding-min: "32px"
  page-padding-max: "62px"
components:
  chart: {}
  panel: {}
  navigation: {}
---

# A2A Track 3 dashboard design

## Overview

The interface should feel like a research instrument panel, not a promotional AI landing page. Its audience is a competition judge or team reviewer checking what has been measured, what remains provisional, and what the shadow system cannot authorize. This is an English-language product dashboard viewed on laptop and phone. Its distinctive contrast is a dark release-lock panel beside light, data-backed charts; the rest of the interface stays deliberately quiet. Avoid molecule imagery that implies a computed structure, predicted hits, or validated release.

The runtime CSS variables in `track3-dashboard.css` are canonical; this file mirrors their accepted values and explains their use. The `chart-outside` color is currently a local chart role. No generated theme or second token source is introduced.

## Colors

Pine conveys the dashboard's identity and stable measurement; amber denotes caveat or outside-domain values, and red denotes a hard stop. The supplied teammate PDFs use the same page but remain separated by explicit provisional labels. Never use color alone to explain admission, uncertainty, or release. The primary chart tone maps to `--green2`; surrounding neutrals map to `--paper`, `--surface`, `--line`, `--ink`, and `--muted`.

## Typography

Georgia is reserved for page titles and key numeric readouts; Inter and its fallbacks carry controls and explanatory copy. Monospace is for identifiers and measurement only. Use tabular numerals for chart values, preserve readable sentence case, and keep status copy precise rather than aspirational.

## Layout

The persistent navigation is 244px on desktop and becomes an off-canvas menu below 960px. Content uses a twelve-column grid and 22px gutters. Overview charts pair the frozen development model comparison with a development-domain diagnostic. Provisional teammate precision lives only in its labeled reference view. Panels collapse to a single column on narrow screens; no chart may require horizontal page scrolling.

## Elevation & Depth

Hierarchy primarily comes from surface tone and spacing. Overview chart panels use a border without a second shadow. The dark release-state panel is the visual anchor, not a claim of approval. Never add decorative glass or blur to scientific data.

## Shapes

Controls follow the existing 6–8px radius family. Overview chart panels use 12px corners. Data bars are flat-ended when they encode partitioned cohorts; small status badges may remain pill-shaped. Avoid decorative diagrams that could be mistaken for molecular evidence.

## Components

Chart axes, labels, and accessible text must expose the same counts. Model comparison and teammate precision keep keyboard-operable selectors with visible pressed and focus states. Empty diagnostics name the missing snapshot instead of substituting illustrative values. Screens that consume frozen data must not silently mix those values with provisional PDF aggregates. Preserve reduced-motion behavior and a visible application-wide scrollbar.

## Do's and Don'ts

- Do identify the cohort, evaluation stage, and data provenance beside each chart.
- Do keep release and external-validation gates visibly separate from exploratory graphics.
- Don't draw a molecule or receptor shape that could be mistaken for a computed result.
- Don't convert a point estimate, docking score, or PDF aggregate into a hit or promotion claim.
