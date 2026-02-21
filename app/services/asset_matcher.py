from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from .utils import normalize_text


def build_asset_aliases(assets: List[Dict]) -> Dict[str, str]:
    """Return alias -> asset_name"""
    alias_map: Dict[str, str] = {}

    def add(alias: str, name: str):
        a = normalize_text(alias)
        if not a:
            return
        if a in alias_map:
            return
        alias_map[a] = name

    for a in assets:
        name = a["name"]
        display = a.get("display_name", "")
        add(name, name)
        add(name.replace("-", ""), name)
        add(name.replace("-", " "), name)
        if display:
            add(display, name)
            add(display.replace("-", " "), name)

        if name.startswith("TG-"):
            n = name.split("-")[1]
            add(f"tg{n}", name)
            add(f"tg {n}", name)
            add(f"t g {n}", name)
        if name.startswith("AFBC-"):
            n = name.split("-")[1]
            add(f"afbc{n}", name)
            add(f"afbc {n}", name)
            add(f"afbc boiler {n}", name)
        if name.startswith("KILN-"):
            n = name.split("-")[1]
            add(f"kiln{n}", name)
            add(f"kiln {n}", name)

    return alias_map


def extract_asset_from_header(original_header: str, alias_map: Dict[str, str]) -> Tuple[Optional[str], str]:
    """Return (asset_name, header_without_asset)."""
    norm = normalize_text(original_header)

    aliases = sorted(alias_map.keys(), key=len, reverse=True)
    for alias in aliases:
        if not alias:
            continue
        if alias in norm:
            asset = alias_map[alias]
            return asset, original_header

    return None, original_header

