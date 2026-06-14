#!/usr/bin/env python3
"""Extract visible text and image slots from a cloned landing-page HTML file."""

from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}
TEXT_TAG_ROLES = {
    "h1": "hero-or-page-heading",
    "h2": "section-heading",
    "h3": "card-or-subsection-heading",
    "h4": "small-heading",
    "p": "body-copy",
    "a": "link-or-cta",
    "button": "button-or-cta",
    "li": "list-item",
    "span": "inline-label",
    "strong": "emphasis",
}
IMAGE_ATTRS = ("src", "data-src", "data-lazy-src", "poster")


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def class_summary(value: str | None) -> str:
    if not value:
        return ""
    classes = [part for part in re.split(r"\s+", value.strip()) if part]
    return "." + ".".join(classes[:3]) if classes else ""


def compact_url(value: str) -> str:
    if value.startswith("data:"):
        header = value.split(",", 1)[0]
        return f"{header},<embedded {len(value)} chars>"
    return value


class LandingInventoryParser(HTMLParser):
    def __init__(self, base_url: str | None = None):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.stack: list[dict] = []
        self.text_entries: list[dict] = []
        self.image_entries: list[dict] = []
        self._tag_counts: dict[str, int] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value for name, value in attrs}
        self._tag_counts[tag] = self._tag_counts.get(tag, 0) + 1
        node = {
            "tag": tag,
            "attrs": attr_map,
            "index": self._tag_counts[tag],
            "text": [],
        }
        self.stack.append(node)

        if tag in {"img", "source", "video"}:
            self._record_image(tag, attr_map)

    def handle_endtag(self, tag: str) -> None:
        while self.stack:
            node = self.stack.pop()
            self._flush_text_node(node)
            if node["tag"] == tag:
                break

    def handle_data(self, data: str) -> None:
        if not self.stack:
            return
        if any(node["tag"] in SKIP_TEXT_TAGS for node in self.stack):
            return
        text = clean_text(data)
        if text:
            self.stack[-1]["text"].append(text)

    def close(self) -> None:
        super().close()
        while self.stack:
            self._flush_text_node(self.stack.pop())

    def _path_for_current_stack(self, leaf: dict | None = None) -> str:
        nodes = self.stack[-5:]
        if leaf is not None and (not nodes or nodes[-1] is not leaf):
            nodes = (self.stack + [leaf])[-5:]
        parts = []
        for node in nodes:
            attrs = node["attrs"]
            tag = node["tag"]
            if attrs.get("id"):
                parts.append(f"{tag}#{attrs['id']}")
            else:
                parts.append(f"{tag}{class_summary(attrs.get('class'))}")
        return " > ".join(part for part in parts if part)

    def _flush_text_node(self, node: dict) -> None:
        if node["tag"] in SKIP_TEXT_TAGS:
            return
        text = clean_text(" ".join(node["text"]))
        if len(text) < 2:
            return
        if len(text) > 500:
            text = text[:497].rstrip() + "..."
        attrs = node["attrs"]
        self.text_entries.append(
            {
                "selector_hint": self._path_for_current_stack(node),
                "tag": node["tag"],
                "role": TEXT_TAG_ROLES.get(node["tag"], "visible-text"),
                "text": text,
                "length": len(text),
                "id": attrs.get("id"),
                "class": attrs.get("class"),
            }
        )

    def _record_image(self, tag: str, attrs: dict[str, str | None]) -> None:
        candidates = []
        for attr in IMAGE_ATTRS:
            value = attrs.get(attr)
            if value:
                candidates.append({"attr": attr, "value": value})
        srcset = attrs.get("srcset")
        if srcset:
            candidates.append({"attr": "srcset", "value": srcset.split(",")[0].strip().split(" ")[0]})
        if not candidates:
            return
        primary = candidates[0]
        raw_url = primary["value"]
        resolved = urljoin(self.base_url, raw_url) if self.base_url else raw_url
        self.image_entries.append(
            {
                "selector_hint": self._path_for_current_stack(),
                "tag": tag,
                "source_attr": primary["attr"],
                "src": compact_url(raw_url),
                "resolved_src": compact_url(resolved),
                "is_data_uri": raw_url.startswith("data:"),
                "alt": attrs.get("alt"),
                "width": attrs.get("width"),
                "height": attrs.get("height"),
                "class": attrs.get("class"),
                "role_guess": guess_image_role(attrs, raw_url),
            }
        )


def guess_image_role(attrs: dict[str, str | None], src: str) -> str:
    haystack = " ".join(
        value or ""
        for value in [
            attrs.get("alt"),
            attrs.get("class"),
            attrs.get("id"),
            src,
        ]
    ).lower()
    if any(word in haystack for word in ["hero", "banner", "cover"]):
        return "hero-visual"
    if any(word in haystack for word in ["logo", "brand"]):
        return "logo-or-brand-mark"
    if any(word in haystack for word in ["avatar", "user", "testimonial"]):
        return "avatar-or-testimonial"
    if any(word in haystack for word in ["screenshot", "screen", "mockup", "product"]):
        return "product-visual"
    if any(word in haystack for word in ["icon"]):
        return "icon"
    return "raster-image"


def unique_text_entries(entries: list[dict], limit: int) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    result = []
    priority = {"h1": 0, "h2": 1, "h3": 2, "button": 3, "a": 4, "p": 5}
    for entry in sorted(entries, key=lambda item: (priority.get(item["tag"], 9), item["length"])):
        key = (entry["tag"], entry["text"])
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
        if len(result) >= limit:
            break
    return result


def unique_image_entries(entries: list[dict], limit: int) -> list[dict]:
    seen: set[str] = set()
    result = []
    for entry in entries:
        key = entry["resolved_src"]
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
        if len(result) >= limit:
            break
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract landing page copy and image inventory from clone.html")
    parser.add_argument("html", help="Path to clone.html or another HTML file")
    parser.add_argument("--base-url", help="Resolve relative image URLs against this URL")
    parser.add_argument("--out", help="Write inventory JSON to this path")
    parser.add_argument("--max-text", type=int, default=160, help="Maximum text entries to keep")
    parser.add_argument("--max-images", type=int, default=120, help="Maximum image entries to keep")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    html_path = Path(args.html)
    html_text = html_path.read_text(encoding="utf-8", errors="replace")
    extractor = LandingInventoryParser(base_url=args.base_url)
    extractor.feed(html_text)
    extractor.close()

    payload = {
        "source_html": str(html_path),
        "base_url": args.base_url,
        "text": unique_text_entries(extractor.text_entries, args.max_text),
        "images": unique_image_entries(extractor.image_entries, args.max_images),
    }

    encoded = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
