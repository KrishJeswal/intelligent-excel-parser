# Excel Data Cleaner (Single-sheet)

FastAPI service that ingests messy `.xlsx` files, detects the header row, maps columns to a canonical **parameter registry** + **asset registry**, parses values deterministically, and returns a structured JSON response.

## Model choice
- LLM: **Gemini Developer API** via `google-genai`
- Model: `gemini-2.5-flash-lite`
- LLM is used **once per file** to map column headers → canonical `param_name` (and optionally `asset_name`).
- Value parsing and validations are deterministic.

> If `GEMINI_API_KEY` is not set, the service falls back to a deterministic fuzzy matcher (useful for local tests), and returns a warning.

## Quickstart (local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
python scripts/create_test_data.py

cp .env.example .env

uvicorn app.main:app --reload
```

Health check:
```bash
curl http://127.0.0.1:8000/health
```

Parse an Excel file:
```bash
curl -F "file=@sample_files/messy_data.xlsx" http://127.0.0.1:8000/parse
```

Run tests:
```bash
pytest -q
```

## Docker

Create `.env`:
```text
GEMINI_API_KEY=YOUR_KEY
```

Run:
```bash
docker-compose up --build
```

## Output format

Response includes:
- `status`: `success` or `error`
- `header_row`: 1-indexed Excel row number
- `parsed_data`: list of parsed cells `{row, col, param_name, asset_name, raw_value, parsed_value, confidence}`
- `unmapped_columns`: columns that couldn't be mapped
- `warnings`: detection/mapping warnings
- `meta`: sheet name + basic size metadata

## Notes / Limitations

- Single-sheet only (first worksheet).
- Asset extraction is deterministic using registry aliases; LLM focuses on parameter mapping.
- Confidence is `high|medium|low` per mapped cell.
