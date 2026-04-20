#!/usr/bin/env python3
"""Generate a DESIGN.md draft from a cloned self-contained HTML file."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from html import escape
from html.parser import HTMLParser
from pathlib import Path


COLOR_TOKEN_RE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)|\b(?:white|black)\b"
)
DECLARATION_RE = re.compile(r"([-\w]+)\s*:\s*([^;{}]+);")
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.IGNORECASE | re.DOTALL)
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*:[^{}]*)\}")
MEDIA_QUERY_RE = re.compile(
    r"@media[^{]*\((min|max)-width\s*:\s*([^)]+)\)", re.IGNORECASE
)
LENGTH_RE = re.compile(r"(-?\d*\.?\d+)(px|rem|em)\b", re.IGNORECASE)

GENERIC_FONTS = {
    "serif",
    "sans-serif",
    "monospace",
    "system-ui",
    "ui-sans-serif",
    "ui-serif",
    "ui-monospace",
    "cursive",
    "fantasy",
    "emoji",
    "math",
    "fangsong",
}

SKIP_COLOR_VALUES = {
    "transparent",
    "currentcolor",
    "inherit",
    "initial",
    "unset",
    "none",
}

ROLE_LABELS = {
    "display": "Display / Hero",
    "section": "Section Heading",
    "subheading": "Sub-heading",
    "body": "Body",
    "button": "Button / CTA",
    "caption": "Caption / Label",
    "code": "Code / Mono",
}

ROLE_ORDER = ["display", "section", "subheading", "body", "button", "caption", "code"]

TRACKED_PROPS = {
    "font-family",
    "font-size",
    "font-weight",
    "line-height",
    "letter-spacing",
    "color",
    "background",
    "background-color",
    "border",
    "border-color",
    "border-radius",
    "box-shadow",
    "padding",
    "margin",
    "gap",
    "max-width",
    "position",
}


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def strip_css_comments(css_text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)


def resolve_css_vars(value: str, custom_props: dict[str, str]) -> str:
    resolved = value
    for _ in range(5):
        updated = re.sub(
            r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\)",
            lambda match: custom_props.get(match.group(1), normalize_space(match.group(2) or match.group(0))),
            resolved,
        )
        if updated == resolved:
            break
        resolved = updated
    return normalize_space(resolved)


def parse_declaration_map(block: str) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for prop, value in DECLARATION_RE.findall(block):
        declarations[prop.strip().lower()] = normalize_space(value)
    return declarations


def iter_css_rules(css_text: str):
    css_text = strip_css_comments(css_text)
    for match in RULE_RE.finditer(css_text):
        selectors = normalize_space(match.group(1))
        if not selectors or selectors.startswith("@"):
            continue
        declarations = parse_declaration_map(match.group(2))
        if declarations:
            yield selectors, declarations


def length_to_px(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip().lower()
    match = re.fullmatch(r"(-?\d*\.?\d+)(px|rem|em)", value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "px":
        return number
    return number * 16.0


def format_number(number: float | None) -> str:
    if number is None:
        return "—"
    if abs(number - round(number)) < 0.01:
        return str(int(round(number)))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def normalize_length(value: str) -> str:
    px = length_to_px(value)
    if px is None:
        return normalize_space(value)
    return f"{format_number(px)}px"


def parse_css_function_args(content: str) -> list[str]:
    return re.findall(r"[-+]?\d*\.?\d+%?", content)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    h = (h % 360.0) / 360.0
    s = clamp(s, 0.0, 1.0)
    l = clamp(l, 0.0, 1.0)
    if s == 0:
        gray = int(round(l * 255))
        return gray, gray, gray
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q

    def hue_to_rgb(t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    r = int(round(hue_to_rgb(h + 1 / 3) * 255))
    g = int(round(hue_to_rgb(h) * 255))
    b = int(round(hue_to_rgb(h - 1 / 3) * 255))
    return r, g, b


def parse_color_to_rgba(value: str) -> tuple[int, int, int, float] | None:
    value = normalize_space(value).lower()
    if value in SKIP_COLOR_VALUES or value.startswith("var("):
        return None
    if value == "white":
        return 255, 255, 255, 1.0
    if value == "black":
        return 0, 0, 0, 1.0

    if value.startswith("#"):
        digits = value[1:]
        if len(digits) == 3:
            digits = "".join(ch * 2 for ch in digits)
        elif len(digits) == 4:
            digits = "".join(ch * 2 for ch in digits)
        if len(digits) == 6:
            return int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16), 1.0
        if len(digits) == 8:
            return (
                int(digits[0:2], 16),
                int(digits[2:4], 16),
                int(digits[4:6], 16),
                round(int(digits[6:8], 16) / 255.0, 3),
            )
        return None

    if value.startswith(("rgb(", "rgba(")):
        parts = parse_css_function_args(value)
        if len(parts) < 3:
            return None

        def parse_rgb_part(part: str) -> int:
            if part.endswith("%"):
                return int(round(clamp(float(part[:-1]) / 100.0, 0.0, 1.0) * 255))
            return int(round(clamp(float(part), 0.0, 255.0)))

        r = parse_rgb_part(parts[0])
        g = parse_rgb_part(parts[1])
        b = parse_rgb_part(parts[2])
        alpha = 1.0
        if len(parts) >= 4:
            alpha = float(parts[3].rstrip("%"))
            if "%" in parts[3]:
                alpha = alpha / 100.0
        return r, g, b, round(clamp(alpha, 0.0, 1.0), 3)

    if value.startswith(("hsl(", "hsla(")):
        parts = parse_css_function_args(value)
        if len(parts) < 3:
            return None
        hue = float(parts[0])
        sat = float(parts[1].rstrip("%")) / 100.0
        light = float(parts[2].rstrip("%")) / 100.0
        r, g, b = hsl_to_rgb(hue, sat, light)
        alpha = 1.0
        if len(parts) >= 4:
            alpha = float(parts[3].rstrip("%"))
            if "%" in parts[3]:
                alpha = alpha / 100.0
        return r, g, b, round(clamp(alpha, 0.0, 1.0), 3)

    return None


def rgba_to_string(rgba: tuple[int, int, int, float]) -> str:
    r, g, b, a = rgba
    if a >= 0.999:
        return f"#{r:02x}{g:02x}{b:02x}"
    alpha = f"{a:.3f}".rstrip("0").rstrip(".")
    return f"rgba({r}, {g}, {b}, {alpha})"


def normalize_color_token(token: str) -> str | None:
    rgba = parse_color_to_rgba(token)
    if rgba is None:
        return None
    return rgba_to_string(rgba)


def relative_luminance(rgba: tuple[int, int, int, float]) -> float:
    def channel(value: int) -> float:
        srgb = value / 255.0
        if srgb <= 0.04045:
            return srgb / 12.92
        return ((srgb + 0.055) / 1.055) ** 2.4

    r, g, b, _ = rgba
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def saturation_score(rgba: tuple[int, int, int, float]) -> float:
    r, g, b, _ = rgba
    mx = max(r, g, b)
    mn = min(r, g, b)
    if mx == 0:
        return 0.0
    return (mx - mn) / mx


def is_neutral(color: str) -> bool:
    rgba = parse_color_to_rgba(color)
    if rgba is None:
        return False
    return saturation_score(rgba) < 0.12


def describe_color(color: str) -> str:
    rgba = parse_color_to_rgba(color)
    if rgba is None:
        return f"`{color}`"
    lum = relative_luminance(rgba)
    sat = saturation_score(rgba)
    if lum < 0.25 and sat < 0.65:
        tone = "dark surface"
    elif lum > 0.85 and sat < 0.65:
        tone = "light surface"
    elif sat < 0.12:
        tone = "dark neutral" if lum < 0.25 else "light neutral" if lum > 0.82 else "mid neutral"
    else:
        tone = "muted accent" if sat < 0.4 else "vivid accent"
    return f"{tone} `{color}`"


def extract_colors(value: str) -> list[str]:
    colors: list[str] = []
    for token in COLOR_TOKEN_RE.findall(value):
        normalized = normalize_color_token(token)
        if normalized:
            colors.append(normalized)
    return colors


def split_font_names(value: str) -> list[str]:
    parts = [strip_quotes(part.strip()) for part in value.split(",")]
    return [part for part in parts if part]


def simplify_font_stack(value: str) -> str:
    parts = split_font_names(value)
    return ", ".join(parts[:3]) if parts else value


def canonical_font_key(value: str) -> str:
    return strip_quotes(value).strip().lower()


def is_monospace_stack(value: str) -> bool:
    lowered = value.lower()
    return "mono" in lowered or "code" in lowered or "monospace" in lowered


def selector_matches(selectors: str, keywords: list[str]) -> bool:
    lowered = selectors.lower()
    return any(keyword in lowered for keyword in keywords)


def classify_role(selectors: str) -> str | None:
    lowered = selectors.lower()
    if selector_matches(lowered, ["h1", ".hero", ".headline", ".display", ".masthead"]):
        return "display"
    if selector_matches(lowered, ["h2", ".section-title", ".section-heading", ".title-lg"]):
        return "section"
    if selector_matches(lowered, ["h3", "h4", ".card-title", ".subheading", ".eyebrow +"]):
        return "subheading"
    if selector_matches(lowered, ["button", ".btn", "[role=button]", "[role=\"button\"]", ".cta"]):
        return "button"
    if selector_matches(lowered, ["small", ".caption", ".eyebrow", ".label", ".meta"]):
        return "caption"
    if selector_matches(lowered, ["code", "pre", ".mono", ".terminal"]):
        return "code"
    if selector_matches(lowered, ["body", "p", "li", ".copy", ".text", ".body"]):
        return "body"
    return None


class CloneHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tag_counts: Counter[str] = Counter()
        self.inline_styles: list[str] = []
        self.text_samples: dict[str, list[str]] = defaultdict(list)
        self.capture_stack: list[tuple[str, list[str]]] = []
        self.title_parts: list[str] = []
        self.body_style: str = ""
        self.html_style: str = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        self.tag_counts[tag] += 1
        style = attrs_dict.get("style")
        if style:
            self.inline_styles.append(style)
            if tag == "body":
                self.body_style = style
            if tag == "html":
                self.html_style = style
        if tag in {"title", "button", "a", "nav", "h1", "h2", "h3", "h4", "p", "code"}:
            self.capture_stack.append((tag, []))

    def handle_data(self, data: str) -> None:
        text = normalize_space(data)
        if not text:
            return
        if self.capture_stack:
            for _, parts in self.capture_stack:
                parts.append(text)
        if any(tag == "title" for tag, _ in self.capture_stack):
            self.title_parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.capture_stack) - 1, -1, -1):
            current_tag, parts = self.capture_stack[index]
            if current_tag != tag:
                continue
            text = normalize_space(" ".join(parts))
            if text and tag != "title":
                self.text_samples[tag].append(text)
            self.capture_stack.pop(index)
            break


def sort_counter_items(counter: Counter[str], limit: int = 10, numeric: bool = False):
    items = list(counter.items())
    if numeric:
        items.sort(
            key=lambda item: (
                -(length_to_px(item[0]) or -1),
                -item[1],
                item[0],
            )
        )
    else:
        items.sort(key=lambda item: (-item[1], item[0]))
    return items[:limit]


def pick_common(counter: Counter[str], fallback: str = "—") -> str:
    if not counter:
        return fallback
    return counter.most_common(1)[0][0]


def pick_largest(counter: Counter[str], fallback: str = "—") -> str:
    if not counter:
        return fallback
    items = sorted(counter.items(), key=lambda item: (length_to_px(item[0]) or -1, item[1]), reverse=True)
    return items[0][0]


def pick_smallest(counter: Counter[str], fallback: str = "—") -> str:
    if not counter:
        return fallback
    items = sorted(counter.items(), key=lambda item: (length_to_px(item[0]) or math.inf, -item[1], item[0]))
    return items[0][0]


def most_common_font(counter: Counter[str], allow_generic: bool = False, mono_only: bool = False) -> str | None:
    for value, _count in counter.most_common():
        families = split_font_names(value)
        if not families:
            continue
        first_family = canonical_font_key(families[0])
        if mono_only and not is_monospace_stack(value):
            continue
        if not allow_generic and first_family in GENERIC_FONTS:
            continue
        return simplify_font_stack(value)
    return simplify_font_stack(counter.most_common(1)[0][0]) if counter else None


def extract_site_name(name: str | None, title: str, path: Path, url: str | None) -> str:
    if name:
        return name.strip()
    if title:
        head = re.split(r"[|\-:]", title, maxsplit=1)[0].strip()
        if head:
            return head
    if url:
        host = re.sub(r"^https?://", "", url)
        host = host.split("/", 1)[0]
        host = host[4:] if host.startswith("www.") else host
        return host
    stem = path.stem
    stem = re.sub(r"^(clone-|snapshot-)", "", stem)
    return stem or "Extracted Site"


def infer_site_name_from_paths(paths: list[Path]) -> str | None:
    if not paths:
        return None
    if len(paths) == 1:
        parent_name = paths[0].parent.name
        if parent_name and parent_name not in {"captures", "design-md"}:
            return parent_name
        return None

    common_parent = Path(os.path.commonpath([str(path.parent) for path in paths]))
    candidate = common_parent.name
    if candidate in {"captures", "design-md"} and common_parent.parent.name:
        candidate = common_parent.parent.name
    return candidate or None


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    slug = slug.strip("-")
    return slug or "site"


def choose_background_color(metrics: dict) -> str | None:
    for source in (
        metrics["body_styles"],
        metrics["html_styles"],
        metrics["role_styles"].get("body", {}),
    ):
        if not source:
            continue
        for key in ("background-color", "background"):
            if key in source and source[key]:
                for color in extract_colors(source[key]):
                    return color
    for prop in ("background-color", "background"):
        if metrics["colors_by_property"][prop]:
            return pick_common(metrics["colors_by_property"][prop])
    return None


def choose_text_color(metrics: dict) -> str | None:
    for source in (
        metrics["body_styles"],
        metrics["html_styles"],
        metrics["role_styles"].get("body", {}),
    ):
        if not source:
            continue
        if source.get("color"):
            colors = extract_colors(source["color"])
            if colors:
                return colors[0]
    if metrics["colors_by_property"]["color"]:
        return pick_common(metrics["colors_by_property"]["color"])
    return None


def choose_surface_color(metrics: dict, background: str | None) -> str | None:
    candidates = []
    for value, count in metrics["colors_by_property"]["background-color"].most_common():
        if value != background:
            candidates.append((value, count))
    for value, count in metrics["colors_by_property"]["background"].most_common():
        if value != background:
            candidates.append((value, count))
    if not candidates:
        return background
    candidates.sort(key=lambda item: (-item[1], item[0]))
    return candidates[0][0]


def choose_border_color(metrics: dict) -> str | None:
    for prop in ("border-color", "border", "box-shadow"):
        counter = metrics["colors_by_property"][prop]
        for value, _count in counter.most_common():
            return value
    return None


def summarize_palette(metrics: dict) -> dict:
    background = choose_background_color(metrics)
    text = choose_text_color(metrics)
    surface = choose_surface_color(metrics, background)
    border = choose_border_color(metrics)

    all_colors = [value for value, _count in metrics["all_colors"].most_common(30)]
    accents = [color for color in all_colors if not is_neutral(color) and color not in {background, text, surface}]
    neutrals = [color for color in all_colors if is_neutral(color)]

    accent_list = accents[:4]
    neutral_list = []
    for candidate in [background, text, surface, border, *neutrals]:
        if candidate and candidate not in neutral_list and is_neutral(candidate):
            neutral_list.append(candidate)

    return {
        "background": background,
        "text": text,
        "surface": surface,
        "border": border,
        "accents": accent_list,
        "neutrals": neutral_list[:6],
    }


def infer_theme_mood(palette: dict, fonts: dict, radii: list[str], shadows: list[str]) -> str:
    phrases: list[str] = []
    background = palette.get("background")
    if background:
        rgba = parse_color_to_rgba(background)
        if rgba is not None:
            luminance = relative_luminance(rgba)
            if luminance < 0.2:
                phrases.append("dark-surface")
            elif luminance > 0.85:
                phrases.append("light-surface")
            else:
                phrases.append("mid-tone")
            if saturation_score(rgba) < 0.12:
                phrases.append("neutral-led")
            else:
                phrases.append("chromatic-led")

    accents = palette.get("accents", [])
    if len(accents) == 0:
        phrases.append("highly restrained")
    elif len(accents) == 1:
        phrases.append("single-accent")
    else:
        phrases.append("multi-accent")

    primary_families = [canonical_font_key(part) for part in split_font_names(fonts.get("primary") or "")]
    if "serif" in primary_families:
        phrases.append("editorial")
    elif "monospace" in primary_families or any("mono" in family for family in primary_families):
        phrases.append("technical")
    else:
        phrases.append("product-oriented")

    max_radius = max((length_to_px(radius) or 0 for radius in radii), default=0)
    if max_radius >= 999:
        phrases.append("pill-heavy")
    elif max_radius >= 24:
        phrases.append("soft-cornered")
    else:
        phrases.append("tight-cornered")

    if shadows:
        phrases.append("layered depth")
    else:
        phrases.append("flat depth")

    return ", ".join(phrases)


def build_role_summary(metrics: dict, global_fonts: Counter[str], global_sizes: Counter[str]) -> dict[str, dict[str, str]]:
    role_summaries: dict[str, dict[str, str]] = {}
    sorted_sizes_desc = [value for value, _count in sort_counter_items(global_sizes, limit=12, numeric=True)]
    common_body_size = next(
        (value for value, _count in global_sizes.most_common() if 13 <= (length_to_px(value) or 0) <= 20),
        None,
    )
    small_size = next(
        (value for value in reversed(sorted_sizes_desc) if 9 <= (length_to_px(value) or 0) <= 14),
        None,
    )

    for role in ROLE_ORDER:
        props = metrics["role_properties"][role]
        if role == "display":
            font_size = pick_largest(props["font-size"], sorted_sizes_desc[0] if sorted_sizes_desc else "—")
        elif role == "section":
            font_size = pick_largest(
                props["font-size"],
                sorted_sizes_desc[1] if len(sorted_sizes_desc) > 1 else sorted_sizes_desc[0] if sorted_sizes_desc else "—",
            )
        elif role == "subheading":
            font_size = pick_largest(
                props["font-size"],
                sorted_sizes_desc[2] if len(sorted_sizes_desc) > 2 else common_body_size or "—",
            )
        elif role == "caption":
            font_size = pick_smallest(props["font-size"], small_size or common_body_size or "—")
        elif role == "button":
            font_size = pick_common(props["font-size"], common_body_size or "—")
        else:
            font_size = pick_common(props["font-size"], common_body_size or "—")

        font_family = most_common_font(props["font-family"]) or most_common_font(global_fonts, allow_generic=True) or "—"
        if role == "code":
            font_family = most_common_font(props["font-family"], mono_only=True) or most_common_font(global_fonts, mono_only=True) or font_family

        role_summaries[role] = {
            "font": font_family or "—",
            "size": font_size,
            "weight": pick_common(props["font-weight"]),
            "line_height": pick_common(props["line-height"]),
            "letter_spacing": pick_common(props["letter-spacing"]),
            "notes": "Inferred from matching CSS selectors" if props["font-size"] or props["font-family"] else "Fallback from global CSS frequency",
        }

    return role_summaries


def compute_base_spacing(spacing_counter: Counter[str]) -> str | None:
    values = {int(round(length_to_px(value) or 0)) for value in spacing_counter if (length_to_px(value) or 0) > 0}
    for candidate in (8, 4, 6, 10, 12):
        if candidate in values:
            return f"{candidate}px"
    return f"{min(values)}px" if values else None


def describe_spacing_density(spacing_counter: Counter[str]) -> str:
    large_values = [length_to_px(value) or 0 for value in spacing_counter]
    if not large_values:
        return "Spacing is not explicit in the clone and should be treated as inferred."
    average = sum(large_values) / len(large_values)
    if average >= 24:
        return "Spacing trends generous, with larger gaps and more breathable section rhythm."
    if average >= 14:
        return "Spacing sits in a balanced middle range, mixing compact UI gaps with comfortable content gutters."
    return "Spacing is compact and UI-dense, favoring tighter gaps and smaller step sizes."


def collect_metrics(html_text: str, html_path: Path) -> dict:
    parser = CloneHTMLParser()
    parser.feed(html_text)

    style_blocks = STYLE_BLOCK_RE.findall(html_text)
    all_css = "\n".join(style_blocks)
    inline_css = "\n".join(parser.inline_styles)
    all_style_text = "\n".join([all_css, inline_css])

    declaration_values: dict[str, Counter[str]] = defaultdict(Counter)
    colors_by_property: dict[str, Counter[str]] = defaultdict(Counter)
    role_properties: dict[str, dict[str, Counter[str]]] = {
        role: defaultdict(Counter) for role in ROLE_ORDER
    }
    role_styles: dict[str, dict[str, str]] = {role: {} for role in ROLE_ORDER}
    component_properties: dict[str, dict[str, Counter[str]]] = {
        "button": defaultdict(Counter),
        "nav": defaultdict(Counter),
        "card": defaultdict(Counter),
        "input": defaultdict(Counter),
    }
    all_colors: Counter[str] = Counter()
    font_families: Counter[str] = Counter()
    custom_properties: Counter[str] = Counter()
    raw_declarations: list[tuple[str, str]] = []

    for prop, value in DECLARATION_RE.findall(strip_css_comments(all_style_text)):
        prop = prop.strip().lower()
        value = normalize_space(value)
        raw_declarations.append((prop, value))
        declaration_values[prop][value] += 1

        if prop.startswith("--"):
            custom_properties[prop] += 1

        if prop == "font-family":
            font_families[simplify_font_stack(value)] += 1
    custom_prop_values = {
        prop: pick_common(values)
        for prop, values in declaration_values.items()
        if prop.startswith("--")
    }

    for prop, value in raw_declarations:
        resolved_value = resolve_css_vars(value, custom_prop_values)
        for color in extract_colors(resolved_value):
            all_colors[color] += 1
            colors_by_property[prop][color] += 1

    body_styles = parse_declaration_map(parser.body_style) if parser.body_style else {}
    body_styles = {key: resolve_css_vars(value, custom_prop_values) for key, value in body_styles.items()}
    html_styles = parse_declaration_map(parser.html_style) if parser.html_style else {}
    html_styles = {key: resolve_css_vars(value, custom_prop_values) for key, value in html_styles.items()}

    for selectors, declarations in iter_css_rules(all_css):
        resolved_declarations = {
            prop: resolve_css_vars(value, custom_prop_values) for prop, value in declarations.items()
        }
        role = classify_role(selectors)
        if role:
            for prop, value in resolved_declarations.items():
                if prop in TRACKED_PROPS:
                    role_properties[role][prop][value] += 1
                    role_styles[role][prop] = value

        lowered = selectors.lower()
        if selector_matches(lowered, ["button", ".btn", "[role=button]", "[role=\"button\"]", ".cta"]):
            for prop, value in resolved_declarations.items():
                if prop in TRACKED_PROPS:
                    component_properties["button"][prop][value] += 1
        if selector_matches(lowered, ["nav", "header", ".navbar", ".navigation", ".topbar"]):
            for prop, value in resolved_declarations.items():
                if prop in TRACKED_PROPS:
                    component_properties["nav"][prop][value] += 1
        if selector_matches(lowered, ["input", "textarea", "select", ".field", ".form"]):
            for prop, value in resolved_declarations.items():
                if prop in TRACKED_PROPS:
                    component_properties["input"][prop][value] += 1
        if selector_matches(lowered, [".card", ".panel", ".tile", ".surface", ".feature-card"]):
            for prop, value in resolved_declarations.items():
                if prop in TRACKED_PROPS:
                    component_properties["card"][prop][value] += 1

    palette = summarize_palette(
        {
            "body_styles": body_styles,
            "html_styles": html_styles,
            "role_styles": role_styles,
            "colors_by_property": colors_by_property,
            "all_colors": all_colors,
        }
    )

    radii_counter = declaration_values["border-radius"]
    shadow_counter = declaration_values["box-shadow"]
    spacing_counter: Counter[str] = Counter()
    for prop in ("padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
                 "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
                 "gap", "row-gap", "column-gap"):
        for value, count in declaration_values[prop].items():
            for number, unit in LENGTH_RE.findall(value):
                spacing_counter[normalize_length(f"{number}{unit}")] += count

    max_width_counter: Counter[str] = Counter()
    for prop in ("max-width", "width"):
        for value, count in declaration_values[prop].items():
            px = length_to_px(value)
            if px is not None and 240 <= px <= 2000:
                max_width_counter[normalize_length(value)] += count

    breakpoint_counter: Counter[str] = Counter()
    for direction, raw_value in MEDIA_QUERY_RE.findall(all_css):
        px = length_to_px(normalize_space(raw_value))
        if px is not None:
            breakpoint_counter[f"{direction}:{format_number(px)}px"] += 1

    typography = build_role_summary(
        {
            "role_properties": role_properties,
        },
        font_families,
        declaration_values["font-size"],
    )

    fonts = {
        "primary": most_common_font(font_families),
        "mono": most_common_font(font_families, mono_only=True),
        "all": [value for value, _count in font_families.most_common(8)],
    }

    return {
        "html_path": str(html_path),
        "html_title": normalize_space(" ".join(parser.title_parts)),
        "tag_counts": dict(parser.tag_counts),
        "text_samples": {tag: values[:12] for tag, values in parser.text_samples.items()},
        "body_styles": body_styles,
        "html_styles": html_styles,
        "all_colors": all_colors,
        "colors_by_property": colors_by_property,
        "palette": palette,
        "fonts": fonts,
        "custom_properties": custom_properties,
        "declaration_values": declaration_values,
        "role_properties": role_properties,
        "role_styles": role_styles,
        "component_properties": component_properties,
        "typography": typography,
        "radii": [value for value, _count in sort_counter_items(radii_counter, limit=8, numeric=True)],
        "shadows": [value for value, _count in shadow_counter.most_common(6)],
        "spacing": [value for value, _count in sort_counter_items(spacing_counter, limit=10, numeric=True)],
        "spacing_counter": spacing_counter,
        "max_widths": [value for value, _count in sort_counter_items(max_width_counter, limit=6, numeric=True)],
        "breakpoints": [value for value, _count in breakpoint_counter.most_common(8)],
    }


def component_value(counter_map: dict[str, Counter[str]], prop: str, fallback: str = "—") -> str:
    return pick_common(counter_map.get(prop, Counter()), fallback)


def render_color_roles(palette: dict) -> str:
    lines = ["### Primary"]
    if palette.get("background"):
        lines.append(f"- **Primary Background** ({palette['background']}): Main canvas and dominant page surface.")
    if palette.get("text"):
        lines.append(f"- **Primary Text** ({palette['text']}): Default heading and body text color.")
    if palette.get("surface") and palette["surface"] != palette.get("background"):
        lines.append(f"- **Surface** ({palette['surface']}): Elevated cards, inner panels, or softened section surfaces.")
    if palette.get("border"):
        lines.append(f"- **Border / Divider** ({palette['border']}): Lines, separators, low-contrast containment, or shadow-border treatment.")

    lines.append("")
    lines.append("### Accent Colors")
    if palette.get("accents"):
        for index, color in enumerate(palette["accents"], start=1):
            lines.append(f"- **Accent {index}** ({color}): Repeating non-neutral emphasis color observed in links, CTAs, badges, charts, or highlights.")
    else:
        lines.append("- No strong recurring accent color was obvious in the clone; the palette appears neutral-led.")

    lines.append("")
    lines.append("### Neutral Scale")
    for index, color in enumerate(palette.get("neutrals", []), start=1):
        lines.append(f"- **Neutral {index}** ({color}): Repeating neutral used somewhere in the background, text, border, or surface stack.")
    return "\n".join(lines)


def render_typography_table(typography: dict[str, dict[str, str]]) -> str:
    lines = [
        "| Role | Font | Size | Weight | Line Height | Letter Spacing | Notes |",
        "|------|------|------|--------|-------------|----------------|-------|",
    ]
    for role in ROLE_ORDER:
        data = typography[role]
        lines.append(
            "| {role} | {font} | {size} | {weight} | {line_height} | {letter_spacing} | {notes} |".format(
                role=ROLE_LABELS[role],
                font=data["font"] or "—",
                size=data["size"] or "—",
                weight=data["weight"] or "—",
                line_height=data["line_height"] or "—",
                letter_spacing=data["letter_spacing"] or "—",
                notes=data["notes"],
            )
        )
    return "\n".join(lines)


def render_typography_principles(fonts: dict, typography: dict[str, dict[str, str]]) -> str:
    lines = []
    primary = fonts.get("primary")
    mono = fonts.get("mono")
    if primary:
        lines.append(f"- **Primary font stack**: `{primary}` anchors most of the visible interface.")
    if mono:
        lines.append(f"- **Monospace companion**: `{mono}` appears in code-like or technical contexts.")
    display_size = typography["display"]["size"]
    body_size = typography["body"]["size"]
    if display_size != "—" and body_size != "—":
        lines.append(f"- **Hierarchy contrast**: display text peaks around `{display_size}` while body copy clusters around `{body_size}`.")
    button_weight = typography["button"]["weight"]
    if button_weight != "—":
        lines.append(f"- **Interactive emphasis**: CTA or button text often uses weight `{button_weight}`.")
    return "\n".join(lines) or "- Typography should be reviewed manually; the clone did not expose strong recurring text rules."


def resolve_input_paths(raw_paths: list[str], capture_dir: str | None) -> list[Path]:
    resolved: list[Path] = []
    seen: set[Path] = set()

    def add_path(path: Path) -> None:
        candidate = path.expanduser().resolve()
        if candidate in seen:
            return
        seen.add(candidate)
        resolved.append(candidate)

    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_dir():
            clone_candidates = sorted(path.rglob("clone.html"))
            if clone_candidates:
                for candidate in clone_candidates:
                    add_path(candidate)
                continue
            for candidate in sorted(path.rglob("*.html")):
                add_path(candidate)
            continue
        add_path(path)

    if capture_dir:
        capture_root = Path(capture_dir).expanduser().resolve()
        clone_candidates = sorted(capture_root.rglob("clone.html"))
        if clone_candidates:
            for candidate in clone_candidates:
                add_path(candidate)
        else:
            for candidate in sorted(capture_root.rglob("*.html")):
                add_path(candidate)

    return resolved


def build_source_context(input_paths: list[Path], url: str | None, capture_dir: str | None) -> dict:
    capture_root = Path(capture_dir).expanduser().resolve() if capture_dir else None
    if capture_root is None and len(input_paths) > 1:
        capture_root = Path(os.path.commonpath([str(path.parent) for path in input_paths]))

    labels: list[str] = []
    for path in input_paths:
        label = str(path)
        if capture_root is not None:
            try:
                label = path.relative_to(capture_root).as_posix()
            except ValueError:
                label = path.name
        elif len(input_paths) == 1:
            label = path.name
        labels.append(label)

    return {
        "url": url,
        "count": len(input_paths),
        "input_paths": [str(path) for path in input_paths],
        "labels": labels,
        "capture_dir": str(capture_root) if capture_root else None,
        "mode": "multi" if len(input_paths) > 1 else "single",
    }


def render_source_scope(source_context: dict) -> str:
    if not source_context["input_paths"]:
        return ""
    lines = [
        f"### Capture Scope",
        f"- Snapshot count: `{source_context['count']}`",
    ]
    if source_context.get("url"):
        lines.append(f"- Live source: `{source_context['url']}`")
    if source_context.get("capture_dir"):
        lines.append(f"- Capture root: `{source_context['capture_dir']}`")
    lines.append("- Included snapshots:")
    for label in source_context["labels"][:8]:
        lines.append(f"- `{label}`")
    remaining = source_context["count"] - min(source_context["count"], 8)
    if remaining > 0:
        lines.append(f"- ... plus `{remaining}` more snapshot(s)")
    return "\n".join(lines)


def source_summary_text(source_context: dict) -> str:
    if source_context["count"] <= 1:
        return source_context.get("url") or source_context["input_paths"][0]
    if source_context.get("url"):
        return f"{source_context['count']} cloned pages captured from {source_context['url']}"
    return f"{source_context['count']} cloned pages"


def source_note_text(source_context: dict, metrics: dict) -> str:
    if source_context["count"] <= 1:
        return f"Source URL: {source_context['url']}" if source_context.get("url") else f"Source clone: {metrics['html_path']}"
    if source_context.get("url"):
        return f"Source URL: {source_context['url']} ({source_context['count']} captured pages)"
    return f"Source clones: {source_context['count']} captured pages"


def render_component_section(metrics: dict) -> str:
    palette = metrics["palette"]
    components = metrics["component_properties"]
    lines = [
        "### Buttons",
        f"- Background: `{component_value(components['button'], 'background-color', component_value(components['button'], 'background', palette.get('surface') or palette.get('background') or '—'))}`",
        f"- Text: `{component_value(components['button'], 'color', palette.get('text') or '—')}`",
        f"- Radius: `{component_value(components['button'], 'border-radius', metrics['radii'][0] if metrics['radii'] else '—')}`",
        f"- Shadow / Border: `{component_value(components['button'], 'box-shadow', component_value(components['button'], 'border', palette.get('border') or '—'))}`",
        "",
        "### Cards & Containers",
        f"- Surface: `{component_value(components['card'], 'background-color', palette.get('surface') or palette.get('background') or '—')}`",
        f"- Radius: `{component_value(components['card'], 'border-radius', metrics['radii'][0] if metrics['radii'] else '—')}`",
        f"- Shadow / Border: `{component_value(components['card'], 'box-shadow', component_value(components['card'], 'border', metrics['shadows'][0] if metrics['shadows'] else palette.get('border') or '—'))}`",
        "",
        "### Navigation",
        f"- Positioning clue: `{component_value(components['nav'], 'position', 'not explicit in clone')}`",
        f"- Text color: `{component_value(components['nav'], 'color', palette.get('text') or '—')}`",
        f"- Background: `{component_value(components['nav'], 'background-color', component_value(components['nav'], 'background', palette.get('background') or '—'))}`",
    ]
    if metrics["tag_counts"].get("input") or metrics["tag_counts"].get("textarea") or components["input"]:
        lines.extend(
            [
                "",
                "### Inputs & Forms",
                f"- Background: `{component_value(components['input'], 'background-color', palette.get('surface') or palette.get('background') or '—')}`",
                f"- Text: `{component_value(components['input'], 'color', palette.get('text') or '—')}`",
                f"- Radius: `{component_value(components['input'], 'border-radius', metrics['radii'][0] if metrics['radii'] else '—')}`",
            ]
        )
    return "\n".join(lines)


def render_layout_section(metrics: dict) -> str:
    base_spacing = compute_base_spacing(metrics["spacing_counter"])
    width_lines = ", ".join(f"`{value}`" for value in metrics["max_widths"][:4]) or "not explicit in clone"
    radius_lines = ", ".join(f"`{value}`" for value in metrics["radii"][:6]) or "not explicit in clone"
    spacing_lines = ", ".join(f"`{value}`" for value in metrics["spacing"][:8]) or "not explicit in clone"
    return "\n".join(
        [
            "### Spacing System",
            f"- Suggested base unit: `{base_spacing}`" if base_spacing else "- Suggested base unit: not explicit in the clone",
            f"- Repeating spacing values: {spacing_lines}",
            f"- Rhythm note: {describe_spacing_density(metrics['spacing_counter'])}",
            "",
            "### Grid & Container",
            f"- Observed content widths: {width_lines}",
            "- Treat the layout as content-width-led unless the live site clearly relies on edge-to-edge sections.",
            "",
            "### Border Radius Scale",
            f"- Observed radius values: {radius_lines}",
        ]
    )


def render_depth_section(metrics: dict) -> str:
    shadows = metrics["shadows"]
    if not shadows:
        return "\n".join(
            [
                "| Level | Treatment | Use |",
                "|-------|-----------|-----|",
                "| Flat (Level 0) | No recurring shadow language was obvious in the clone | Keep surfaces mostly flat and rely on spacing or borders |",
            ]
        )
    lines = [
        "| Level | Treatment | Use |",
        "|-------|-----------|-----|",
    ]
    for index, shadow in enumerate(shadows[:4], start=1):
        label = "Ring / Border" if index == 1 else f"Elevation {index - 1}"
        use = "Primary containment or border substitute" if index == 1 else "Elevated card, popover, or highlighted surface"
        lines.append(f"| {label} | `{shadow}` | {use} |")
    return "\n".join(lines)


def render_dos_and_donts(metrics: dict) -> str:
    palette = metrics["palette"]
    lines = ["### Do"]
    if palette.get("background") and palette.get("text"):
        lines.append(f"- Keep the core contrast anchored on `{palette['background']}` surfaces with `{palette['text']}` text.")
    if metrics["fonts"].get("primary"):
        lines.append(f"- Reuse the `{metrics['fonts']['primary']}` stack, or a very close fallback, as the dominant voice.")
    if metrics["radii"]:
        lines.append(f"- Stay inside the extracted radius family: {', '.join(f'`{value}`' for value in metrics['radii'][:4])}.")

    lines.append("")
    lines.append("### Don't")
    if palette.get("accents"):
        lines.append("- Do not introduce extra accent colors outside the observed palette unless the source product clearly does so.")
    else:
        lines.append("- Do not add flashy accent colors; the source appears deliberately restrained.")
    if metrics["shadows"]:
        lines.append("- Do not swap the extracted shadow language for heavier, blurrier shadows with a different visual weight.")
    else:
        lines.append("- Do not compensate for missing depth by overusing shadows; rely on spacing, borders, and contrast first.")
    lines.append("- Do not mix unrelated type systems or corner treatments that sit outside the extracted visual vocabulary.")
    return "\n".join(lines)


def render_responsive_section(metrics: dict) -> str:
    lines = []
    if metrics["breakpoints"]:
        lines.append("- Explicit media-query breakpoints observed in the clone:")
        for value in metrics["breakpoints"]:
            direction, width = value.split(":", 1)
            lines.append(f"- `{direction}-width: {width}`")
    else:
        lines.append("- No explicit media-query breakpoints were detected in the clone; responsive behavior may rely on fluid sizing, utility classes, or runtime styling.")
    nav_count = metrics["tag_counts"].get("nav", 0)
    if nav_count:
        lines.append("- Navigation is present in the DOM and should be preserved as a top-level responsive priority.")
    button_count = metrics["tag_counts"].get("button", 0)
    if button_count:
        lines.append("- Button-heavy interfaces should preserve clear CTA hierarchy and comfortable tap targets when collapsed.")
    return "\n".join(lines)


def render_prompt_guide(site_name: str, metrics: dict) -> str:
    palette = metrics["palette"]
    accents = ", ".join(f"`{color}`" for color in palette["accents"]) if palette["accents"] else "no strong accent color"
    radii = ", ".join(f"`{value}`" for value in metrics["radii"][:4]) if metrics["radii"] else "tight, low-variance radii"
    shadows = metrics["shadows"][0] if metrics["shadows"] else "minimal shadow use"
    font = metrics["fonts"].get("primary") or "the extracted primary font stack"
    return "\n".join(
        [
            f"- **Canvas**: favor `{palette['background']}` surfaces with `{palette['text']}` text." if palette.get("background") and palette.get("text") else "- **Canvas**: keep a restrained surface/text contrast model.",
            f"- **Accents**: {accents}.",
            f"- **Typography**: build the hierarchy around `{font}`.",
            f"- **Corners**: stay close to {radii}.",
            f"- **Depth**: reuse `{shadows}` as the primary elevation cue.",
            "",
            "**Prompt starter**",
            "",
            f"`Build a landing page inspired by {site_name}. Use {font}, keep the palette anchored on {palette.get('background') or 'the extracted background color'} and {palette.get('text') or 'the extracted text color'}, reuse accents like {palette['accents'][0] if palette['accents'] else 'the observed neutrals'}, keep radius values around {metrics['radii'][0] if metrics['radii'] else 'the extracted radius scale'}, and match the extracted shadow/border language instead of inventing a new style.`",
        ]
    )


def render_design_md(site_name: str, metrics: dict, source_context: dict) -> str:
    palette = metrics["palette"]
    theme_mood = infer_theme_mood(palette, metrics["fonts"], metrics["radii"], metrics["shadows"])
    source_note = source_note_text(source_context, metrics)
    visual_lines = [
        f"{site_name}'s visual language reads as a {theme_mood} system. The interface is anchored on {describe_color(palette['background']) if palette.get('background') else 'an inferred dominant background'} with {describe_color(palette['text']) if palette.get('text') else 'an inferred dominant text color'} carrying most of the legibility load.",
        f"Typography appears to be led by `{metrics['fonts']['primary']}`." if metrics["fonts"].get("primary") else "Typography should be reviewed manually; no strong primary stack was isolated from the clone.",
    ]
    if palette["accents"]:
        visual_lines.append(
            "Accent usage centers on "
            + ", ".join(f"`{color}`" for color in palette["accents"][:3])
            + ", which appear as the most repeated non-neutral highlights in the extracted CSS."
        )
    if metrics["radii"]:
        visual_lines.append(
            f"Shape language clusters around {', '.join(f'`{value}`' for value in metrics['radii'][:4])}, while depth relies on {'`' + metrics['shadows'][0] + '`' if metrics['shadows'] else 'very light or absent shadowing'}."
        )

    sections = [
        f"# Design System: {site_name}",
        "",
        f"> Extracted from a cloned HTML snapshot. {source_note}. Some component roles and mood descriptions are inferred from recurring CSS patterns.",
        "",
        render_source_scope(source_context),
        "",
        "## 1. Visual Theme & Atmosphere",
        "",
        "\n\n".join(visual_lines),
        "",
        "## 2. Color Palette & Roles",
        "",
        render_color_roles(palette),
        "",
        "## 3. Typography Rules",
        "",
        "### Font Family",
        "",
        f"- **Primary**: `{metrics['fonts']['primary']}`" if metrics["fonts"].get("primary") else "- **Primary**: not explicit in clone",
        f"- **Monospace**: `{metrics['fonts']['mono']}`" if metrics["fonts"].get("mono") else "- **Monospace**: not explicit in clone",
        "",
        "### Hierarchy",
        "",
        render_typography_table(metrics["typography"]),
        "",
        "### Principles",
        "",
        render_typography_principles(metrics["fonts"], metrics["typography"]),
        "",
        "## 4. Component Stylings",
        "",
        render_component_section(metrics),
        "",
        "## 5. Layout Principles",
        "",
        render_layout_section(metrics),
        "",
        "## 6. Depth & Elevation",
        "",
        render_depth_section(metrics),
        "",
        "## 7. Do's and Don'ts",
        "",
        render_dos_and_donts(metrics),
        "",
        "## 8. Responsive Behavior",
        "",
        render_responsive_section(metrics),
        "",
        "## 9. Agent Prompt Guide",
        "",
        render_prompt_guide(site_name, metrics),
        "",
    ]
    return "\n".join(sections)


def is_dark_color(color: str | None) -> bool:
    if not color:
        return False
    rgba = parse_color_to_rgba(color)
    if rgba is None:
        return False
    return relative_luminance(rgba) < 0.45


def contrast_text_for(color: str | None, dark: str = "#0f172a", light: str = "#ffffff") -> str:
    if not color:
        return dark
    rgba = parse_color_to_rgba(color)
    if rgba is None:
        return dark
    return light if relative_luminance(rgba) < 0.45 else dark


def pick_text_sample(metrics: dict, tags: list[str], fallback: str) -> str:
    for tag in tags:
        samples = metrics["text_samples"].get(tag, [])
        for sample in samples:
            clean = normalize_space(sample)
            if clean:
                return clean
    return fallback


def shorten_text(text: str, limit: int = 90) -> str:
    clean = normalize_space(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def build_preview_theme(metrics: dict, mode: str) -> dict[str, str]:
    palette = metrics["palette"]
    background = palette.get("background") or ("#ffffff" if mode == "light" else "#0b1020")
    text = palette.get("text") or ("#111827" if mode == "light" else "#f8fafc")
    surface = palette.get("surface") or ("#ffffff" if mode == "light" else "#111827")
    border = palette.get("border") or ("rgba(15, 23, 42, 0.12)" if mode == "light" else "rgba(248, 250, 252, 0.14)")
    accent = palette["accents"][0] if palette["accents"] else ("#2563eb" if mode == "light" else "#38bdf8")
    accent_alt = palette["accents"][1] if len(palette["accents"]) > 1 else accent

    neutral_candidates = [color for color in palette.get("neutrals", []) if color not in {background, text}]
    muted = neutral_candidates[0] if neutral_candidates else ("#64748b" if mode == "light" else "rgba(226, 232, 240, 0.72)")

    if mode == "light":
        page_bg = background if not is_dark_color(background) else "#f6f7fb"
        page_fg = text if is_dark_color(text) else "#111827"
        panel_bg = surface if not is_dark_color(surface) else "#ffffff"
        chrome_bg = "#ffffff"
        divider = border
    else:
        page_bg = background if is_dark_color(background) else "#0b1020"
        page_fg = text if not is_dark_color(text) else "#f8fafc"
        panel_bg = surface if is_dark_color(surface) else "#111827"
        chrome_bg = "rgba(15, 23, 42, 0.84)"
        divider = border if is_dark_color(page_bg) else "rgba(248, 250, 252, 0.14)"

    panel_fg = contrast_text_for(panel_bg, dark="#0f172a", light="#f8fafc")
    button_bg = component_value(
        metrics["component_properties"]["button"],
        "background-color",
        component_value(metrics["component_properties"]["button"], "background", accent),
    )
    button_fg = component_value(
        metrics["component_properties"]["button"],
        "color",
        contrast_text_for(button_bg),
    )

    return {
        "page_bg": page_bg,
        "page_fg": page_fg,
        "chrome_bg": chrome_bg,
        "panel_bg": panel_bg,
        "panel_fg": panel_fg,
        "divider": divider,
        "muted": muted,
        "accent": accent,
        "accent_alt": accent_alt,
        "button_bg": button_bg,
        "button_fg": button_fg,
        "button_radius": component_value(
            metrics["component_properties"]["button"],
            "border-radius",
            metrics["radii"][0] if metrics["radii"] else "12px",
        ),
        "button_shadow": component_value(
            metrics["component_properties"]["button"],
            "box-shadow",
            metrics["shadows"][0] if metrics["shadows"] else f"0 0 0 1px {divider}",
        ),
        "card_bg": component_value(
            metrics["component_properties"]["card"],
            "background-color",
            component_value(metrics["component_properties"]["card"], "background", panel_bg),
        ),
        "card_radius": component_value(
            metrics["component_properties"]["card"],
            "border-radius",
            metrics["radii"][1] if len(metrics["radii"]) > 1 else metrics["radii"][0] if metrics["radii"] else "20px",
        ),
        "card_shadow": component_value(
            metrics["component_properties"]["card"],
            "box-shadow",
            component_value(metrics["component_properties"]["card"], "border", metrics["shadows"][0] if metrics["shadows"] else f"0 0 0 1px {divider}"),
        ),
        "input_bg": component_value(
            metrics["component_properties"]["input"],
            "background-color",
            panel_bg,
        ),
        "input_radius": component_value(
            metrics["component_properties"]["input"],
            "border-radius",
            metrics["radii"][0] if metrics["radii"] else "12px",
        ),
        "input_border": component_value(
            metrics["component_properties"]["input"],
            "border",
            border,
        ),
        "font_primary": metrics["fonts"].get("primary") or "system-ui, sans-serif",
        "font_mono": metrics["fonts"].get("mono") or "ui-monospace, SFMono-Regular, monospace",
    }


def render_readme(site_name: str, source_context: dict) -> str:
    source_label = source_summary_text(source_context)
    source_host = site_name.lower()
    if source_context.get("url"):
        source_host = re.sub(r"^https?://", "", source_context["url"]).split("/", 1)[0]
    link_target = source_context.get("url") or "./DESIGN.md"
    scope_lines = [
        "## Capture Scope",
        "",
        f"- Snapshot count: `{source_context['count']}`",
    ]
    if source_context.get("capture_dir"):
        scope_lines.append(f"- Capture root: `{source_context['capture_dir']}`")
    for label in source_context["labels"][:8]:
        scope_lines.append(f"- `{label}`")
    if source_context["count"] > 8:
        scope_lines.append(f"- ... plus `{source_context['count'] - 8}` more snapshot(s)")
    return "\n".join(
        [
            f"# {site_name} Inspired Design System",
            "",
            f"[DESIGN.md](./DESIGN.md) extracted from the public [{source_host}]({link_target}) website. This is not the official design system. Colors, fonts, spacing, and component behavior may not be 100% accurate, but it is a strong starting point for building something visually similar.",
            "",
            "## Files",
            "",
            "| File | Description |",
            "|------|-------------|",
            "| `DESIGN.md` | Complete design system documentation (9 sections) |",
            "| `preview.html` | Interactive design token catalog (light) |",
            "| `preview-dark.html` | Interactive design token catalog (dark) |",
            "",
            f"Use [DESIGN.md](./DESIGN.md) as a reference for AI agents to generate UI that follows the {site_name} visual language.",
            "",
            *scope_lines,
            "",
            "## Preview",
            "",
            "Open these files locally:",
            "",
            "- [Light preview](./preview.html)",
            "- [Dark preview](./preview-dark.html)",
            "",
            f"Source: {source_label}",
        ]
    )


def render_preview_html(site_name: str, metrics: dict, mode: str, source_context: dict) -> str:
    theme = build_preview_theme(metrics, mode)
    palette = metrics["palette"]

    hero_title = shorten_text(
        pick_text_sample(metrics, ["h1", "h2"], f"Design System Inspired by {site_name}"),
        72,
    )
    hero_copy = shorten_text(
        pick_text_sample(metrics, ["p"], "A generated design token catalog built from a cloned website snapshot."),
        140,
    )
    primary_action = shorten_text(pick_text_sample(metrics, ["button", "a"], "Primary Action"), 24)
    secondary_samples = metrics["text_samples"].get("a", []) + metrics["text_samples"].get("button", [])
    secondary_action = shorten_text(secondary_samples[1], 24) if len(secondary_samples) > 1 else "Secondary Action"

    color_items: list[tuple[str, str, str]] = []
    if palette.get("background"):
        color_items.append(("Primary Background", palette["background"], "Page canvas"))
    if palette.get("text"):
        color_items.append(("Primary Text", palette["text"], "Default text"))
    if palette.get("surface"):
        color_items.append(("Surface", palette["surface"], "Cards and inner panels"))
    if palette.get("border"):
        color_items.append(("Border", palette["border"], "Dividers and containment"))
    for index, color in enumerate(palette.get("accents", [])[:4], start=1):
        color_items.append((f"Accent {index}", color, "Highlight or CTA"))

    color_cards_html = "\n".join(
        f"""
        <div class="color-card">
          <div class="swatch" style="background:{escape(color)}"></div>
          <div class="swatch-meta">
            <div class="swatch-name">{escape(label)}</div>
            <div class="swatch-value">{escape(color)}</div>
            <div class="swatch-role">{escape(role)}</div>
          </div>
        </div>
        """.strip()
        for label, color, role in color_items
    )

    typography_rows_html = "\n".join(
        f"""
        <div class="type-row">
          <div class="type-sample" style="font-size:{escape(data['size'])};font-weight:{escape(data['weight'] if data['weight'] != '—' else '400')};line-height:{escape(data['line_height'] if data['line_height'] != '—' else '1.3')};letter-spacing:{escape(data['letter_spacing'] if data['letter_spacing'] != '—' else 'normal')};font-family:{escape(data['font'] if data['font'] != '—' else theme['font_primary'])};">
            {escape(ROLE_LABELS[role])}
          </div>
          <div class="type-meta">{escape(data['size'])} / {escape(data['weight'])} / {escape(data['line_height'])} / {escape(data['font'])}</div>
        </div>
        """.strip()
        for role, data in ((role, metrics["typography"][role]) for role in ROLE_ORDER)
    )

    spacing_html = "\n".join(
        f"""
        <div class="meter-item">
          <div class="meter-bar" style="width:{max(24, min(160, int((length_to_px(value) or 0) * 3)))}px;"></div>
          <div class="meter-label">{escape(value)}</div>
        </div>
        """.strip()
        for value in metrics["spacing"][:8]
    ) or '<div class="empty-note">Spacing values were not explicit in the clone.</div>'

    radius_html = "\n".join(
        f"""
        <div class="radius-item">
          <div class="radius-box" style="border-radius:{escape(value)}"></div>
          <div class="meter-label">{escape(value)}</div>
        </div>
        """.strip()
        for value in metrics["radii"][:6]
    ) or '<div class="empty-note">Radius values were not explicit in the clone.</div>'

    shadow_html = "\n".join(
        f"""
        <div class="elevation-card" style="box-shadow:{escape(value)}">
          <div class="elevation-title">Elevation {index}</div>
          <div class="elevation-value">{escape(value)}</div>
        </div>
        """.strip()
        for index, value in enumerate(metrics["shadows"][:4], start=1)
    ) or '<div class="empty-note">No recurring shadow language was extracted.</div>'

    breakpoint_html = "\n".join(
        f'<span class="breakpoint-pill">{escape(value.replace(":", " "))}</span>'
        for value in metrics["breakpoints"][:8]
    ) or '<span class="breakpoint-pill">No explicit media breakpoints detected</span>'

    card_title = shorten_text(pick_text_sample(metrics, ["h3", "h2"], site_name), 28)
    card_copy = shorten_text(
        pick_text_sample(metrics, ["p"], "Representative card content using the extracted colors, radius, and depth."),
        96,
    )
    nav_label = escape(site_name.lower().replace(" ", "-"))
    mode_label = "Dark" if mode == "dark" else "Light"
    source_meta = escape(source_summary_text(source_context))
    secondary_button_border = palette.get("border") or theme["divider"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Design System Preview: {escape(site_name)} ({mode_label})</title>
<style>
  :root {{
    --page-bg: {theme['page_bg']};
    --page-fg: {theme['page_fg']};
    --chrome-bg: {theme['chrome_bg']};
    --panel-bg: {theme['panel_bg']};
    --panel-fg: {theme['panel_fg']};
    --divider: {theme['divider']};
    --muted: {theme['muted']};
    --accent: {theme['accent']};
    --accent-alt: {theme['accent_alt']};
    --button-bg: {theme['button_bg']};
    --button-fg: {theme['button_fg']};
    --button-radius: {theme['button_radius']};
    --button-shadow: {theme['button_shadow']};
    --card-bg: {theme['card_bg']};
    --card-radius: {theme['card_radius']};
    --card-shadow: {theme['card_shadow']};
    --input-bg: {theme['input_bg']};
    --input-radius: {theme['input_radius']};
    --input-border: {theme['input_border']};
    --font-primary: {theme['font_primary']};
    --font-mono: {theme['font_mono']};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--page-bg);
    color: var(--page-fg);
    font-family: var(--font-primary);
    line-height: 1.5;
  }}
  a {{ color: inherit; text-decoration: none; }}
  .nav {{
    position: sticky;
    top: 0;
    z-index: 20;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    padding: 16px 24px;
    background: var(--chrome-bg);
    border-bottom: 1px solid var(--divider);
    backdrop-filter: blur(18px);
  }}
  .nav-brand {{ font-size: 14px; font-weight: 700; letter-spacing: 0.02em; }}
  .nav-links {{ display: flex; gap: 16px; color: var(--muted); font-size: 14px; }}
  .nav-chip {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 38px;
    height: 38px;
    border-radius: 999px;
    background: var(--accent);
    color: {contrast_text_for(theme['accent'])};
    font-weight: 700;
  }}
  .hero {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 72px 24px 40px;
  }}
  .eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid var(--divider);
    color: var(--muted);
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
  .hero h1 {{
    margin: 20px 0 14px;
    font-size: clamp(2.2rem, 5vw, 4.5rem);
    line-height: 1.05;
    letter-spacing: -0.03em;
  }}
  .hero p {{
    max-width: 760px;
    margin: 0 0 24px;
    color: var(--muted);
    font-size: 1rem;
  }}
  .hero-actions {{ display: flex; gap: 12px; flex-wrap: wrap; }}
  .btn-primary {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 18px;
    border-radius: var(--button-radius);
    background: var(--button-bg);
    color: var(--button-fg);
    box-shadow: var(--button-shadow);
    font-weight: 600;
  }}
  .btn-secondary {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 18px;
    border-radius: var(--button-radius);
    border: 1px solid {secondary_button_border};
    color: var(--page-fg);
    background: transparent;
  }}
  .section {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 24px;
  }}
  .section-header {{
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 18px;
  }}
  .section-label {{
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}
  .section-title {{
    font-size: 1.4rem;
    margin: 4px 0 0;
  }}
  .divider {{
    max-width: 1100px;
    margin: 0 auto;
    border: 0;
    border-top: 1px solid var(--divider);
  }}
  .color-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
  }}
  .color-card, .panel {{
    background: var(--panel-bg);
    color: var(--panel-fg);
    border-radius: 18px;
    border: 1px solid var(--divider);
    overflow: hidden;
  }}
  .swatch {{ height: 88px; }}
  .swatch-meta {{ padding: 12px; }}
  .swatch-name {{ font-weight: 700; }}
  .swatch-value {{
    margin-top: 4px;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 12px;
  }}
  .swatch-role {{ margin-top: 4px; color: var(--muted); font-size: 12px; }}
  .type-list {{ display: grid; gap: 12px; }}
  .type-row {{
    padding: 16px;
    border-radius: 18px;
    background: var(--panel-bg);
    color: var(--panel-fg);
    border: 1px solid var(--divider);
  }}
  .type-meta {{
    margin-top: 8px;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 12px;
  }}
  .component-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }}
  .panel {{ padding: 18px; }}
  .panel h3 {{ margin: 0 0 12px; }}
  .button-stack, .breakpoints {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .mini-card {{
    background: var(--card-bg);
    color: {contrast_text_for(theme['card_bg'], dark='#0f172a', light='#f8fafc')};
    border-radius: var(--card-radius);
    box-shadow: var(--card-shadow);
    overflow: hidden;
  }}
  .mini-card-visual {{
    height: 140px;
    background: linear-gradient(135deg, var(--accent), var(--accent-alt));
    opacity: 0.9;
  }}
  .mini-card-body {{ padding: 16px; }}
  .mini-card p {{ color: var(--muted); }}
  .input {{
    width: 100%;
    padding: 12px 14px;
    border-radius: var(--input-radius);
    border: 1px solid var(--divider);
    background: var(--input-bg);
    color: {contrast_text_for(theme['input_bg'], dark='#0f172a', light='#f8fafc')};
    font: inherit;
  }}
  .meter-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
  }}
  .meter-item, .radius-item, .elevation-card {{
    padding: 16px;
    border-radius: 18px;
    background: var(--panel-bg);
    color: var(--panel-fg);
    border: 1px solid var(--divider);
  }}
  .meter-bar {{
    height: 18px;
    border-radius: 999px;
    background: var(--accent);
    margin-bottom: 10px;
  }}
  .meter-label {{
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 12px;
  }}
  .radius-grid, .elevation-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
  }}
  .radius-box {{
    width: 72px;
    height: 72px;
    background: linear-gradient(135deg, var(--accent), var(--accent-alt));
    margin-bottom: 10px;
  }}
  .elevation-title {{ font-weight: 700; margin-bottom: 8px; }}
  .elevation-value {{
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 11px;
    word-break: break-word;
  }}
  .breakpoint-pill {{
    display: inline-flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 999px;
    background: var(--panel-bg);
    border: 1px solid var(--divider);
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 12px;
  }}
  .footer {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 24px;
    color: var(--muted);
    font-size: 12px;
  }}
  .empty-note {{
    color: var(--muted);
    font-size: 13px;
  }}
  @media (max-width: 768px) {{
    .nav-links {{ display: none; }}
    .hero {{ padding-top: 48px; }}
    .section {{ padding: 20px 16px; }}
  }}
</style>
</head>
<body>
  <nav class="nav">
    <div class="nav-brand">{nav_label}</div>
    <div class="nav-links">
      <a href="#colors">Colors</a>
      <a href="#type">Type</a>
      <a href="#components">Components</a>
      <a href="#layout">Layout</a>
    </div>
    <a class="nav-chip" href="#hero">{escape(mode_label[0])}</a>
  </nav>

  <section class="hero" id="hero">
    <div class="eyebrow">Generated {mode_label} Preview</div>
    <h1>{escape(hero_title)}</h1>
    <p>{escape(hero_copy)}</p>
    <div class="hero-actions">
      <a class="btn-primary" href="#components">{escape(primary_action)}</a>
      <a class="btn-secondary" href="./DESIGN.md">{escape(secondary_action)}</a>
    </div>
  </section>

  <hr class="divider">

  <section class="section" id="colors">
    <div class="section-header">
      <div>
        <div class="section-label">01 / Colors</div>
        <h2 class="section-title">Extracted Color Roles</h2>
      </div>
      <div class="meter-label">{escape(source_meta)}</div>
    </div>
    <div class="color-grid">
      {color_cards_html}
    </div>
  </section>

  <hr class="divider">

  <section class="section" id="type">
    <div class="section-header">
      <div>
        <div class="section-label">02 / Typography</div>
        <h2 class="section-title">Hierarchy Samples</h2>
      </div>
    </div>
    <div class="type-list">
      {typography_rows_html}
    </div>
  </section>

  <hr class="divider">

  <section class="section" id="components">
    <div class="section-header">
      <div>
        <div class="section-label">03 / Components</div>
        <h2 class="section-title">Reusable UI Patterns</h2>
      </div>
    </div>
    <div class="component-grid">
      <div class="panel">
        <h3>Buttons</h3>
        <div class="button-stack">
          <a class="btn-primary" href="#">{escape(primary_action)}</a>
          <a class="btn-secondary" href="#">{escape(secondary_action)}</a>
          <a class="nav-chip" href="#">&rarr;</a>
        </div>
      </div>
      <div class="panel">
        <h3>Card</h3>
        <div class="mini-card">
          <div class="mini-card-visual"></div>
          <div class="mini-card-body">
            <strong>{escape(card_title)}</strong>
            <p>{escape(card_copy)}</p>
          </div>
        </div>
      </div>
      <div class="panel">
        <h3>Form Surface</h3>
        <input class="input" value="{escape(primary_action)}" aria-label="Input sample">
      </div>
    </div>
  </section>

  <hr class="divider">

  <section class="section" id="layout">
    <div class="section-header">
      <div>
        <div class="section-label">04 / Layout</div>
        <h2 class="section-title">Spacing, Radius, and Elevation</h2>
      </div>
    </div>
    <div class="component-grid">
      <div class="panel">
        <h3>Spacing Scale</h3>
        <div class="meter-grid">{spacing_html}</div>
      </div>
      <div class="panel">
        <h3>Radius Scale</h3>
        <div class="radius-grid">{radius_html}</div>
      </div>
    </div>
    <div style="height:16px"></div>
    <div class="panel">
      <h3>Elevation</h3>
      <div class="elevation-grid">{shadow_html}</div>
    </div>
    <div style="height:16px"></div>
    <div class="panel">
      <h3>Responsive Clues</h3>
      <div class="breakpoints">{breakpoint_html}</div>
    </div>
  </section>

  <footer class="footer">
    Preview generated from {escape(source_summary_text(source_context))}. Open <a href="./DESIGN.md">DESIGN.md</a> for the full written system.
  </footer>
</body>
</html>
"""


