from __future__ import annotations

import json
import os
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

from google import genai
from google.genai import types as genai_types
from pydantic import ValidationError

from app.models.schemas import ColumnInput, ColumnMapping, LLMMappingResponse
from .utils import normalize_text


_SYSTEM_PROMPT = """You map messy Excel column headers to canonical IDs from the provided registries.

Rules:
- param_name MUST be one of parameter_registry[*].name, or null.
- asset_name MUST be one of asset_registry[*].name, or null.
- Do NOT invent new parameters or assets.
- If unsure or ambiguous, set param_name to null and confidence to low.
- Return ONLY valid JSON matching the output_schema. No prose, no markdown fences."""


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM response contained no JSON object.")
    return text[start: end + 1]


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _fallback_map(columns: List[ColumnInput], parameters: List[Dict]) -> List[ColumnMapping]:
    param_blobs = [
        (
            p["name"],
            normalize_text(f"{p['name']} {p.get('display_name', '')} {p.get('unit', '')}"),
        )
        for p in parameters
    ]

    results: List[ColumnMapping] = []
    for col in columns:
        h = normalize_text(col.normalized_header)
        best_name, best_score = None, 0.0

        for name, blob in param_blobs:
            score = _similarity(h, blob)
            if score > best_score:
                best_score = score
                best_name = name

        if best_score >= 0.75:
            confidence = "high"
        elif best_score >= 0.62:
            confidence = "medium"
        else:
            confidence = "low"
            best_name = None

        results.append(
            ColumnMapping(
                column_index=col.column_index,
                param_name=best_name,
                asset_name=col.asset_hint,
                confidence=confidence,
                reason=f"fallback similarity={best_score:.2f}",
            )
        )

    return results


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
        warnings.append("GEMINI_API_KEY not set; used deterministic fallback mapper.")
        return _fallback_map(columns, parameters), warnings

    client = genai.Client(api_key=api_key)

    payload = {
        "task": "map_headers",
        "asset_registry": [
            {"name": a["name"], "display_name": a.get("display_name", "")}
            for a in assets
        ],
        "parameter_registry": [
            {
                "name": p["name"],
                "display_name": p.get("display_name", ""),
                "unit": p.get("unit", ""),
            }
            for p in parameters
        ],
        "columns": [c.model_dump() for c in columns],
        "output_schema": {
            "mappings": [
                {
                    "column_index": "int",
                    "param_name": "string|null",
                    "asset_name": "string|null",
                    "confidence": "high|medium|low",
                    "reason": "string",
                }
            ]
        },
    }

    prompt = _SYSTEM_PROMPT + "\n\nUSER_PAYLOAD_JSON:\n" + json.dumps(payload, ensure_ascii=False)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )

        raw = (response.text or "").strip()
        json_str = _extract_json(raw)
        data = json.loads(json_str)

        parsed = LLMMappingResponse.model_validate(data)
        return parsed.mappings, warnings

    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        warnings.append(f"LLM mapping failed ({exc}); used deterministic fallback.")
        return _fallback_map(columns, parameters), warnings
    except Exception as exc:
        warnings.append(f"Gemini API error ({exc}); used deterministic fallback.")
        return _fallback_map(columns, parameters), warnings