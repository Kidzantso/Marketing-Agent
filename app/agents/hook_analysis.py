from __future__ import annotations

import re
from collections import Counter, defaultdict

from app.models import ScoredPost, SocialPost


def hook_type(text: str) -> str:
    lower = text.lower()
    if "?" in text:
        return "Question hook"
    if re.search(r"\b\d+|one hundred|hundred", lower):
        return "Statistic / data-reveal"
    if lower.startswith(("everyone", "most ")):
        return "Contrarian / challenge-assumption"
    if "used to" in lower or "now " in lower:
        return "Before-After-Bridge"
    if "cut " in lower and "%" in lower:
        return "Mini case-study"
    if "pain" in lower or "too late" in lower:
        return "Problem-Agitation-Solution"
    return "Problem-Agitation-Solution"


def score(post: SocialPost) -> tuple[int, dict[str, bool | str | int]]:
    first_line = post.text.splitlines()[0]
    has_number = bool(re.search(r"\d+", post.text))
    single_cta = post.text.lower().count("download") + post.text.lower().count("reply") <= 1
    format_bonus = post.format in {"carousel", "video"}
    points = 3 + int(len(first_line) <= 120) + int(has_number) + int(single_cta) + int(format_bonus)
    return min(points, 7), {
        "first_line_length": len(first_line),
        "specific_first_line": len(first_line) <= 120,
        "concrete_number": has_number,
        "single_cta": single_cta,
        "format_bonus": format_bonus,
    }


def run(posts: list[SocialPost]) -> tuple[list[ScoredPost], dict[str, str]]:
    scored: list[ScoredPost] = []
    hooks_by_competitor: dict[str, Counter[str]] = defaultdict(Counter)
    for post in posts:
        kind = hook_type(post.text)
        points, features = score(post)
        hooks_by_competitor[post.competitor][kind] += 1
        scored.append(
            ScoredPost(
                **post.model_dump(),
                hook_type=kind,
                score=points,
                features=features,
                playbook_note="pending",
            )
        )
    playbook = {
        competitor: ", ".join(hook for hook, _ in counts.most_common(3))
        for competitor, counts in hooks_by_competitor.items()
    }
    scored = [
        item.model_copy(update={"playbook_note": f"{item.competitor}: repeat {playbook[item.competitor]}."})
        for item in scored
    ]
    return scored, playbook
