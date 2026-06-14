# Landing Page Remix Workflow

Use this workflow after a source landing page has been captured as a credible 1:1 `clone.html`.

## Goal

Create a local landing page for the current project while preserving the source page's layout, spacing, typography rhythm, animation feel, and responsive structure.

The workflow has two strict phases:

1. Verify the source clone.
2. Replace content and imagery without breaking the clone.

Do not start rewriting copy or generating images until the source clone has passed browser screenshot review.

## Inputs

Expected inputs:

- source URL or existing `clone.html`
- current workspace/project folder
- optional user notes about the product, audience, offer, or brand tone
- optional existing brand assets or screenshots

If the workspace has no discoverable product context, ask the user for a short product brief before remixing.

## Output Shape

Default folder:

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
    original-mobile.png
    clone-mobile.png
    final-mobile.png
```

Use `source-clone.html` as the frozen visual baseline. Use `index.html` as the adapted page.

## Step 1: Freeze A 1:1 Baseline

1. Save the captured source clone.
2. Open the source site and local clone in a browser.
3. Capture desktop screenshots around `1440 x 900`.
4. Capture mobile screenshots around `390px` width when the source is responsive.
5. Compare visible sections:
   - navbar
   - hero
   - proof/social proof
   - feature sections
   - pricing/offer sections
   - FAQ
   - footer
6. Fix clone-only issues before remixing:
   - blank hero
   - missing images
   - wrong font weights
   - broken gradients
   - lazy images still pointing to placeholders
   - overlays or cookie banners covering content
   - mobile overflow

Keep fixes targeted. Do not redesign.

## Step 2: Extract Current Project Context

Inspect the current workspace before writing copy. Prefer these sources:

- `README.md`, `README.en.md`, docs, `PRODUCT.md`, `VISION.md`
- `package.json` name, description, scripts, dependencies
- app source strings in `src/`, `app/`, `pages/`, `components/`
- existing landing pages or marketing pages
- screenshots, logos, product images, demo media
- issue/PR notes only if they are already local and relevant

Summarize the project into:

- product name
- one-sentence positioning
- target audience
- main user problem
- strongest proof or differentiator
- primary CTA
- secondary CTA
- 4-8 feature claims
- tone words
- visual asset themes

Do not invent a product category if the repo does not support it.

## Step 3: Build The Copy Map

Before writing the copy map, run:

```bash
python3 scripts/extract_landing_inventory.py \
  "landing-pages/<slug>/source-clone.html" \
  --base-url "<SOURCE_URL>" \
  --out "landing-pages/<slug>/content-inventory.json" \
  --pretty
```

Create `copy-map.json` before editing `index.html`.

Recommended shape:

```json
[
  {
    "selector": "h1",
    "original": "Original headline",
    "replacement": "Project-specific headline",
    "role": "hero-headline",
    "length_strategy": "same visual weight"
  }
]
```

Copy mapping rules:

- Preserve section intent. Hero text stays hero text; feature labels stay feature labels.
- Preserve approximate length and line count when possible.
- Keep CTAs short.
- Replace source brand names, customer names, metrics, and testimonials unless the user explicitly says to keep them.
- Avoid false claims. Mark unsupported metrics as generic benefits, or ask the user for proof.
- Keep legal, pricing, and compliance claims conservative.
- Do not alter structural class names or component nesting while replacing text.

After applying the map, inspect the rendered page for:

- text overflow
- CTA label clipping
- broken line rhythm
- mobile wrapping issues
- accidental source-brand leftovers

## Step 4: Build The Image Plan

Create `image-plan.json` before generating assets.

Use `content-inventory.json` as the first pass. Then inspect the rendered page for image-like surfaces the HTML parser may miss, such as CSS backgrounds or canvas-like media.

Inventory image-like surfaces:

- hero images or product mockups
- screenshots inside device frames
- feature cards with photos or thumbnails
- testimonial avatars
- customer logos
- background photos
- decorative raster textures
- Open Graph/social preview image if present

Recommended shape:

```json
[
  {
    "selector": ".hero img",
    "original_src": "https://example.com/hero.png",
    "role": "hero-product-visual",
    "target_size": "1536x1024",
    "aspect_ratio": "3:2",
    "replacement_path": "assets/generated/hero-product-visual.png",
    "prompt": "..."
  }
]
```

Replacement rules:

- Use existing project assets first when they are high quality and relevant.
- Use the `imagegen` skill for new raster assets that should match the project.
- Preserve the original slot's aspect ratio, dimensions, object-fit, border radius, shadow, and visual density.
- Generate screenshots/mockups only when there is enough product context to make them plausible.
- Use abstract product visuals when the repo does not expose a concrete UI.
- Replace third-party logos and avatars with neutral/project-safe alternatives.
- Do not replace SVG icons, CSS gradients, or simple vector decoration with generated bitmaps by default.

## Step 5: Use Imagegen For Raster Replacements

When generating images:

1. Use the `imagegen` skill's built-in mode by default.
2. Write one prompt per distinct asset slot.
3. Include the asset's role, target aspect ratio, visual style, subject, project context, and constraints.
4. Avoid text inside generated images unless exact text is essential.
5. Save final assets under `landing-pages/<slug>/assets/generated/`.
6. Update `index.html` and CSS references to use project-local paths.

Prompt template:

```text
Use case: ads-marketing
Asset type: landing page <asset role>
Primary request: <project-relevant visual>
Scene/backdrop: <environment or abstract setting>
Subject: <main subject>
Style/medium: <photo, 3D render, UI mockup, illustration>
Composition/framing: match a <width>x<height> slot, preserve negative space and crop behavior
Color palette: compatible with the cloned page palette
Constraints: no source-site logos, no watermark, no unreadable UI text
Avoid: third-party trademarks, copied screenshots, source-brand imagery
```

For project screenshots, prefer rendering real local UI if available. Use generated UI-like imagery only when no real app screen exists.

## Step 6: Final QA

Open `landing-pages/<slug>/index.html` in a browser and verify:

- all generated images load from local paths
- no broken remote image references remain unless intentionally kept
- source brand text and logos are removed or intentionally retained
- text fits at desktop and mobile widths
- sections still align with the source layout
- hover/click interactions that existed in the clone still work
- mobile layout does not horizontally scroll

Capture final screenshots into `qa/`.

## Final Report

Report:

- source URL and local source clone path
- final `index.html` path
- project files used as copy source
- number of mapped text replacements
- number of generated or reused image replacements
- browser viewports checked
- remaining limitations
