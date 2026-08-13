from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings


def ensure_data_dir() -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ensure_data_dir() / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def read_json(name: str) -> dict[str, Any] | None:
    path = ensure_data_dir() / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
