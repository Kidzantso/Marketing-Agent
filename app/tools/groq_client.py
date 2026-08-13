from __future__ import annotations

import itertools

from app.config import settings

_key_cycle = itertools.cycle(settings.groq_keys) if settings.groq_keys else None


def next_key() -> str:
    if _key_cycle is None:
        raise RuntimeError("No Groq API keys configured in environment")
    return next(_key_cycle)


def complete(prompt: str, system: str = "You are a concise B2B marketing analyst.") -> str:
    from groq import Groq

    client = Groq(api_key=next_key())
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=500,
    )
    return response.choices[0].message.content or ""
