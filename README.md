## Excel Cleaner — Track A (Intelligent Excel Parser)

Built a FastAPI service that takes messy `.xlsx` files, automatically detects the header row, maps columns to a canonical **Parameter Registry** + **Asset Registry** using an LLM (`gemini-2.5-flash-lite`), parses values deterministically (commas, %, YES/NO, N/A), and returns structured JSON with `parsed_data`, `unmapped_columns`, `warnings`, and `meta`. A lightweight dashboard at `/` demonstrates the full end-to-end flow.

### Why Track A
I chose **Track A** because data cleaning is one of the biggest bottlenecks in analytics and ML workflows, and having a reliable, repeatable way to normalize Excel data directly enables future tasks like building strong ML models from that data.

### Setup / Run
**Local**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

Create .env in the project root:
GEMINI_API_KEY=YOUR_KEY_HERE

Generate sample files:
python scripts/create_test_data.py

Run:
python -m uvicorn app.main:app --reload

Open:
Dashboard: http://127.0.0.1:8000/

Docker
docker-compose up --build

Future Improvements

Build a full end-to-end web application (saved uploads/runs, review UI for low-confidence mappings, exports).

Improve mapping accuracy using more signals (units + value patterns + applicability rules) and a feedback loop from user corrections.

Add validation/anomaly detection (e.g., efficiency > 100%, negative consumption) with actionable warnings.

Support multi-sheet parsing and large files with chunking/streaming for performance.

::contentReference[oaicite:0]{index=0}