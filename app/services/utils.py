from __future__ import annotations

import re
from typing import Optional


_whitespace_re = re.compile(r"\s+")
_non_alnum_re = re.compile(r"[^a-z0-9%/]+")


def normalize_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    s = str(value).strip().lower()
    s = s.replace("co₂", "co2").replace("so₂", "so2")
    s = s.replace("–", "-").replace("—", "-")
    s = _non_alnum_re.sub(" ", s)
    s = _whitespace_re.sub(" ", s).strip()
    return s


def extract_unit_hint(normalized_header: str) -> Optional[str]:
    tokens = normalized_header.split()
    unit_tokens = {"mt", "mwh", "kl", "kg", "%", "t/hr", "kcal/kg", "kcal/kwh", "kg/kwh"}
    for t in tokens:
        if t in unit_tokens:
            return t
    if "kcal kg" in normalized_header:
        return "kcal/kg"
    if "kg kwh" in normalized_header:
        return "kg/kWh"
    if "kcal kwh" in normalized_header:
        return "kcal/kWh"
    if "t hr" in normalized_header:
        return "T/hr"
    return None

