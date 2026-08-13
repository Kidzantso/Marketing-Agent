from __future__ import annotations

from app.models import RawFinding
from app.models import PublicPage
from app.tools.web_search_tool import fixture_search


def classify_claim(text: str) -> str:
    lower = text.lower()
    if "price" in lower or "pricing" in lower:
        return "pricing"
    if "hiring" in lower or "job" in lower or "role" in lower:
        return "hiring"
    return "announcement"


def run(competitors: list[str], search_fn=fixture_search, limit_per_competitor: int = 10) -> list[RawFinding]:
    findings: list[RawFinding] = []
    seen: set[tuple[str, str]] = set()
    for competitor in competitors:
        for item in search_fn(competitor)[:limit_per_competitor]:
            url = item["url"]
            key = (competitor, url)
            if key in seen:
                continue
            seen.add(key)
            text = item.get("snippet") or item.get("title") or ""
            findings.append(
                RawFinding(
                    competitor=competitor,
                    claim_text=text,
                    source_url=url,
                    claim_type=classify_claim(text),
                )
            )
    return findings


def run_from_pages(pages: list[PublicPage], fallback_competitors: list[str]) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for page in pages:
        if page.error or not page.text:
            continue
        snippets = []
        lower = page.text.lower()
        if any(word in lower for word in ["pricing", "plans", "quote"]):
            snippets.append(("pricing", f"{page.competitor} has public pricing or plan messaging on {page.label}."))
        if any(word in lower for word in ["ai", "automation", "agent", "intelligence"]):
            snippets.append(("announcement", f"{page.competitor} emphasizes AI, automation, or intelligence messaging on {page.label}."))
        if any(word in lower for word in ["career", "hiring", "jobs", "role"]):
            snippets.append(("hiring", f"{page.competitor} shows hiring or career activity on {page.label}."))
        for claim_type, text in snippets:
            findings.append(
                RawFinding(
                    competitor=page.competitor,
                    claim_text=text,
                    source_url=page.url,
                    claim_type=claim_type,
                )
            )
    covered = {finding.competitor for finding in findings}
    missing = [competitor for competitor in fallback_competitors if competitor not in covered]
    return findings + run(missing)
