from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

from app.models import DiscoveredCompetitor, MarketInsight, MarketingRecommendation
from app.tools.groq_client import complete
from app.tools.web_search_tool import search_web

SOCIAL_DOMAINS = ("linkedin.com", "x.com", "twitter.com", "facebook.com", "instagram.com", "tiktok.com", "youtube.com")
LIST_DOMAINS = ("g2.com", "capterra.com", "softwareadvice.com", "thecmo.com", "startus-insights.com", "thedigitalelevator.com")
BAD_HOSTS = ("cloudflare.com", "developers.cloudflare.com", "openai.com", "gemini.google.com", "chatgpt.com", "perplexity.ai")
BAD_NAMES = {
    "What", "Why", "This", "Please", "Sorry", "Fast", "Attention Required", "Cloudflare Ray ID",
    "Cloudflare Please", "Free", "Free Ai", "OpenAI", "Google Gemini", "ChatGPT", "Perplexity AI",
}


def first_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


def infer_market(company: dict) -> MarketInsight:
    prompt = f"""
Return one JSON object for market research. No markdown.
Company profile:
{json.dumps(company, indent=2)}

Schema:
{{
  "market": "specific market category",
  "target_audience": "buyer",
  "positioning": "short competitive positioning",
  "keywords": ["5 search keywords"],
  "buying_triggers": ["4 buyer triggers"],
  "competitor_queries": ["4 web search queries to find direct competitors"]
}}
"""
    try:
        data = first_json(complete(prompt, system="You are a senior B2B market strategist. Return valid JSON only."))
        return MarketInsight(**data, source="groq")
    except Exception:
        one_liner = str(company.get("one_liner") or company.get("description") or company.get("name") or "")
        words = [word for word in re.findall(r"[A-Za-z][A-Za-z0-9-]+", one_liner.lower()) if len(word) > 3]
        keywords = list(dict.fromkeys(words[:6] or ["software", "marketing", "analytics"]))
        market = " ".join(keywords[:3]).title()
        return MarketInsight(
            market=market,
            target_audience=str(company.get("icp") or "Business buyers"),
            positioning=one_liner or "Differentiated market solution",
            keywords=keywords,
            buying_triggers=["save time", "reduce risk", "improve visibility", "grow pipeline"],
            competitor_queries=[
                f"best \"{market}\" software vendors",
                f"top \"{market}\" companies",
                f"\"{market}\" alternatives pricing",
                f"\"{market}\" competitors",
            ],
            source="fallback",
        )


def clean_name(title: str, host: str) -> str:
    base = re.split(r"[\-|:|–|—]", title)[0].strip()
    if 2 <= len(base) <= 35 and not re.search(r"\b(best|top|pricing|alternatives|reviews)\b", base, re.I):
        return base
    parts = host.removeprefix("www.").split(".")
    return parts[0].replace("-", " ").title()


def page_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:12000]
    except Exception:
        return ""


def extract_names_with_groq(insight: MarketInsight, search_results: list[dict[str, str]], texts: list[str]) -> list[str]:
    prompt = f"""
Extract direct competitor company/product names for this market: {insight.market}
Return JSON only: {{"competitors":["Name 1","Name 2"]}}
Search results:
{json.dumps(search_results[:12], indent=2)}
Page text excerpts:
{json.dumps(texts[:4], indent=2)[:16000]}
Rules: no publishers, no review sites, no generic categories, only vendors a buyer could buy from.
"""
    try:
        data = first_json(complete(prompt, system="You extract B2B competitor names. Return valid JSON only."))
        return [str(name).strip() for name in data.get("competitors", []) if str(name).strip()]
    except Exception:
        return []


def fallback_names(texts: list[str]) -> list[str]:
    blocked = {
        "Best", "Software", "Reviews", "Pricing", "Competitive", "Intelligence", "Companies", "Tools",
        "Facebook", "Instagram", "LinkedIn", "Twitter", "YouTube", "Google", "Microsoft", "OpenAI",
        "What", "Why", "This", "Please", "Sorry", "Cloudflare", "Attention", "Required",
    }
    counts: dict[str, int] = {}
    for text in texts:
        for name in re.findall(r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,2}\b", text):
            if name in BAD_NAMES or name.split()[0] in blocked or len(name) < 3 or len(name) > 35:
                continue
            counts[name] = counts.get(name, 0) + 1
    return [name for name, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:12]]


def official_site_for(name: str, insight: MarketInsight, search_fn=search_web) -> str | None:
    for result in search_fn(f"{name} {insight.market} official website", max_results=5):
        host = urlparse(result["url"]).netloc.lower().removeprefix("www.")
        if not host or any(domain in host for domain in SOCIAL_DOMAINS + LIST_DOMAINS + BAD_HOSTS):
            continue
        parsed = urlparse(result["url"])
        return f"{parsed.scheme or 'https'}://{host}/"
    return None


