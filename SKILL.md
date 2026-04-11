---
name: clone-design
description: Distill a live website or a self-contained HTML clone into a reusable DESIGN.md bundle, including preview HTML files and optional evidence JSON. Use when asked to extract a design system, analyze a site's visual language, or turn a cloned page into DESIGN.md.
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

## Preferred Workflow

Best source quality is:

`URL -> browser render/UI clone -> self-contained clone.html -> clone-design -> design-md/<slug>/`

If the user gives a URL:

- first create a self-contained HTML snapshot with built-in browser tools or a companion cloning workflow
- save the source material under `captures/<slug>/`
- include `clone.html`
- add a screenshot and token dump when helpful

If the user gives a local `.html` file:

- use it directly

Avoid writing `DESIGN.md` from a raw HTTP fetch when the site depends on client-side rendering.

## Default Paths

If the user does not specify paths:

- capture folder: `captures/<slug>/`
- output folder: `design-md/<slug>/`
- output files:
  - `DESIGN.md`
  - `README.md`
  - `preview.html`
  - `preview-dark.html`
- optional evidence file:
  - `evidence.json`

## Run The Generator

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

- where the output folder was saved
- whether it contains `DESIGN.md`, `README.md`, `preview.html`, and `preview-dark.html`
- where `evidence.json` was saved, if generated
- whether the result came from a strong clone source or a weaker fallback
- any notable limitations
