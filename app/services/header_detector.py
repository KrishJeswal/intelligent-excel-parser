from __future__ import annotations

from typing import Any, List, Tuple

from .utils import normalize_text


def _non_empty(row: List[Any]) -> List[Any]:
    return [
        v for v in row
        if v is not None and not (isinstance(v, str) and v.strip() == "")
    ]


def _is_title_row(row: List[Any]) -> bool:
    ne = _non_empty(row)
    return (
        len(ne) == 1
        and isinstance(ne[0], str)
        and len(ne[0].strip()) >= 6
    )


def detect_header_row(rows: List[List[Any]], max_scan: int = 30) -> Tuple[int, List[str], List[str]]:
    warnings: List[str] = []
    scan = rows[:max_scan]

    title_rows = set()
    for i, row in enumerate(scan[:10]):
        if _is_title_row(row):
            warnings.append(f"Row {i + 1} appears to be a title row, skipped.")
            title_rows.add(i)

    best_idx = -1
    best_score = -1.0
    best_headers: List[str] = []

    for i, row in enumerate(scan):
        if i in title_rows:
            continue

        ne = _non_empty(row)
        if len(ne) < 2:
            continue

        string_count = sum(1 for v in ne if isinstance(v, str))
        string_ratio = string_count / len(ne)

        if string_ratio < 0.55:
            continue

        normalized = [normalize_text(str(v)) for v in ne]
        uniq_ratio = len(set(normalized)) / len(normalized)

        short_count = sum(1 for v in ne if isinstance(v, str) and 1 <= len(v.strip()) <= 40)
        short_ratio = short_count / len(ne)

        score = (
            len(ne) * 2.0
            + string_ratio * 5.0
            + uniq_ratio * 3.0
            + short_ratio * 2.0
        )

        if score > best_score:
            best_score = score
            best_idx = i
            best_headers = ["" if v is None else str(v).strip() for v in row]

    if best_idx == -1:
        raise ValueError("Could not detect a header row.")

    return best_idx, best_headers, warnings