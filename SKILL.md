---
name: clone-design
description: End-to-end website-to-DESIGN.md skill. Given a URL or one or more self-contained HTML clones, it captures pages with the frontend-ui-clone workflow, including logged-in multi-page sessions when needed, then distills them into a DESIGN.md bundle with previews and optional evidence JSON. Use when asked to extract a design system, analyze a site's visual language, or turn live pages into DESIGN.md.
---

# clone-design

Turn a website into a reusable `DESIGN.md` bundle.

Your job is design distillation, not pixel-perfect cloning. Capture the visual system, keep only reusable rules, and clearly separate observed facts from inference.

## When To Use

Use this skill when the user asks to:

- turn a website into `DESIGN.md`
- extract a site's design system
- analyze the visual language of a page
- analyze a logged-in product UI or workspace
- synthesize design guidance from multiple pages or states
- transform a UI clone into reusable design guidance
- turn a live URL directly into a design bundle

## Preferred Workflow

Best source quality is:

`URL -> integrated UI clone -> captures/<slug>/<page>/clone.html -> clone-design -> design-md/<slug>/`

If the user gives a URL:

- do NOT ask the user to install or run `frontend-ui-clone` separately
- first create a self-contained HTML snapshot yourself
- reuse the same cloning workflow and fidelity ladder as `frontend-ui-clone`
- read [references/ui_clone_workflow.md](./references/ui_clone_workflow.md) and follow it
- if the target requires login or the user wants more than one page, also read [references/multi_page_session_workflow.md](./references/multi_page_session_workflow.md)
- save the source material under `captures/<slug>/`
- include `clone.html` for every captured page or state
- add a screenshot and token dump when helpful

If the user gives a local `.html` file:

- use it directly
- accept one file, multiple files, or a capture directory that contains several `clone.html` files

Avoid writing `DESIGN.md` from a raw HTTP fetch when the site depends on client-side rendering.

This skill owns both phases:

1. Clone the page into a reusable capture.
2. Distill the capture into a design bundle.

## Default Paths

If the user does not specify paths:

- single-page capture folder: `captures/<slug>/`
- multi-page capture folder: `captures/<slug>/<page-slug>/`
- capture files per page:
  - `clone.html`
  - `homepage.png`
  - `live.json`
- optional site-level capture manifest:
  - `captures/<slug>/capture-plan.json`
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
- if the site needs authentication, let the user complete login in the browser and keep the same browser context alive
- after login, capture each requested page or UI state separately in the same session
- save each self-contained page as `captures/<slug>/<page-slug>/clone.html` when doing multi-page work
- save a visible-state screenshot as `captures/<slug>/<page-slug>/homepage.png`
- save any useful live token dump as `captures/<slug>/<page-slug>/live.json`
- if it is truly a single-page job, `captures/<slug>/clone.html` is still valid
- if the first capture has a blank hero or obvious overlay issue, apply the same escalation mindset as `frontend-ui-clone`:
  - Level 1: DOM + CSS clone
  - Level 1a: hybrid clone with targeted fixes
  - Level 1b: targeted style bake

When the input is already a local `.html` file, skip the clone phase and go straight to generation.

Do NOT auto-crawl an entire authenticated app unless the user clearly asks for that breadth. Prefer a curated set of key pages or states.

## Run The Generator Script

Use the bundled script:

```bash
python3 scripts/generate_design_md.py "$CLONE_HTML" \
  --name "$SITE_NAME" \
  --url "$SITE_URL" \
  --out-dir "design-md/$SLUG" \
  --json-out "design-md/$SLUG/evidence.json"
```

For multiple captured pages:

```bash
python3 scripts/generate_design_md.py \
  "captures/$SLUG/home/clone.html" \
  "captures/$SLUG/workspace/clone.html" \
  "captures/$SLUG/settings-modal-open/clone.html" \
  --name "$SITE_NAME" \
  --url "$SITE_URL" \
  --out-dir "design-md/$SLUG" \
  --json-out "design-md/$SLUG/evidence.json"
```

Or scan a capture root directly:

```bash
python3 scripts/generate_design_md.py \
  --capture-dir "captures/$SLUG" \
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
- coverage claims for pages or flows you did not actually include in the session

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
- whether it contains one `clone.html` or several page folders with their own `clone.html`, and optionally `homepage.png` / `live.json`
- where the output folder was saved
- whether it contains `DESIGN.md`, `README.md`, `preview.html`, and `preview-dark.html`
- where `evidence.json` was saved, if generated
- whether the result came from a strong clone source or a weaker fallback
- how many pages or states were included in the final synthesis
- any notable limitations