def discover_competitors(company: dict, insight: MarketInsight, max_competitors: int = 10, search_fn=search_web) -> list[DiscoveredCompetitor]:
    own_name = str(company.get("name", "")).lower()
    by_host: dict[str, DiscoveredCompetitor] = {}
    queries = insight.competitor_queries + [f"{keyword} competitors pricing" for keyword in insight.keywords[:3]]
    all_results: list[dict[str, str]] = []
    for query in queries:
        all_results.extend(search_fn(query, max_results=8))
    list_texts = [page_text(result["url"]) for result in all_results[:6] if any(domain in urlparse(result["url"]).netloc.lower() for domain in LIST_DOMAINS)]
    names = list(dict.fromkeys(extract_names_with_groq(insight, all_results, list_texts) + fallback_names(list_texts)))
    for name in names:
        if own_name and own_name in name.lower():
            continue
        if name in BAD_NAMES:
            continue
        homepage = official_site_for(name, insight, search_fn)
        if not homepage:
            continue
        host = urlparse(homepage).netloc.lower().removeprefix("www.")
        by_host[host] = DiscoveredCompetitor(
            name=name,
            category=insight.market,
            homepage=homepage,
            pricing_url=f"{homepage.rstrip('/')}/pricing",
            blog_url=f"{homepage.rstrip('/')}/blog",
            evidence=[homepage],
        )
        if len(by_host) >= max_competitors:
            break
    if len(by_host) < max_competitors:
        for result in all_results:
            parsed = urlparse(result["url"])
            host = parsed.netloc.lower().removeprefix("www.")
            if not host or any(domain in host for domain in SOCIAL_DOMAINS + LIST_DOMAINS + BAD_HOSTS):
                continue
            name = clean_name(result["title"], host)
            if own_name and own_name in name.lower():
                continue
            if name in BAD_NAMES:
                name = host.split(".")[0].replace("-", " ").title()
            existing = by_host.get(host)
            homepage = f"{parsed.scheme or 'https'}://{host}/"
            evidence = [result["url"]]
            if existing:
                existing.evidence = list(dict.fromkeys(existing.evidence + evidence))
            else:
                by_host[host] = DiscoveredCompetitor(
                    name=name,
                    category=insight.market,
                    homepage=homepage,
                    pricing_url=f"{homepage.rstrip('/')}/pricing",
                    blog_url=f"{homepage.rstrip('/')}/blog",
                    evidence=evidence,
                )
            if len(by_host) >= max_competitors:
                break
    return list(by_host.values())


def enrich_social_urls(competitors: list[DiscoveredCompetitor], search_fn=search_web) -> list[DiscoveredCompetitor]:
    enriched: list[DiscoveredCompetitor] = []
    for competitor in competitors:
        data = competitor.model_dump()
        for result in search_fn(f"{competitor.name} LinkedIn company", max_results=3):
            if "linkedin.com/company" in result["url"]:
                data["linkedin_url"] = result["url"]
                break
        for result in search_fn(f"{competitor.name} X Twitter company", max_results=3):
            if "x.com/" in result["url"] or "twitter.com/" in result["url"]:
                data["x_url"] = result["url"]
                break
        enriched.append(DiscoveredCompetitor(**data))
    return enriched


def write_market_files(competitors: list[DiscoveredCompetitor]) -> None:
    names = [item.name for item in competitors]
    sources = {
        "competitors": {
            item.name: {
                "category": item.category,
                "urls": {
                    key: value
                    for key, value in {
                        "homepage": item.homepage,
                        "pricing": item.pricing_url,
                        "blog": item.blog_url,
                        "linkedin": item.linkedin_url,
                        "x": item.x_url,
                    }.items()
                    if value
                },
            }
            for item in competitors
        }
    }
    with open("data/competitors.yaml", "w", encoding="utf-8") as fh:
        yaml.safe_dump({"competitors": names}, fh, sort_keys=False)
    with open("data/competitor_sources.yaml", "w", encoding="utf-8") as fh:
        yaml.safe_dump(sources, fh, sort_keys=False)


def recommend(insight: MarketInsight, metrics: list, playbook: dict[str, str]) -> list[MarketingRecommendation]:
    leaders = metrics[:3]
    recs: list[MarketingRecommendation] = []
    if leaders:
        leader = leaders[0]
        recs.append(
            MarketingRecommendation(
                priority="high",
                channel="Website",
                action=f"Create comparison page against {leader.competitor} with pricing, proof, and use-case fit.",
                rationale=f"{leader.competitor} has the most observed public signals in this scan: {leader.market_pressure}.",
                suggested_hook="Most comparison pages hide the tradeoff. Here is the honest one.",
                source_competitor=leader.competitor,
            )
        )
    common_hook = next(iter(playbook.values()), "Statistic / data-reveal")
    recs.append(
        MarketingRecommendation(
            priority="high",
            channel="LinkedIn",
            action=f"Publish 3 posts this week around {', '.join(insight.buying_triggers[:2])}.",
            rationale=f"Detected market hooks: {common_hook}. Repeat pattern with your own proof.",
            suggested_hook=f"I reviewed the market for {insight.market}. Here is where buyers still get stuck.",
        )
    )
    recs.append(
        MarketingRecommendation(
            priority="medium",
            channel="Sales",
            action="Turn top competitor moves into battlecard objections and one-slide talk tracks.",
            rationale="Verified public moves are useful only if sales can answer them before calls.",
            suggested_hook="Your competitor changed the story. Your sales deck should change before Friday.",
        )
    )
    return recs
