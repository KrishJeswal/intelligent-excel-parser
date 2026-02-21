from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple
from difflib import SequenceMatcher

from google import genai
from pydantic import ValidationError

from app.models.schemas import ColumnInput, ColumnMapping, LLMMappingResponse
from .utils import normalize_text


SYSTEM_PROMPT = """You map messy Excel column headers to canonical IDs from the provided registries.

Rules:
- param_name MUST be one of parameter_registry[*].name, or null.
- asset_name MUST be one of asset_registry[*].name, or null.
- Do NOT invent new parameters/assets.
- If unsure or ambiguous, set param_name to null and confidence to low.
- Return ONLY valid JSON matching the output_schema. No prose, no markdown.
"""


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM did not return a JSON object.")
    return text[start : end + 1]


def _fallback_map(columns: List[ColumnInput], parameters: List[Dict]) -> List[ColumnMapping]:
    param_candidates = []
    for p in parameters:
        name = p["name"]
        disp = p.get("display_name", "")
        unit = p.get("unit", "")
        blob = normalize_text(f"{name} {disp} {unit}")
        param_candidates.append((name, blob))

    def sim(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    out: List[ColumnMapping] = []
    for c in columns:
        h = normalize_text(c.normalized_header)
        best_name = None
        best_score = 0.0
        for name, blob in param_candidates:
            score = sim(h, blob)
            if score > best_score:
                best_score = score
                best_name = name

        if best_score >= 0.75:
            conf = "high"
        elif best_score >= 0.62:
            conf = "medium"
        else:
            conf = "low"
            best_name = None

        out.append(
            ColumnMapping(
                column_index=c.column_index,
                param_name=best_name,
                asset_name=c.asset_hint,
                confidence=conf,
                reason=f"fallback similarity={best_score:.2f}",
            )
        )
    return out


def map_columns_with_gemini(
    columns: List[ColumnInput],
    parameters: List[Dict],
    assets: List[Dict],
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.0,
) -> Tuple[List[ColumnMapping], List[str]]:
    warnings: List[str] = []

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        warnings.append("GEMINI_API_KEY not set; used deterministic fallback header mapper.")
        return _fallback_map(columns, parameters), warnings

    client = genai.Client()

    payload = {
        "task": "map_headers",
        "asset_registry": [{"name": a["name"], "display_name": a.get("display_name", "")} for a in assets],
        "parameter_registry": [{"name": p["name"], "display_name": p.get("display_name", ""), "unit": p.get("unit", "")} for p in parameters],
        "columns": [c.model_dump() for c in columns],
        "output_schema": {
            "mappings": [
                {"column_index": "int", "param_name": "string|null", "asset_name": "string|null", "confidence": "high|medium|low", "reason": "string"}
            ]
        },
    }

    prompt = SYSTEM_PROMPT + "\n\nUSER_PAYLOAD_JSON:\n" + json.dumps(payload, ensure_ascii=False)

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    )

    raw_text = (resp.text or "").strip()  
    json_str = _extract_json(raw_text)
    data = json.loads(json_str)

    try:
        parsed = LLMMappingResponse.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Gemini JSON failed schema validation: {e}") from e

    return parsed.mappings, warnings