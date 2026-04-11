# clone-design

Turn a website into a reusable `DESIGN.md` bundle.

`clone-design` is a small repository built for the workflow:

```text
URL -> UI clone -> self-contained HTML -> clone-design -> design-md/<slug>/
```

It focuses on design distillation rather than pixel-perfect cloning. The output is meant to help another agent, designer, or frontend developer recreate the visual language of a site.

The case output follows an `awesome-design-md`-style layout:

```text
design-md/<slug>/
```

## What It Produces

- `DESIGN.md` with reusable design-system guidance
- `README.md` for the generated case folder
- `preview.html` and `preview-dark.html` for token browsing
- optional `evidence.json` with extracted raw signals

## Repo Layout

```text
clone-design/
  SKILL.md
  README.md
  scripts/
    generate_design_md.py
  design-md/
    jimeng/
      DESIGN.md
      README.md
      preview.html
      preview-dark.html
      evidence.json
  captures/
    jimeng/
      clone.html
      live.json
      homepage.png
```

## Quick Start

1. Create a self-contained page snapshot.
   Best source: a browser-rendered `clone.html` from `frontend-ui-clone` or an equivalent Playwright capture.
2. Run the generator:

```bash
python3 scripts/generate_design_md.py \
  captures/jimeng/clone.html \
  --name "Jimeng AI" \
  --url "https://jimeng.jianying.com/ai-tool/home?type=image&workspace=undefined" \
  --out-dir design-md/jimeng \
  --json-out design-md/jimeng/evidence.json
```

3. Review the generated `DESIGN.md` and refine anything that should be marked as inferred instead of observed.

## Install As A Skill

Clone the repository and place it in your local skills directory, or copy the folder directly into a skill workspace.

For local use, the key files are:

- `SKILL.md`
- `scripts/generate_design_md.py`
- the optional example folders under `design-md/` and `captures/`

## Included Example

This repository already includes one complete case:

- [jimeng bundle](./design-md/jimeng/)
- [jimeng capture](./captures/jimeng/)

The example shows both sides of the workflow:

- the browser-derived source artifacts in `captures/jimeng/`
- the final reusable design bundle in `design-md/jimeng/`

## Notes

- Best results come from a good self-contained clone.
- The extractor reads HTML and CSS signals; it does not fully reconstruct runtime-only UI states.
- Mood, token roles, and component naming may require a final human pass.
