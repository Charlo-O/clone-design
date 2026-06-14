[简体中文](./README.md) | [English](./README.en.md)

# clone-design

`clone-design` is an end-to-end website cloning, landing-page remix, and design-system extraction skill.

It now supports two primary workflows:

```text
URL -> 1:1 clone.html -> project copy replacement -> imagegen asset replacement -> landing-pages/<slug>/index.html
```

```text
URL / clone.html -> design signal extraction -> design-md/<slug>/DESIGN.md
```

Core principle: **clone 1:1 first, then adapt content**. Do not rewrite copy, replace images, or redesign before the baseline clone has passed browser screenshot review.

## Main Capabilities

- Capture rendered DOM, CSS, fonts, images, and visual state from a URL in a real browser.
- Generate a high-fidelity `clone.html` as the baseline for remixing or design extraction.
- Follow the `frontend-ui-clone` approach for lazy images, CSS variables, gradient text, inner scroll containers, invisible overlays, and Tailwind cascade issues.
- Replace source landing-page copy with product copy discovered from the current project folder.
- Use the `imagegen` skill to create project-relevant hero images, product visuals, thumbnails, avatars, or decorative raster assets.
- Preserve the original layout, spacing, type rhythm, animation feel, and responsive structure.
- Continue producing `DESIGN.md`, light/dark token previews, and optional `evidence.json`.

## Outputs

### Landing Remix

```text
landing-pages/<slug>/
  index.html
  source-clone.html
  content-inventory.json
  copy-map.json
  image-plan.json
  assets/
    generated/
  qa/
    original-desktop.png
    clone-desktop.png
    final-desktop.png
```

### Capture Artifacts

```text
captures/<slug>/
  clone.html
  homepage.png
  live.json
```

For multi-page or multi-state sessions:

```text
captures/<slug>/<page>/
  clone.html
  homepage.png
  live.json
```

### DESIGN.md Bundle

```text
design-md/<slug>/
  DESIGN.md
  README.md
  preview.html
  preview-dark.html
  evidence.json
```

## Repo Layout

```text
clone-design/
  SKILL.md
  README.md
  README.en.md
  references/
    ui_clone_workflow.md
    landing_page_remix_workflow.md
    multi_page_session_workflow.md
  scripts/
    extract_landing_inventory.py
    generate_design_md.py
  captures/
  design-md/
  landing-pages/
```

## Quick Start

### Clone And Remix A Landing Page

```text
/clone-design turn https://example.com into a 1:1 cloned landing page for this project
```

Recommended flow:

1. Capture the source page in a real browser and save `captures/<slug>/clone.html`.
2. Compare source and local clone screenshots, then fix visible differences.
3. Read the current project folder for product name, positioning, features, CTAs, voice, and existing assets.
4. Run `scripts/extract_landing_inventory.py` to create `content-inventory.json`.
5. Create `copy-map.json`, then replace visible copy.
6. Create `image-plan.json`, then reuse project assets or call `imagegen` for raster replacements.
7. Write `landing-pages/<slug>/index.html`.
8. Run desktop and mobile browser QA.

### Generate DESIGN.md Only

```bash
python3 scripts/generate_design_md.py \
  captures/jimeng/clone.html \
  --name "Jimeng AI" \
  --url "https://jimeng.jianying.com/ai-tool/home?type=image&workspace=undefined" \
  --out-dir design-md/jimeng \
  --json-out design-md/jimeng/evidence.json
```

For multi-page synthesis:

```bash
python3 scripts/generate_design_md.py \
  --capture-dir captures/acme \
  --name "Acme" \
  --url "https://app.example.com" \
  --out-dir design-md/acme \
  --json-out design-md/acme/evidence.json
```

## Use As A Skill

Place this repository in a local skill directory, or copy the core resources:

- `SKILL.md`
- `references/`
- `scripts/extract_landing_inventory.py`
- `scripts/generate_design_md.py`
- example `captures/` and `design-md/`

## Notes

- The clone phase aims for 1:1 fidelity and should not add creative interpretation.
- The remix phase replaces copy, imagery, and brand-specific content while preserving structure.
- `imagegen` is for raster image assets; SVG icons, CSS gradients, and simple vector decoration should usually remain code-native.
- For authenticated products, preserve one browser session and capture a curated set of pages or states instead of crawling the whole app by default.
- `DESIGN.md` generation still reads HTML/CSS signals; mood, token roles, and component taxonomy should get a final human review.
