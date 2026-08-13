from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()


class Settings:
    data_dir = Path(os.environ.get("APP_DATA_DIR", "data/runs"))
    dry_run = os.environ.get("DRY_RUN", "true").lower() != "false"
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

    @property
    def groq_keys(self) -> list[str]:
        return [
            key
            for key in (
                os.environ.get("GROQ_API_KEY_1"),
                os.environ.get("GROQ_API_KEY_2"),
                os.environ.get("GROQ_API_KEY_3"),
            )
            if key
        ]


settings = Settings()
