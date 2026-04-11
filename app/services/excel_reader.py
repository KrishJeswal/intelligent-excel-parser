from __future__ import annotations

from io import BytesIO
from typing import Any, List, Tuple

import openpyxl


def read_first_sheet(file_bytes: bytes) -> Tuple[str, List[List[Any]]]:
    wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True, read_only=True)

    if not wb.worksheets:
        raise ValueError("Workbook contains no sheets.")

    ws = wb.worksheets[0]
    rows: List[List[Any]] = []
    max_cols = 0

    for row in ws.iter_rows(values_only=True):
        row_list = list(row)
        if len(row_list) > max_cols:
            max_cols = len(row_list)
        rows.append(row_list)

    for r in rows:
        gap = max_cols - len(r)
        if gap > 0:
            r.extend([None] * gap)

    wb.close()
    return ws.title, rows