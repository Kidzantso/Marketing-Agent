from __future__ import annotations

import re
from collections.abc import Iterable

import requests
from bs4 import BeautifulSoup

from app.models import PublicPage

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LocalMarketWatch/0.1; +https://example.local)",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def scrape_page(competitor: str, label: str, url: str, timeout: int = 8) -> PublicPage:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = clean_text(soup.title.get_text(" ")) if soup.title else ""
        text = clean_text(soup.get_text(" "))[:6000]
        return PublicPage(
            competitor=competitor,
            label=label,
            url=url,
            title=title,
            text=text,
            status_code=response.status_code,
        )
    except Exception as exc:
        return PublicPage(competitor=competitor, label=label, url=url, error=str(exc))


def scrape_competitors(source_config: dict, competitors: Iterable[str]) -> list[PublicPage]:
    pages: list[PublicPage] = []
    configured = source_config.get("competitors", {})
    for competitor in competitors:
        urls = configured.get(competitor, {}).get("urls", {})
        for label, url in urls.items():
            pages.append(scrape_page(competitor, label, url))
    return pages
