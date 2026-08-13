from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.agents import analyst, change_log, content_strategist, fact_checker, graph_builder, hook_analysis, market_agent, market_metrics, research, social_listening
from app.models import CompanyMetric, GraphSnapshot, RunResult
from app.storage import read_json, write_json
from app.tools.public_scraper import scrape_competitors


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_competitors() -> list[str]:
    return list(load_yaml("data/competitors.yaml")["competitors"])


def load_company() -> dict:
    return load_yaml("data/company_profile.yaml")


def load_sources() -> dict:
    return load_yaml("data/competitor_sources.yaml")


def load_our_metrics() -> CompanyMetric:
    return CompanyMetric.model_validate(load_yaml("data/our_metrics.yaml"))


def discover_market(company: dict | None = None) -> tuple:
    profile = company or load_company()
    insight = market_agent.infer_market(profile)
    if insight.source != "groq":
        return insight, []
    competitors = market_agent.enrich_social_urls(market_agent.discover_competitors(profile, insight))
    if competitors:
        market_agent.write_market_files(competitors)
    return insight, competitors


def run_weekly(auto_discover: bool = False) -> RunResult:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    company = load_company()
    market_insight = market_agent.infer_market(company)
    if auto_discover:
        market_insight, discovered = discover_market(company)
    competitors = load_competitors()
    sources = load_sources()
    categories = {
        name: data.get("category", "Competitive intelligence")
        for name, data in sources.get("competitors", {}).items()
    }

    public_pages = scrape_competitors(sources, competitors)
    findings = research.run_from_pages(public_pages, competitors)
    verified = fact_checker.run(findings)
    graph = graph_builder.run(verified)
    brief = analyst.run(graph)
    previous_payload = read_json("latest_graph.json")
    previous = GraphSnapshot.model_validate(previous_payload) if previous_payload else None
    changelog = change_log.run(graph, previous)

    posts = social_listening.run(competitors)
    scored, playbook = hook_analysis.run(posts)
    drafts = content_strategist.run(playbook, company)
    verified_counts: dict[str, int] = {}
    for finding in verified:
        if finding.status == "verified":
            verified_counts[finding.competitor] = verified_counts.get(finding.competitor, 0) + 1
    competitor_metrics = market_metrics.run(
        competitors=competitors,
        pages=public_pages,
        findings=findings,
        verified_count_by_competitor=verified_counts,
        scored_posts=scored,
        categories=categories,
    )
    company_metrics = load_our_metrics()
    recommendations = market_agent.recommend(market_insight, competitor_metrics, playbook)

    result = RunResult(
        run_id=run_id,
        status="ok",
        findings=findings,
        verified_findings=verified,
        graph=graph,
        brief=brief,
        changelog=changelog,
        social_posts=posts,
        scored_posts=scored,
        playbook=playbook,
        drafts=drafts,
        public_pages=public_pages,
        competitor_metrics=competitor_metrics,
        company_metrics=company_metrics,
        market_insight=market_insight,
        recommendations=recommendations,
    )
    write_json(f"{run_id}.json", result.model_dump())
    write_json("latest_graph.json", graph.model_dump())
    write_json("latest_run.json", result.model_dump())
    return result


if __name__ == "__main__":
    result = run_weekly()
    print(f"run_id={result.run_id} status={result.status} competitors={len(result.competitor_metrics)} verified={len([f for f in result.verified_findings if f.status == 'verified'])} drafts={len(result.drafts)}")
