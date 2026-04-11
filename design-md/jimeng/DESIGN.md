# Design System: Jimeng AI

> Extracted from a rendered snapshot of https://jimeng.jianying.com/ai-tool/home?type=image&workspace=undefined. This document focuses on the visible homepage experience. Some responsive behavior and token naming are inferred from CSS and rendered UI rather than official source files.

## 1. Visual Theme & Atmosphere

Jimeng AI feels like a consumer-grade AI creation workspace disguised as a lightweight studio dashboard. The overall canvas is bright and low-noise rather than dark or theatrical: a soft neutral background (`#f8f9fa`) carries the page, while most functional modules sit on white or near-white cards with translucent treatment (`rgba(255,255,255,0.92)`). The result is calm, productized, and highly operational. It looks less like a marketing landing page and more like an always-open creative workbench.

The design language is built on contrast between soft utility surfaces and one sharp identity accent: a cyan-teal line centered around `#00a1c2` and `#00cae0`. That accent is used sparingly but very deliberately on active states, selected labels, and “currently chosen” tool modes. Everything else stays restrained: near-black text (`#0f1419`), muted gray-blue copy (`#536471`, `#72808a`), hairline borders, and almost no decorative shadow.

Typography does a lot of the emotional work. Standard UI text relies on a modern product sans stack led by `CapCut Sans` and `PingFang SC`, but the headline-like mode selector swaps into a heavier display voice using `Founder Yashi Black`. Numerals and compact tool metadata frequently bring in `Montserrat`, which gives model names and parameter labels a more technical, dashboard-like precision.

**Key Characteristics:**
- Light neutral canvas with soft white modules rather than dark hero sections
- Cyan-teal accent (`#00a1c2` / `#00cae0`) used for active selections and tool emphasis
- Primary UI stack: `CapCut Sans`, `PingFang SC`, system sans
- Display moments use `Founder Yashi Black` for a more branded, poster-like tone
- Very low shadow usage; depth mostly comes from borders and translucent fills
- Two corner families dominate: `8px` for controls, `24px` for prominent cards and feature pills
- Left rail + centered work area layout, with the creation panel acting as the visual anchor

## 2. Color Palette & Roles

### Primary
- **Workspace Background** (`#f8f9fa`): Main page canvas and tab-strip background
- **Panel White** (`rgba(255,255,255,0.92)`): Generator module, floating utility surfaces, elevated light cards
- **Primary Text** (`#0f1419`): Main headings, active labels, important tool names
- **Secondary Text** (`#536471`): Descriptions, lightweight UI copy, inactive button text

### Accent Colors
- **Jimeng Cyan** (`#00a1c2`): Active mode label, selected control text, product emphasis
- **Bright Aqua** (`#00cae0`): Secondary accent visible in extracted CSS; use as a brighter companion to the main cyan
- **Soft Ice Tint** (`rgba(204,221,255,0.06)`): Placeholder/media tile background and cool surface tint

### Neutral & Utility
- **Muted Gray Blue** (`#72808a`): Secondary navigation and low-priority metadata
- **Hairline Border** (`rgba(0,0,0,0.05)`): Default card and pill outline
- **Input Border** (`rgba(0,0,0,0.07)`): Search and form-field outline
- **Hover Utility Fill** (`rgba(0,0,0,0.05)`): Active tab chip, upload placeholder, subtle emphasis surfaces
- **Pure White** (`#ffffff`): Feature pills, compact action buttons, top utility button

## 3. Typography Rules

### Font Family
- **Primary UI**: `CapCut Sans`, `PingFang SC`, `Hiragino Sans GB`, `Microsoft YaHei`, `Arial`, sans-serif
- **Display / Emphasis**: `Founder Yashi Black`, then fallback into the primary UI stack
- **Numeric / Tool Labels**: `Montserrat` paired with the primary UI stack

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing | Notes |
|------|------|------|--------|-------------|----------------|-------|
| Display Selector | Founder Yashi Black + primary sans | 24px | 600 | 32px-36px | normal | Homepage mode switcher words like “图片生成” |
| Section / Module Heading | CapCut Sans / PingFang SC | 24px | 500-600 | 32px | normal | Generator area heading and strong section anchors |
| Standard UI Label | CapCut Sans / PingFang SC | 14px | 500 | 18px-21px | normal | Banner text, side nav, common interface labels |
| Body / Secondary UI | CapCut Sans / PingFang SC | 14px | 400 | 21px-22px | normal | Descriptions and ordinary product copy |
| Compact Control Text | Montserrat + primary sans | 12px | 450-600 | 18px-20px | normal | Tool chips, model names, parameter labels |
| Micro Navigation Label | Montserrat + primary sans | 11px-12px | 400-500 | 18px | normal | Left-rail captions and tiny metadata |

### Principles
- **Utility-first typography**: most of the interface stays in a compact 12px-14px operational range
- **Display only where needed**: the site reserves the heavier `Founder Yashi Black` voice for the mode-selection moment rather than using it everywhere
- **Mixed-script pragmatism**: Chinese UI copy leans on `PingFang SC`, while Latin labels and numbers frequently inherit `Montserrat`
- **Low-drama hierarchy**: emphasis comes more from weight, placement, and accent color than from giant headline sizes

## 4. Component Stylings

### Announcement Strip
- Height around `42px`
- Transparent background on top of the page
- Text in near-black (`#0f1419`)
- Compact white CTA button with `6px` radius

### Generator Card
- Surface: `rgba(255,255,255,0.92)`
- Border: `1px solid rgba(0,0,0,0.05)`
- Radius: `24px`
- Treatment: large, quiet, centered, almost no shadow
- Purpose: this is the visual and functional anchor of the homepage

