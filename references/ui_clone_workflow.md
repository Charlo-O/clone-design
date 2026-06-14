# Integrated UI Clone Workflow

Use this file when `clone-design` receives a live URL instead of a local `clone.html`.

The goal is to create a high-fidelity rendered-page capture that can serve as either:

- the frozen baseline for a project-specific landing page remix
- the source material for `DESIGN.md` extraction

## Core Principle

Clone first. Remix or distill second.

Do not jump straight from a dynamic URL to rewritten content or `DESIGN.md` when you can capture a rendered page first.

The baseline clone must preserve the source page's DOM, CSS, typography, assets, section rhythm, and responsive behavior as closely as the available tools allow.

## Default Outputs

For a site slug `<slug>`, create:

- `captures/<slug>/clone.html`
- `captures/<slug>/homepage.png`
- `captures/<slug>/live.json`

For multi-page captures:

```text
captures/<slug>/<page>/
  clone.html
  homepage.png
  live.json
```

For landing remix mode, copy the verified clone into:

```text
landing-pages/<slug>/source-clone.html
```

For design extraction mode, generate:

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

Prefer the highest-fidelity path available. Landing remix mode should not proceed from a weak fallback unless the user accepts the limitation.

## Level 1 Capture Standard

When browser tooling is available:

- open the page in a real browser context
- use a desktop viewport around `1440 x 900`
- wait for page render with a practical fallback from `networkidle` to `domcontentloaded`
- scroll the full page twice to trigger lazy loading and scroll reveals
- scroll inner containers as well as `window` when the app uses fixed/full-screen SPA wrappers
- reset to a neutral state before extraction:
  - mouse in a safe corner
  - no focused field
  - page scrolled back to top
- extract the rendered DOM and CSS instead of rewriting the page from scratch
- preserve visible text, layout, fonts, gradients, CSS custom properties, and resolved asset URLs
- preserve `<html>` attributes such as `lang`, `class`, and theme/data attributes when they affect styling
- strip analytics, trackers, CSP traps, and production write scripts when building local output

## Extraction Details

Capture these signals when possible:

- final rendered `<body>` DOM
- inline `<style>` tags
- linked CSS contents or resolved stylesheet URLs
- CSS custom properties from `:root`, `html`, and `body`
- font preload/link tags
- computed gradient text styles, especially `background-clip: text`
- image `src`, `srcset`, `data-src`, `data-lazy-src`, and framework image URLs such as `/_next/image?...`
- visible text samples by section
- section topology and approximate section boundaries
- responsive media-query hints

Fix common static-clone failures:

- remove or neutralize invisible overlays that block the page
- strip `loading="lazy"` from images
- convert lazy image attributes into real `src` values
- resolve relative URLs against the source origin
- keep hero `min-height` behavior; do not globally force `section { height: auto }`
- avoid global `overflow: visible` overrides that break clipped hero backgrounds
- keep CSS `@import` rules before other style rules

## Escalation Rules

If the first clone is obviously broken, escalate like `frontend-ui-clone`:

- hero section is blank
- a fixed overlay blocks the main content
- major Tailwind `important:true` styles do not apply
- gradient text becomes invisible
- lazy images stay blank
- mobile layout is unusable

Escalate in this order:

1. Keep original CSS and add targeted overrides.
2. Remove or hide only the blocking overlay/panel.
3. Bake the most important computed styles inline when the CSS cascade is still unusable.

Use targeted style bake as a last resort because it can reduce responsive fidelity.

## Visual QA

Before remixing or distilling, verify the clone:

1. Screenshot the source page and local clone at desktop width around `1440 x 900`.
2. If the page is responsive, screenshot both at mobile width around `390px`.
3. Compare the first viewport and full-page screenshots.
4. Fix the largest differences first:
   - layout origin
   - hero visibility
   - missing media
   - wrong background/gradient
   - typography scale or weight
   - spacing and section height
   - mobile stacking
5. Re-screenshot after fixes.

Do not call the clone 1:1 if the first viewport, hero, or major sections are visibly different.

## Evidence Capture

Alongside `clone.html`, try to save:

- a screenshot of the visible homepage
- full-page screenshot when useful
- a lightweight JSON dump of useful live tokens such as page title, CSS variables, font families, sampled colors, key image URLs, and section labels

This evidence helps validate both the final landing page remix and the `DESIGN.md` output.

## Final Handoff

Once `captures/<slug>/clone.html` exists and looks credible:

- for landing remix mode, continue with [landing_page_remix_workflow.md](./landing_page_remix_workflow.md)
- for design extraction mode, run:

```bash
python3 scripts/generate_design_md.py "captures/<slug>/clone.html" \
  --url "$SITE_URL" \
  --out-dir "design-md/<slug>" \
  --json-out "design-md/<slug>/evidence.json"
```
