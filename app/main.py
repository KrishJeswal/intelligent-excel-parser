from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv

from app.services.pipeline import parse_excel

load_dotenv()  # optional but helpful for local runs

app = FastAPI(title="Excel Data Cleaner", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/parse")
async def parse(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        return JSONResponse(status_code=400, content={"status": "error", "warnings": ["Only .xlsx files are supported."]})

    file_bytes = await file.read()
    if not file_bytes:
        return JSONResponse(status_code=400, content={"status": "error", "warnings": ["Empty file upload."]})

    result = parse_excel(file_bytes)
    return JSONResponse(content=result.model_dump())