### Controls & Inputs
- Standard control radius: `8px`
- Outlined rather than filled by default
- Border: `rgba(0,0,0,0.05)` to `rgba(0,0,0,0.07)`
- Active text often switches to `#00a1c2`
- Disabled circular submit button uses light gray fill (`rgb(225,227,229)`) with `50%` radius

### Feature Pills / Capability Cards
- Background: white
- Border: `1px solid rgba(0,0,0,0.05)`
- Radius: `24px`
- Height: approximately `76px`
- Use: horizontally arranged “what this tool can do” capsules

### Side Navigation
- Narrow left rail around `76px` wide
- Minimal chrome, mostly text/icon-driven
- Menu items use `6px` corner rounding
- Selected state depends on stronger text treatment rather than heavy background fill

### Tabs & Search
- Active tab chip uses `rgba(0,0,0,0.05)` fill with `8px` radius
- Search and search-like inputs use `8px` radius and hairline borders
- The entire tab/search strip stays light and restrained against the neutral background

### Media / Discovery Tiles
- Placeholder surface: `rgba(204,221,255,0.06)`
- Geometry: tall rectangular cards around `255px` wide in a masonry-like grid
- Visual identity comes from content thumbnails more than from card chrome

### Floating Utility Button
- Surface: `rgba(255,255,255,0.92)`
- Border: `1px solid rgba(0,0,0,0.03)`
- Radius: `8px`
- Shadow: `0 4px 12px rgba(0,0,0,0.06), 0 2px 6px rgba(0,0,0,0.02)`
- Use: rare example of actual elevation on the page

## 5. Layout Principles

### Spacing System
- Practical base step: `8px`
- Common control heights: `28px`, `36px`, `42px`, `48px`, `76px`
- Large module rhythm is roomy, but individual controls remain compact

### Grid & Container
- Left rail occupies roughly `76px`
- Main content area begins after the rail and centers key modules in a wide workspace
- Prominent working widths observed around `1000px`, `1280px`, and `1364px`
- Discovery/media section uses repeated `255px` card widths in a multi-column feed

### Whitespace Philosophy
- **Tool-first, not editorial**: whitespace exists to clarify controls, not to create dramatic pauses
- **Center-stage creation panel**: the upload + prompt module is given the clearest breathing room
- **Dense but calm**: multiple modules coexist on screen, but the low-chroma palette prevents visual overload

### Border Radius Scale
- `6px`: tiny utility buttons and menu states
- `8px`: standard controls, inputs, search, light utility elements
- `24px`: main generator panel and homepage capability pills
- `50%`: icon-only circular buttons

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat (Level 0) | No shadow | Most of the page, including tabs, nav, text sections, media grid |
| Outlined Surface (Level 1) | `1px solid rgba(0,0,0,0.05)` | Generator card, pills, selectors, quiet containers |
| Hover Utility (Level 2) | `rgba(0,0,0,0.05)` fill without strong shadow | Active chips, placeholders, soft emphasis |
| Floating Utility (Level 3) | `0 4px 12px rgba(0,0,0,0.06), 0 2px 6px rgba(0,0,0,0.02)` | Support/help button and rare floating affordances |

**Depth Philosophy**: Jimeng does not build drama through shadows. It behaves more like a design system for a modern desktop app: mostly flat, softly outlined, and lightly frosted. Elevation is the exception, not the default.

## 7. Do's and Don'ts

### Do
- Keep the overall canvas light and low-chroma
- Use cyan-teal as the active-state accent, not as a flood-fill background color
- Pair `8px` controls with `24px` hero modules and pills
- Use borders before shadows when you need separation
- Keep most interface copy in the compact `12px-14px` range
- Let thumbnails, generated assets, or canvases provide the visual richness

### Don't
- Don't convert this system into a glossy dark AI aesthetic; the current homepage is intentionally bright and operational
- Don't overuse blur, neon glow, or oversized shadows
- Don't introduce saturated secondary colors that compete with the cyan accent
- Don't replace the mixed type system with a single generic font everywhere
- Don't sharpen the corners; the soft `8px` / `24px` rhythm is part of the product feel

## 8. Responsive Behavior

Observed CSS includes breakpoints around:
- `max-width: 626px`
- `max-width: 860px`
- `max-width: 1279px`
- `max-width: 1536px`
- `max-width: 1920px`

### Responsive Principles
- The layout appears to preserve the left-rail + content-shell logic on wide screens
- Large working modules and discovery tiles compress before the interface changes visual language
- Compact controls and short labels make the system resilient when widths tighten
- Discovery tiles likely reduce column count progressively rather than switching to radically different card styling

## 9. Agent Prompt Guide

- **Canvas**: use a light neutral workspace background like `#f8f9fa`
- **Primary surfaces**: place key modules on `rgba(255,255,255,0.92)` cards with `24px` radius
- **Accent**: use `#00a1c2` or `#00cae0` only for active states, selected labels, and small emphasis moments
- **Text**: rely on `#0f1419` for primary copy and `#536471` / `#72808a` for quieter UI text
- **Controls**: use `8px` radius, hairline borders, and outlined styling before filled styling
- **Typography**: combine `CapCut Sans` / `PingFang SC` for UI with a heavier display face for short headline moments
- **Depth**: keep the system mostly flat; use subtle borders and very rare shadows

**Prompt starter**

`Build an AI creation workspace inspired by Jimeng AI. Use a soft light canvas, white translucent panels with 24px radius, compact 8px controls, near-black text, muted gray-blue secondary copy, and a restrained cyan accent for active states. Keep the interface product-like and operational rather than cinematic or neon-heavy.`
