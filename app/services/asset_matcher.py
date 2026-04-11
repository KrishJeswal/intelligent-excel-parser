from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .utils import normalize_text


def build_asset_aliases(assets: List[Dict]) -> Dict[str, str]:
    alias_map: Dict[str, str] = {}

    def add(alias: str, canonical: str) -> None:
        key = normalize_text(alias)
        if key and key not in alias_map:
            alias_map[key] = canonical

    for asset in assets:
        name: str = asset["name"]
        display: str = asset.get("display_name", "")

        add(name, name)
        add(name.replace("-", ""), name)
        add(name.replace("-", " "), name)

        if display:
            add(display, name)
            add(display.replace("-", " "), name)

        parts = name.split("-", 1)
        if len(parts) == 2:
            prefix, suffix = parts[0].lower(), parts[1]
            add(f"{prefix}{suffix}", name)
            add(f"{prefix} {suffix}", name)

            if prefix == "tg":
                add(f"t g {suffix}", name)
            elif prefix == "afbc":
                add(f"afbc boiler {suffix}", name)

    return alias_map


def extract_asset_from_header(
    original_header: str, alias_map: Dict[str, str]
) -> Tuple[Optional[str], str]:
    norm = normalize_text(original_header)

    for alias in sorted(alias_map, key=len, reverse=True):
        if alias and alias in norm:
            return alias_map[alias], original_header

    return None, original_header