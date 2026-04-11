from __future__ import annotations

import re
from typing import Optional


_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9%/]+")

_ENCODING_FIXES = {
    "co\u00e2\u0082\u0082": "co2",
    "so\u00e2\u0082\u0082": "so2",
    "\u00e2\u0080\x93": "-",
    "\u00e2\u0080\x94": "-",
    "co₂": "co2",
    "so₂": "so2",
    "\u2013": "-",
    "\u2014": "-",
}


def normalize_text(value: Optional[str]) -> str:
    if value is None:
        return ""

    s = str(value).strip().lower()

    for bad, good in _ENCODING_FIXES.items():
        s = s.replace(bad, good)

    s = _NON_ALNUM_RE.sub(" ", s)
    s = _WHITESPACE_RE.sub(" ", s).strip()

    return s


def extract_unit_hint(normalized_header: str) -> Optional[str]:
    tokens = normalized_header.split()
    _UNIT_TOKENS = {"mt", "mwh", "kwh", "kl", "kg", "%", "t/hr", "kcal/kg", "kcal/kwh", "kg/kwh"}

    for t in tokens:
        if t in _UNIT_TOKENS:
            return t

    if "kcal kg" in normalized_header:
        return "kcal/kg"
    if "kg kwh" in normalized_header:
        return "kg/kwh"
    if "kcal kwh" in normalized_header:
        return "kcal/kwh"
    if "t hr" in normalized_header:
        return "t/hr"

    return None