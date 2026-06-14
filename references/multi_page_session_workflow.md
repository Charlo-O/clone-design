# Multi-Page Session Workflow

Use this workflow when the target site:

- requires login
- has important pages behind auth
- needs several routes or states to represent the design system or landing-page experience
- contains drawers, modals, tabs, or workspaces that should be captured separately

## Goal

Keep one authenticated browser session alive, then capture a curated set of pages or UI states under the same session instead of treating the product as a single public page.

## Recommended Process

1. Open the site with the built-in browser tools.
2. If the site requires login, let the user complete authentication in that browser context.
3. Stay in the same browser tab or browser context after login so cookies and storage remain available.
4. Ask the user which pages or states matter, or infer a short high-value list if they already named them.
5. Capture each page or state separately.
6. Save every capture under a page-specific folder.
7. For design extraction, run the generator on all captured `clone.html` files together.
8. For landing remix, choose the page/state that will become the main `source-clone.html`, and keep the other captures as evidence or secondary route references.

## What To Capture

Prefer a small, representative set such as:

- marketing or dashboard home
- landing page plus pricing or docs page if those pages affect the offer copy
- primary creation or editing workspace
- settings or configuration page
- list/detail pair
- one or two important expanded states

State captures should be named explicitly, for example:

- `home`
- `workspace`
- `settings`
- `tag-picker-open`
- `settings-modal-open`
- `empty-state`

Do not silently merge several very different states into one unnamed snapshot.

## Suggested Folder Shape

```text
captures/<site-slug>/
  capture-plan.json
  home/
    clone.html
    homepage.png
    live.json
  workspace/
    clone.html
    homepage.png
    live.json
  settings-modal-open/
    clone.html
    homepage.png
    live.json
```

The optional `capture-plan.json` can list page labels, original URLs, and any notes about the state that was open at capture time.

## Capture Rules

- Keep one folder per page or state.
- Preserve the same auth session for all captures.
- Avoid auto-crawling every route in a product app unless the user explicitly wants broad coverage.
- If a modal, drawer, or popover matters, capture it as its own state-specific folder.
- If a page is data-heavy, capture the design shell and representative UI, not every possible record variation.

## Generation Or Remix

For design extraction, synthesize captures together:

```bash
python3 scripts/generate_design_md.py \
  --capture-dir "captures/<site-slug>" \
  --name "<Site Name>" \
  --url "<Original URL>" \
  --out-dir "design-md/<site-slug>" \
  --json-out "design-md/<site-slug>/evidence.json"
```

You can also pass specific `clone.html` files if only a subset should contribute to the final bundle.

For landing remix, do not merge unrelated pages into one HTML file. Pick one primary landing-page capture for `landing-pages/<site-slug>/source-clone.html`, then use secondary captures only for copy, imagery, components, or states that the user explicitly wants reused.

## Reporting

When you finish, report:

- whether login was required
- which pages or states were included
- where the capture root was saved
- where the final `design-md/<site-slug>/` bundle was written
- any coverage gaps, such as pages not captured or flows that still require runtime interaction
