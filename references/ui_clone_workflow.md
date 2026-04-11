# Integrated UI Clone Workflow

Use this file when `clone-design` receives a live URL instead of a local `clone.html`.

The goal is to reuse the same cloning approach as `frontend-ui-clone` without requiring the user to install that skill separately.

## Core Principle

Clone first, distill second.

Do not jump straight from a dynamic URL to `DESIGN.md` when you can capture a rendered page first.

## Default Outputs

For a site slug `<slug>`, create:

- `captures/<slug>/clone.html`
- `captures/<slug>/homepage.png`
- `captures/<slug>/live.json`

Then generate:

- `design-md/<slug>/DESIGN.md`
- `design-md/<slug>/README.md`
- `design-md/<slug>/preview.html`
- `design-md/<slug>/preview-dark.html`
- optional `design-md/<slug>/evidence.json`

## Strategy Ladder

Reuse the same strategy order as `frontend-ui-clone`:

1. Level 1: browser-rendered DOM + CSS extraction
2. Level 1a: hybrid clone with targeted fixes
3. Level 1b: targeted style bake
4. Lower-confidence fallbacks only if browser capture is unavailable

Prefer the highest-fidelity path available.

## Level 1 Capture Standard

When browser tooling is available:

- open the page in a real browser context
- use a desktop viewport around `1440 x 900`
- wait for page render with a practical fallback from `networkidle` to `domcontentloaded`
- scroll the full page and any inner scroll containers
- reset to a neutral state before extraction:
  - mouse in a safe corner
  - no focused field
  - page scrolled back to top
- extract the rendered DOM and CSS rather than rewriting the page from scratch
- preserve visible text, layout, fonts, gradients, and CSS custom properties

## Escalation Rules

If the first clone is obviously broken, escalate like `frontend-ui-clone`:

- hero section is blank
- a fixed overlay blocks the main content
- major Tailwind `important:true` styles do not apply

Escalate in this order:

1. Keep original CSS and add targeted overrides
2. Bake the most important computed styles inline when the CSS cascade is still unusable

## Evidence Capture

Alongside `clone.html`, try to save:

- a screenshot of the visible homepage
- a lightweight JSON dump of useful live tokens such as page title, CSS variables, font families, or sampled colors

This evidence helps validate the final `DESIGN.md`.

## Final Handoff

Once `captures/<slug>/clone.html` exists and looks credible, run:

```bash
python3 scripts/generate_design_md.py "captures/<slug>/clone.html" \
  --url "$SITE_URL" \
  --out-dir "design-md/<slug>" \
  --json-out "design-md/<slug>/evidence.json"
```
