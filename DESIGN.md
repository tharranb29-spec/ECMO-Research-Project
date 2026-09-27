---
version: alpha
name: "A2A Track 3 Signal Atlas"
description: "An evidence-gated scientific exhibit for judges and team reviewers."
colors:
  ink: "#102637"
  muted: "#526879"
  paper: "#edf2f4"
  surface: "#ffffff"
  line: "#d4dfe5"
  primary: "#102f46"
  chart-primary: "#137994"
  chart-outside: "#e8b45b"
  highlight: "#f2cc70"
  danger: "#a84038"
typography:
  display:
    fontFamily: "'Iowan Old Style', Baskerville, 'Palatino Linotype', Georgia, serif"
  body:
    fontFamily: "'Avenir Next', 'Segoe UI', sans-serif"
  data:
    fontFamily: "ui-monospace, monospace"
rounded:
  control: "8px"
  panel: "13px"
spacing:
  dashboard-grid-gap: "22px"
  page-padding-min: "15px"
  page-padding-max: "58px"
components:
  chart: {}
  panel: {}
  navigation: {}
---

# A2A Track 3 dashboard design

## Purpose and audience

This is a judge-facing scientific exhibit that must also work as a team review instrument. Its first task is to make a limit understandable: 240 records are held for review, none entered the frozen external cohort, and no model was promoted. Discovery is demonstrable in shadow mode, not autonomous scientific authority. The dashboard should feel deliberate and memorable without presenting a decorative diagram as molecular or experimental evidence.

## Visual direction

“Signal Atlas” uses cool laboratory paper, a deep-blue evidence field, and a three-stage state sequence as its signature. The dark field is a visual explanation of the real gate—not a marketing hero. The light workspace below holds clearly scoped charts, source records, and human actions. Avoid decorative molecule or receptor imagery, generic AI glows, and numbered navigation that implies a sequence where none exists.

## Tokens and source of truth

`track3-dashboard.css` retains legacy layout and component behavior. `track3-dashboard-theme.css`, loaded after it, is the canonical visual layer and owns the runtime values listed above. New visual changes should go into the theme layer; changes to behavior and data remain in the HTML/JS and their tests. No chart, border, or status color may substitute for a written state label.

## Typography and content

The display face is used for editorial titles and measured readouts. Avenir Next/Segoe UI carries controls and explanatory text; monospace is limited to identifiers and code-like data. Chart captions state cohort and evaluation stage. Provisional teammate PDF analysis remains labeled as separate and not independently reproduced. The official competition project title stays readable in the overview.

## Layout and interaction

Desktop navigation is a 268px dark instrument index; below 960px it is an off-canvas menu. The overview pairs an evidence-state field with an unbordered metric strip, then offers three explicit routes and two development-only charts. Other views share the same title, panel, input, and status treatment. The experience must work at 390px without horizontal page overflow. Visible focus, reduced motion, keyboard-operable charts, readable loading/error states, and source provenance are required.

Provider mode and human disposition deliberately use native selects: the operating-system popup is acceptable for these short, single-choice lists. The application owns text validation and inline recovery; chart axes use real cohort values rather than relative ranking widths.

## Scientific constraints

- Keep frozen project counts and provisional PDF aggregates in separate views and contracts.
- Never represent development R², a shadow point estimate, docking, or MD as external confirmation.
- Never imply candidate ordering, hit probability, or autonomous release.
- Keep the 240-held → 0-admitted → locked diagram tied to the audited snapshot. If its meaning changes, update the label, accessible text, and tests together.
