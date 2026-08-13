from __future__ import annotations

import re
from collections import Counter, defaultdict

from app.models import CompetitorMetric, PublicPage, RawFinding, ScoredPost


def mentions(text: str, words: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(word) for word in words)


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
        pricing_words = mentions(text, ["pricing", "plans", "$", "quote", "demo"])
        ai_words = mentions(text, ["ai", "automation", "agent", "intelligence", "brief"])
        hiring_words = mentions(text, ["career", "hiring", "jobs", "role"])
        hooks = hooks_by_competitor[competitor]
        avg_hook = round(sum(post.score for post in hooks) / len(hooks), 1) if hooks else 0.0
        content_pages = len([page for page in competitor_pages if re.search(r"blog|news|resource|linkedin|x|twitter", page.label, re.I) and page.text])
        observed_signals = signal_counts[competitor] + pricing_words + ai_words + hiring_words + len(source_urls)
        metrics.append(
            CompetitorMetric(
                competitor=competitor,
                category=categories.get(competitor, "Competitive intelligence"),
                public_sources=len(source_urls),
                signal_count=signal_counts[competitor],
                verified_count=verified_count_by_competitor.get(competitor, 0),
                pricing_transparency=pricing_words,
                ai_message_score=ai_words,
                hiring_signal_score=hiring_words,
                social_momentum=len(hooks),
                content_velocity=content_pages,
                avg_hook_score=avg_hook,
                share_of_voice=round(signal_counts[competitor] / total_signals * 100, 1),
                market_pressure=observed_signals,
                top_move=top_move(findings_by_competitor[competitor], competitor_pages),
                source_urls=source_urls[:5],
            )
        )
    return sorted(metrics, key=lambda item: item.market_pressure, reverse=True)
