# Intelligent Excel Parser

A FastAPI service that ingests messy `.xlsx` files and uses Google Gemini to intelligently map column headers to canonical parameter and asset names from a predefined registry. Ships with a built-in web dashboard for interactive file parsing.

---

## What It Does

- Detects header rows automatically, skipping title rows and blank rows
- Normalises column headers and extracts unit and asset hints
- Maps headers to canonical parameter/asset names via Gemini (`gemini-2.5-flash-lite`)
- Falls back to deterministic similarity matching if no API key is present or if the API call fails
- Parses cell values including comma-formatted numbers, percentages, parenthetical negatives `(42.1)`, boolean strings, and common null markers
- Returns structured JSON with per-cell confidence levels (`high`, `medium`, `low`)
- Serves a web dashboard at `/` for drag-and-drop file uploads and visual result inspection

---

## Tech Stack

| Layer | Library |
|---|---|
| API | FastAPI + Uvicorn |
| Excel reading | openpyxl |
| LLM mapping | Google Gemini (`google-genai`) |
| Schema validation | Pydantic v2 |
| Runtime | Python 3.11+ |

---

## Project Structure

```
intelligent-excel-parser/
├── app/
│   ├── main.py                  # FastAPI app, routes
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   ├── registries/
│   │   ├── assets.json          # Canonical asset names (TG-1, AFBC-2, …)
│   │   └── parameters.json      # Canonical parameter names + units
│   ├── services/
│   │   ├── pipeline.py          # Main orchestration logic
│   │   ├── llm_mapper.py        # Gemini API call + fallback mapper
│   │   ├── header_detector.py   # Heuristic header-row detection
│   │   ├── excel_reader.py      # openpyxl sheet reader
│   │   ├── asset_matcher.py     # Alias expansion for asset names
│   │   ├── value_parser.py      # Numeric/boolean/null value parsing
│   │   └── utils.py             # Text normalisation, unit hint extraction
│   └── static/
│       └── index.html           # Web dashboard
├── test_files/
│   ├── test_clean_TG1.xlsx      # 30 days of clean TG-1 performance data
│   ├── test_messy_headers.xlsx  # Title row, multiline headers, % strings, N/A values
│   ├── test_multi_asset.xlsx    # Columns across TG-1, TG-2, AFBC-1/2, KILN-1/2
│   └── test_edge_cases.xlsx     # Parenthetical negatives, Unicode (CO₂/SO₂), booleans, nulls
├── tests/
│   ├── test_header_detector.py
│   └── test_value_parser.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure environment**
```bash
cp .env.example .env
# Edit .env and add your Gemini API key:
# GEMINI_API_KEY=your_key_here
```

**3. Run the server**
```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. The web dashboard is at `http://localhost:8000/`.

---

## API

### `POST /parse`

Upload an `.xlsx` file for parsing.

**Request:** `multipart/form-data` with a `file` field containing a `.xlsx` file.

**Response:**
```json
{
  "status": "success",
  "header_row": 1,
  "parsed_data": [
    {
      "row": 2,
      "col": 1,
      "param_name": "coal_consumption",
      "asset_name": "TG-1",
      "raw_value": "312.5",
      "parsed_value": 312.5,
      "confidence": "high"
    }
  ],
  "unmapped_columns": [
    {
      "col": 4,
      "header": "Remarks",
      "reason": "No matching parameter found in registry."
    }
  ],
  "warnings": [],
  "meta": {
    "sheet": "Sheet1",
    "rows": 32,
    "cols": 8
  }
}
```

### `GET /health`

Returns `{"status": "ok"}`.

---

## Registries

The registries in `app/registries/` define what parameters and assets the parser recognises. Edit these JSON files to extend coverage.

**`assets.json`** — physical assets identified in column headers:

| Name | Display Name |
|---|---|
| `TG-1` … `TG-4` | Turbine Generator 1–4 |
| `AFBC-1` … `AFBC-4` | AFBC Boiler 1–4 |
| `KILN-1` … `KILN-3` | Kiln 1–3 |

**`parameters.json`** — 22 measurable quantities with canonical names and units, including `coal_consumption`, `power_generation`, `heat_rate`, `plant_load_factor`, `co2_emission`, and more.

---

## Fallback Behaviour

If `GEMINI_API_KEY` is not set, or if the Gemini API call fails for any reason (network error, quota exceeded, malformed response), the pipeline automatically falls back to a deterministic similarity matcher. The fallback uses `SequenceMatcher` against normalised parameter names and units, with confidence thresholds of 0.75 for `high` and 0.62 for `medium`. A warning is included in the response when the fallback is used.

---

## Value Parsing

`value_parser.py` handles the following input formats:

| Input | Parsed Value |
|---|---|
| `312.5`, `1,234` | `312.5`, `1234.0` |
| `85.3%` | `0.853` |
| `(42.1)` | `-42.1` (accounting notation) |
| `yes` / `no` | `1.0` / `0.0` |
| `true` / `false` | `1.0` / `0.0` |
| `N/A`, `null`, `—` | `null` |

---

## Testing

```bash
pytest tests/
```

The files in `test_files/` can also be used to exercise the API manually via the dashboard or curl:

```bash
curl -X POST http://localhost:8000/parse \
  -F "file=@test_files/test_messy_headers.xlsx"
```