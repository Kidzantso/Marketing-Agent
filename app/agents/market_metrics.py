from __future__ import annotations

import re
from collections import Counter, defaultdict

from app.models import CompetitorMetric, PublicPage, RawFinding, ScoredPost


def mentions(text: str, words: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(word) for word in words)


def clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


def top_move(findings: list[RawFinding], pages: list[PublicPage]) -> str:
    if findings:
        return findings[0].claim_text
    usable = next((page for page in pages if page.title), None)
    return usable.title if usable else "No current public move captured."


def run(
    competitors: list[str],
    pages: list[PublicPage],
    findings: list[RawFinding],
    verified_count_by_competitor: dict[str, int],
    scored_posts: list[ScoredPost],
    categories: dict[str, str],
) -> list[CompetitorMetric]:
    pages_by_competitor: dict[str, list[PublicPage]] = defaultdict(list)
    findings_by_competitor: dict[str, list[RawFinding]] = defaultdict(list)
    hooks_by_competitor: dict[str, list[ScoredPost]] = defaultdict(list)
    for page in pages:
        pages_by_competitor[page.competitor].append(page)
    for finding in findings:
        findings_by_competitor[finding.competitor].append(finding)
    for post in scored_posts:
        hooks_by_competitor[post.competitor].append(post)

    signal_counts = Counter({name: len(findings_by_competitor[name]) + len(hooks_by_competitor[name]) for name in competitors})
    total_signals = sum(signal_counts.values()) or 1
    metrics: list[CompetitorMetric] = []
    for competitor in competitors:
        competitor_pages = pages_by_competitor[competitor]
        text = " ".join(page.text for page in competitor_pages if page.text)
        source_urls = [page.url for page in competitor_pages if page.status_code and page.status_code < 400]
        pricing_words = min(mentions(text, ["pricing", "plans", "$", "quote", "demo"]), 8)
        ai_words = min(mentions(text, ["ai", "automation", "agent", "intelligence", "brief"]), 12)
        hiring_words = min(mentions(text, ["career", "hiring", "jobs", "role"]), 8)
        hooks = hooks_by_competitor[competitor]
        avg_hook = round(sum(post.score for post in hooks) / len(hooks), 1) if hooks else 0.0
        velocity = len([page for page in competitor_pages if re.search(r"blog|news|resource", page.label, re.I)]) * 20 + len(hooks) * 8
        pressure = clamp(signal_counts[competitor] * 3 + ai_words * 1.5 + avg_hook * 4 + len(source_urls) * 3)
        metrics.append(
            CompetitorMetric(
                competitor=competitor,
                category=categories.get(competitor, "Competitive intelligence"),
                public_sources=len(source_urls),
                signal_count=signal_counts[competitor],
                verified_count=verified_count_by_competitor.get(competitor, 0),
                pricing_transparency=clamp(pricing_words * 10),
                ai_message_score=clamp(ai_words * 6),
                hiring_signal_score=clamp(hiring_words * 10),
                social_momentum=clamp(avg_hook * 12 + len(hooks) * 6),
                content_velocity=clamp(velocity),
                avg_hook_score=avg_hook,
                share_of_voice=round(signal_counts[competitor] / total_signals * 100, 1),
                market_pressure=pressure,
                top_move=top_move(findings_by_competitor[competitor], competitor_pages),
                source_urls=source_urls[:5],
            )
        )
    return sorted(metrics, key=lambda item: item.market_pressure, reverse=True)
