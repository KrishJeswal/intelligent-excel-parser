from __future__ import annotations

import re
from typing import Any, Optional


_NA_VALUES = frozenset({"n/a", "na", "null", "none", "-", "--", ""})

_PERCENT_RE = re.compile(r"^\s*\$?\s*([-+]?[0-9][0-9,]*\.?[0-9]*)\s*\$?\s*%\s*$")
_NUMBER_RE = re.compile(r"^\s*([-+]?[0-9][0-9,]*\.?[0-9]*)\s*$")
_PAREN_NUMBER_RE = re.compile(r"^\s*\(\s*([-+]?[0-9][0-9,]*\.?[0-9]*)\s*\)\s*$")


def parse_value(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, bool):
        return 1.0 if value else 0.0

    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (ValueError, OverflowError):
            return None

    s = str(value).strip()
    if s.lower() in _NA_VALUES:
        return None

    sl = s.lower()
    if sl in {"yes", "y", "true", "t"}:
        return 1.0
    if sl in {"no", "n", "false", "f"}:
        return 0.0

    m = _PERCENT_RE.match(s)
    if m:
        num = m.group(1).replace(",", "")
        try:
            val = float(num) / 100.0
            return -val if s.lstrip().startswith("(") else val
        except (ValueError, OverflowError):
            return None

    m = _PAREN_NUMBER_RE.match(s)
    if m:
        num = m.group(1).replace(",", "")
        try:
            return -float(num)
        except (ValueError, OverflowError):
            return None

    m = _NUMBER_RE.match(s)
    if m:
        num = m.group(1).replace(",", "")
        try:
            return float(num)
        except (ValueError, OverflowError):
            return None

    try:
        return float(s.replace(",", ""))
    except (ValueError, OverflowError):
        return None