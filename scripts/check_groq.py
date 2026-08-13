from __future__ import annotations

import os

from app.config import settings
from app.tools.groq_client import complete


def main() -> None:
    if not settings.groq_keys:
        raise SystemExit("No Groq keys configured")
    text = complete("Reply with exactly: groq-ok")
    ok = bool(text.strip())
    print(f"groq_keys={len(settings.groq_keys)} smoke={'ok' if ok else 'empty'}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
