from __future__ import annotations

from io import BytesIO
from typing import List, Any, Tuple
import openpyxl


def read_first_sheet(file_bytes: bytes) -> Tuple[str, List[List[Any]]]:
    wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows: List[List[Any]] = []
    max_cols = 0
    for row in ws.iter_rows(values_only=True):
        row_list = list(row)
        max_cols = max(max_cols, len(row_list))
        rows.append(row_list)
    for r in rows:
        if len(r) < max_cols:
            r.extend([None] * (max_cols - len(r)))
    return ws.title, rows

