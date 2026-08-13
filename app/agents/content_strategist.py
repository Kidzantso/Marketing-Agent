from __future__ import annotations

from app.agents.hook_analysis import score
from app.models import DraftPost, SocialPost


def run(playbook: dict[str, str], company: dict[str, object]) -> list[DraftPost]:
    name = str(company["name"])
    one_liner = str(company["one_liner"])
    platforms = list(company.get("platforms", ["LinkedIn"]))
    hooks = ", ".join(playbook.values()) or "Statistic / data-reveal"
    candidates = [
        (
            "Statistic / data-reveal",
            f"I reviewed 10 competitors in this market. Only a few make pricing easy to compare.\n\nThat opacity slows buyers down and leaves teams guessing. {name} turns market signals into a clearer weekly plan.",
        ),
        (
            "Problem-Agitation-Solution",
            f"Your competitor changed their offer. You find out after buyers already ask about it.\n\nThat is weeks of marketing and sales using stale answers. {name} watches public market signals every week.",
        ),
        (
            "Contrarian / challenge-assumption",
            "Most competitive intelligence is a Slack channel someone forgot to check.\n\nA real system has sources, timestamps, diffs, and a human approval step before claims reach customers.",
        ),
    ]
    drafts: list[DraftPost] = []
    for idx, (hook, text) in enumerate(candidates):
        platform = str(platforms[idx % len(platforms)])
        points, _ = score(
            SocialPost(
                competitor=name,
                platform=platform,
                text=text,
                post_url="manual://draft",
                posted_at="draft",
                format="text",
            )
        )
        drafts.append(
            DraftPost(
                platform=platform,
                text=text,
                hook_type=hook,
                why=f"Matches learned competitor patterns: {hooks}. Brand fit: {one_liner}",
                self_score=points,
            )
        )
    return drafts
