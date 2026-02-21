from __future__ import annotations

from typing import List, Any, Tuple
from .utils import normalize_text


def _row_non_empty_cells(row: List[Any]) -> List[Any]:
    out = []
    for v in row:
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        out.append(v)
    return out


def detect_header_row(rows: List[List[Any]], max_scan: int = 30) -> Tuple[int, List[str], List[str]]:
    """Return (header_row_index_0_based, headers, warnings)."""
    warnings: List[str] = []
    scan = rows[:max_scan] if rows else []
    best_idx = -1
    best_score = -1.0
    best_headers: List[str] = []

    for i, row in enumerate(scan[:10]):
        non_empty = _row_non_empty_cells(row)
        if len(non_empty) == 1 and isinstance(non_empty[0], str) and len(non_empty[0].strip()) >= 6:
            warnings.append(f"Row {i+1} appears to be a title row, skipped")

    for i, row in enumerate(scan):
        non_empty = _row_non_empty_cells(row)
        if len(non_empty) < 2:
            continue

        stringish = sum(1 for v in non_empty if isinstance(v, str))
        string_ratio = stringish / max(1, len(non_empty))

        if string_ratio < 0.55:
            continue

        normalized = [normalize_text(v) for v in non_empty]
        uniq_ratio = len(set(normalized)) / max(1, len(normalized))

        shortish = sum(1 for v in non_empty if isinstance(v, str) and 1 <= len(v.strip()) <= 40)
        short_ratio = shortish / max(1, len(non_empty))

        score = (len(non_empty) * 2.0) + (string_ratio * 5.0) + (uniq_ratio * 3.0) + (short_ratio * 2.0)

        if score > best_score:
            best_score = score
            best_idx = i
            best_headers = ["" if v is None else str(v).strip() for v in row]

    if best_idx == -1:
        raise ValueError("Could not detect a header row (no sufficiently header-like row found).")

    headers = []
    for h in best_headers:
        headers.append(h if h is not None else "")

    return best_idx, headers, warnings

