from __future__ import annotations

from fastapi import FastAPI

from app.config import settings
from app.graph import discover_market, run_weekly
from app.storage import read_json

app = FastAPI(title="Competitive Intel Agent")


@app.get("/health")
def health() -> dict[str, object]:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return {
        "status": "ok",
        "storage": str(settings.data_dir),
        "dry_run": settings.dry_run,
        "groq_configured": bool(settings.groq_keys),
    }


@app.post("/run/weekly")
def run() -> dict:
    return run_weekly().model_dump()


@app.post("/discover")
def discover() -> dict:
    insight, competitors = discover_market()
    return {"insight": insight.model_dump(), "competitors": [item.model_dump() for item in competitors]}


@app.get("/runs/latest")
def latest() -> dict:
    return read_json("latest_run.json") or {"status": "missing"}
