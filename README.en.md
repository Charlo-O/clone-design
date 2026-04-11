[简体中文](./README.md) | [English](./README.en.md)

# clone-design

Turn any website into a reusable `DESIGN.md` bundle.

`clone-design` now includes the full flow:

```text
URL -> built-in clone flow -> captures/<slug>/clone.html -> design-md/<slug>/
```

It first reuses the same capture methodology as `frontend-ui-clone` to obtain a strong `clone.html`, then distills reusable visual rules that another agent, designer, or frontend developer can build on.

The case output follows an `awesome-design-md`-style structure:

```text
design-md/<slug>/
```

## What It Produces

- `captures/<slug>/clone.html`: self-contained page snapshot
- `captures/<slug>/homepage.png`: capture-time screenshot
- `captures/<slug>/live.json`: optional live-style evidence
- `DESIGN.md`: distilled design-system guidance
- `README.md`: case-level bundle notes
- `preview.html`: light token preview
- `preview-dark.html`: dark token preview
- `evidence.json`: optional extracted evidence

## Repo Layout

```text
clone-design/
  SKILL.md
  README.md
  README.en.md
  references/
    ui_clone_workflow.md
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

1. Hand a URL directly to the skill:

```text
/clone-design https://example.com
```

This reuses the `frontend-ui-clone` capture flow inside the skill, so the user does not need to install a second cloning skill.

2. If you already have a `clone.html`, you can still run the generator script directly:

```bash
python3 scripts/generate_design_md.py \
  captures/jimeng/clone.html \
  --name "Jimeng AI" \
  --url "https://jimeng.jianying.com/ai-tool/home?type=image&workspace=undefined" \
  --out-dir design-md/jimeng \
  --json-out design-md/jimeng/evidence.json
```

3. Review the generated `DESIGN.md` and mark uncertain statements as inferred rather than observed.

## Use As A Skill

You can place this repository in a local skill directory, or copy the core files you need:

- `SKILL.md`
- `scripts/generate_design_md.py`
- the example content under `design-md/` and `captures/`

## Included Example

The repository currently includes one complete example:

- [jimeng design bundle](./design-md/jimeng/)
- [jimeng capture artifacts](./captures/jimeng/)

This example preserves both sides of the workflow:

- `captures/jimeng/`: browser-derived source material
- `design-md/jimeng/`: final distilled design bundle

## Notes

- You no longer need to install `frontend-ui-clone` separately; `clone-design` reuses that workflow internally.
- Better `clone.html` input leads to better output.
- The extractor reads HTML and CSS signals; it does not fully reconstruct runtime-only interaction states.
- Mood, token roles, and component taxonomy should still get a final human review.