def serialize_counter(counter: Counter[str], limit: int = 20, numeric: bool = False) -> list[dict[str, object]]:
    return [{"value": value, "count": count} for value, count in sort_counter_items(counter, limit=limit, numeric=numeric)]


def build_evidence_payload(site_name: str, source_context: dict, metrics: dict) -> dict:
    return {
        "site_name": site_name,
        "source_url": source_context.get("url"),
        "source_html": metrics["html_path"],
        "source_html_files": source_context["input_paths"],
        "source_labels": source_context["labels"],
        "source_count": source_context["count"],
        "capture_dir": source_context.get("capture_dir"),
        "html_title": metrics["html_title"],
        "palette": metrics["palette"],
        "fonts": metrics["fonts"],
        "top_colors": serialize_counter(metrics["all_colors"], limit=20),
        "font_sizes": serialize_counter(metrics["declaration_values"]["font-size"], limit=12, numeric=True),
        "font_weights": serialize_counter(metrics["declaration_values"]["font-weight"], limit=12),
        "line_heights": serialize_counter(metrics["declaration_values"]["line-height"], limit=12),
        "letter_spacings": serialize_counter(metrics["declaration_values"]["letter-spacing"], limit=12),
        "radii": metrics["radii"],
        "shadows": metrics["shadows"],
        "spacing": metrics["spacing"],
        "max_widths": metrics["max_widths"],
        "breakpoints": metrics["breakpoints"],
        "custom_properties": serialize_counter(metrics["custom_properties"], limit=20),
        "tag_counts": metrics["tag_counts"],
        "text_samples": metrics["text_samples"],
        "typography": metrics["typography"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate DESIGN.md from a cloned self-contained HTML file."
    )
    parser.add_argument("input_html", nargs="*", help="Path(s) to cloned HTML files, or a directory containing clone.html files")
    parser.add_argument("--capture-dir", help="Capture directory to scan recursively for clone.html files")
    parser.add_argument("--name", help="Override site name")
    parser.add_argument("--url", help="Original source URL")
    parser.add_argument("--out", help="Write DESIGN.md to this path")
    parser.add_argument("--out-dir", help="Write the full output bundle to this directory")
    parser.add_argument("--json-out", help="Write evidence JSON to this path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input_html and not args.capture_dir:
        print("Provide at least one HTML input path or --capture-dir.", file=sys.stderr)
        return 1
    input_paths = resolve_input_paths(args.input_html, args.capture_dir)
    if not input_paths:
        print("No input HTML files were found.", file=sys.stderr)
        return 1
    missing = [path for path in input_paths if not path.exists()]
    if missing:
        print(f"Input HTML not found: {missing[0]}", file=sys.stderr)
        return 1

    html_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in input_paths)
    metrics = collect_metrics(html_text, input_paths[0])
    inferred_name = infer_site_name_from_paths(input_paths)
    site_name = extract_site_name(args.name or inferred_name, metrics["html_title"], input_paths[0], args.url)
    site_slug = normalize_slug(site_name)
    source_context = build_source_context(input_paths, args.url, args.capture_dir)
    design_md = render_design_md(site_name, metrics, source_context)
    readme_md = render_readme(site_name, source_context)
    preview_light = render_preview_html(site_name, metrics, "light", source_context)
    preview_dark = render_preview_html(site_name, metrics, "dark", source_context)
    evidence = build_evidence_payload(site_name, source_context, metrics)

    if args.out:
        design_path = Path(args.out).expanduser().resolve()
        output_dir = design_path.parent
    elif args.out_dir:
        output_dir = Path(args.out_dir).expanduser().resolve()
        design_path = output_dir / "DESIGN.md"
    else:
        output_dir = (Path.cwd() / "design-md" / site_slug).resolve()
        design_path = output_dir / "DESIGN.md"

    output_dir.mkdir(parents=True, exist_ok=True)
    design_path.write_text(design_md, encoding="utf-8")
    (output_dir / "README.md").write_text(readme_md, encoding="utf-8")
    (output_dir / "preview.html").write_text(preview_light, encoding="utf-8")
    (output_dir / "preview-dark.html").write_text(preview_dark, encoding="utf-8")

    if args.json_out:
        json_path = Path(args.json_out).expanduser().resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")

    print(str(output_dir))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
