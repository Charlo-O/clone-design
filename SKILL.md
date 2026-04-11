---
name: clone-design
description: End-to-end website-to-DESIGN.md skill. Given a URL or a self-contained HTML clone, it first captures the page into a reusable clone.html using the same workflow as frontend-ui-clone, then distills it into a DESIGN.md bundle with previews and optional evidence JSON. Use when asked to extract a design system, analyze a site's visual language, or turn a live site into DESIGN.md.
---

# clone-design

Turn a website into a reusable `DESIGN.md` bundle.

Your job is design distillation, not pixel-perfect cloning. Capture the visual system, keep only reusable rules, and clearly separate observed facts from inference.

## When To Use

Use this skill when the user asks to:

- turn a website into `DESIGN.md`
- extract a site's design system
- analyze the visual language of a page
- transform a UI clone into reusable design guidance
- turn a live URL directly into a design bundle

## Preferred Workflow

Best source quality is:

`URL -> integrated UI clone -> captures/<slug>/clone.html -> clone-design -> design-md/<slug>/`

If the user gives a URL:

- do NOT ask the user to install or run `frontend-ui-clone` separately
- first create a self-contained HTML snapshot yourself
- reuse the same cloning workflow and fidelity ladder as `frontend-ui-clone`
- read [references/ui_clone_workflow.md](./references/ui_clone_workflow.md) and follow it
- save the source material under `captures/<slug>/`
- include `clone.html`
- add a screenshot and token dump when helpful

If the user gives a local `.html` file:

- use it directly

Avoid writing `DESIGN.md` from a raw HTTP fetch when the site depends on client-side rendering.

This skill owns both phases:

1. Clone the page into a reusable capture.
2. Distill the capture into a design bundle.

## Default Paths

If the user does not specify paths:

- capture folder: `captures/<slug>/`
- capture files:
  - `clone.html`
  - `homepage.png`
  - `live.json`
- output folder: `design-md/<slug>/`
- output files:
  - `DESIGN.md`
  - `README.md`
  - `preview.html`
  - `preview-dark.html`
- optional evidence file:
  - `evidence.json`

## Clone Then Generate

When the input is a URL:

- prefer built-in browser/Playwright tools when available
- use the same default viewport and scrolling strategy as `frontend-ui-clone`
- preserve rendered DOM, CSS, fonts, and resolved asset URLs
- save the final self-contained page as `captures/<slug>/clone.html`
- save a visible-state screenshot as `captures/<slug>/homepage.png`
- save any useful live token dump as `captures/<slug>/live.json`
- if the first capture has a blank hero or obvious overlay issue, apply the same escalation mindset as `frontend-ui-clone`:
  - Level 1: DOM + CSS clone
  - Level 1a: hybrid clone with targeted fixes
  - Level 1b: targeted style bake

When the input is already a local `.html` file, skip the clone phase and go straight to generation.

## Run The Generator Script

Use the bundled script:

```bash
python3 scripts/generate_design_md.py "$CLONE_HTML" \
  --name "$SITE_NAME" \
  --url "$SITE_URL" \
  --out-dir "design-md/$SLUG" \
  --json-out "design-md/$SLUG/evidence.json"
```

Omit optional flags when you do not have those values.

## Review Standard

After generation:

- read the produced `DESIGN.md`
- tighten vague wording
- keep token claims grounded in the source
- mark uncertain statements as inferred

Never invent:

- colors not present in the clone
- font families not observed in CSS
- breakpoints that were not extracted
- interactions that require runtime state you did not capture

## Required Sections

The final `DESIGN.md` should include:

1. Visual Theme & Atmosphere
2. Color Palette & Roles
3. Typography Rules
4. Component Stylings
5. Layout Principles
6. Depth & Elevation
7. Do's and Don'ts
8. Responsive Behavior
9. Agent Prompt Guide

## Final Response

Report:

- where the capture folder was saved, if you cloned from a live URL
- whether it contains `clone.html`, and optionally `homepage.png` / `live.json`
- where the output folder was saved
- whether it contains `DESIGN.md`, `README.md`, `preview.html`, and `preview-dark.html`
- where `evidence.json` was saved, if generated
- whether the result came from a strong clone source or a weaker fallback
- any notable limitations
