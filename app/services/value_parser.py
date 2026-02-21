from __future__ import annotations

from typing import Any, Optional
import re


_na = {"n/a", "na", "null", "none", "-", "--", ""}

_percent_re = re.compile(r"^\s*\(?\s*([-+]?[0-9][0-9,]*\.?[0-9]*)\s*\)?\s*%\s*$")
_number_re = re.compile(r"^\s*\(?\s*([-+]?[0-9][0-9,]*\.?[0-9]*)\s*\)?\s*$")


def parse_value(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return None

    s = str(value).strip()
    if s.lower() in _na:
        return None

    sl = s.strip().lower()
    if sl in {"yes", "y", "true", "t"}:
        return 1.0
    if sl in {"no", "n", "false", "f"}:
        return 0.0

    # Percent values can appear as "45%", "(45)%", or "(45%)".
    st = s.strip()
    if st.startswith("(") and st.endswith(")") and "%" in st:
        inner = st[1:-1].strip()
        m_inner = _percent_re.match(inner)
        if m_inner:
            num = m_inner.group(1).replace(",", "")
            try:
                return -float(num) / 100.0
            except Exception:
                return None

    m = _percent_re.match(s)
    if m:
        num = m.group(1).replace(",", "")
        try:
            val = float(num) / 100.0
            if s.strip().startswith("(") and s.strip().endswith(")"):
                val = -val
            return val
        except Exception:
            return None

    m = _number_re.match(s)
    if m:
        num = m.group(1).replace(",", "")
        try:
            val = float(num)
            if s.strip().startswith("(") and s.strip().endswith(")"):
                val = -val
            return val
        except Exception:
            return None

    try:
        return float(s.replace(",", ""))
    except Exception:
        return None

