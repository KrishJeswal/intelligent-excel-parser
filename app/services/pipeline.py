from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import json
import os

from app.models.schemas import ColumnInput, ColumnMapping, ParsedCell, ParseResponse, UnmappedColumn
from .excel_reader import read_first_sheet
from .header_detector import detect_header_row
from .utils import normalize_text, extract_unit_hint
from .asset_matcher import build_asset_aliases, extract_asset_from_header
from .llm_mapper import map_columns_with_gemini
from .value_parser import parse_value


def _load_registry(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_excel(file_bytes: bytes) -> ParseResponse:
    try:
        sheet_name, rows = read_first_sheet(file_bytes)
        if not rows:
            return ParseResponse(status="error", warnings=["Workbook appears to be empty."])

        assets = _load_registry(os.path.join(os.path.dirname(__file__), "..", "registries", "assets.json"))
        params = _load_registry(os.path.join(os.path.dirname(__file__), "..", "registries", "parameters.json"))

        alias_map = build_asset_aliases(assets)

        header_idx, headers, warnings = detect_header_row(rows)
        header_row_excel = header_idx + 1

        columns: List[ColumnInput] = []
        for col_idx, header in enumerate(headers):
            header_str = "" if header is None else str(header)
            norm = normalize_text(header_str)
            unit_hint = extract_unit_hint(norm)
            asset_hint, _ = extract_asset_from_header(header_str, alias_map)
            columns.append(ColumnInput(
                column_index=col_idx,
                original_header=header_str,
                normalized_header=norm,
                unit_hint=unit_hint,
                asset_hint=asset_hint
            ))

        mappings, llm_warnings = map_columns_with_gemini(columns, params, assets)
        warnings.extend(llm_warnings)

        param_set = {p["name"] for p in params}
        asset_set = {a["name"] for a in assets}

        mapping_by_col: Dict[int, ColumnMapping] = {}
        for m in mappings:
            if m.param_name is not None and m.param_name not in param_set:
                warnings.append(f"Column {m.column_index}: invalid param_name '{m.param_name}' not in registry; treating as unmapped.")
                m.param_name = None
                m.confidence = "low"
            if m.asset_name is not None and m.asset_name not in asset_set:
                cleaned = m.asset_name.replace(" ", "")
                if cleaned in asset_set:
                    m.asset_name = cleaned
                else:
                    warnings.append(f"Column {m.column_index}: invalid asset_name '{m.asset_name}' not in registry; set to null.")
                    m.asset_name = None
            if m.asset_name is None:
                hint = next((c.asset_hint for c in columns if c.column_index == m.column_index), None)
                if hint in asset_set:
                    m.asset_name = hint

            mapping_by_col[m.column_index] = m

        unmapped: List[UnmappedColumn] = []
        for c in columns:
            m = mapping_by_col.get(c.column_index)
            if not m or not m.param_name:
                unmapped.append(UnmappedColumn(
                    col=c.column_index,
                    header=c.original_header,
                    reason=(m.reason if m else "No mapping returned")
                ))

        parsed_cells: List[ParsedCell] = []
        for r_idx in range(header_idx + 1, len(rows)):
            row = rows[r_idx]
            if all(v is None or (isinstance(v, str) and v.strip() == "") for v in row):
                continue

            for c in columns:
                m = mapping_by_col.get(c.column_index)
                if not m or not m.param_name:
                    continue

                raw_val = row[c.column_index] if c.column_index < len(row) else None
                parsed_val = parse_value(raw_val)

                conf = m.confidence
                if parsed_val is None and raw_val not in (None, "", " ", "N/A", "NA"):
                    if conf == "high":
                        conf = "medium"

                parsed_cells.append(ParsedCell(
                    row=r_idx + 1,  
                    col=c.column_index,
                    param_name=m.param_name,
                    asset_name=m.asset_name,
                    raw_value=raw_val,
                    parsed_value=parsed_val,
                    confidence=conf
                ))

        return ParseResponse(
            status="success",
            header_row=header_row_excel,
            parsed_data=parsed_cells,
            unmapped_columns=unmapped,
            warnings=warnings,
            meta={"sheet": sheet_name, "rows": len(rows), "cols": len(headers)}
        )

    except Exception as e:
        return ParseResponse(status="error", warnings=[str(e)])

