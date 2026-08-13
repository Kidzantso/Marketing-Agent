from __future__ import annotations

import base64
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup


def fixture_search(competitor: str) -> list[dict[str, str]]:
    slug = competitor.lower().replace(" ", "-")
    return [
        {
            "title": f"{competitor} pricing page changed",
            "url": f"https://{slug}.example.com/pricing",
            "snippet": f"{competitor} updated pricing for its competitive intelligence platform.",
        },
        {
            "title": f"{competitor} pricing coverage",
            "url": f"https://marketwatch.example.org/{slug}/pricing",
            "snippet": f"{competitor} updated pricing for its competitive intelligence platform.",
        },
        {
            "title": f"{competitor} announces AI briefing feature",
            "url": f"https://news.example.org/{slug}-ai-briefing",
            "snippet": f"{competitor} announced an AI briefing feature for market intelligence teams.",
        },
        {
            "title": f"{competitor} product update analysis",
            "url": f"https://analyst.example.net/{slug}/ai-briefing",
            "snippet": f"{competitor} announced an AI briefing feature for market intelligence teams.",
        },
        {
            "title": f"{competitor} hiring product marketers",
            "url": f"https://jobs.example.net/{slug}/pmm",
            "snippet": f"{competitor} is hiring product marketing roles to support expansion.",
        },
        {
            "title": f"{competitor} expansion signal",
            "url": f"https://talent.example.com/{slug}/pmm",
            "snippet": f"{competitor} is hiring product marketing roles to support expansion.",
        },
    ]


def search_web(query: str, max_results: int = 8) -> list[dict[str, str]]:
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            found = ddgs.text(query, max_results=max_results)
        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("href") or item.get("url", ""),
                "snippet": item.get("body", ""),
            }
            for item in found
            if item.get("href") or item.get("url")
        ]
        if results:
            return results
    except Exception:
        pass
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []
        for node in soup.select(".result"):
            link = node.select_one(".result__a")
            snippet = node.select_one(".result__snippet")
            if not link or not link.get("href"):
                continue
            href = link["href"]
            parsed = urlparse(href)
            if "duckduckgo.com" in parsed.netloc or href.startswith("//duckduckgo.com"):
                href = unquote(parse_qs(parsed.query).get("uddg", [href])[0])
            results.append(
                {
                    "title": link.get_text(" ", strip=True),
                    "url": href,
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                }
            )
            if len(results) >= max_results:
                break
        return results or search_bing(query, max_results)
    except Exception:
        return search_bing(query, max_results)


def clean_bing_url(href: str) -> str:
    parsed = urlparse(href)
    encoded = parse_qs(parsed.query).get("u", [""])[0]
    if not encoded:
        return href
    if encoded.startswith("a1"):
        encoded = encoded[2:]
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(padded).decode("utf-8")
    except Exception:
        return href


def search_bing(query: str, max_results: int = 8) -> list[dict[str, str]]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []
        for node in soup.select("li.b_algo"):
            link = node.select_one("h2 a")
            snippet = node.select_one(".b_caption p")
            if not link or not link.get("href"):
                continue
            results.append(
                {
                    "title": link.get_text(" ", strip=True),
                    "url": clean_bing_url(link["href"]),
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                }
            )
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []
