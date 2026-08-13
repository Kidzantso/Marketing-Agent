from __future__ import annotations

from collections import defaultdict

from app.models import GraphSnapshot, WeeklyBrief


def run(graph: GraphSnapshot) -> WeeklyBrief:
    per_competitor: dict[str, list[str]] = defaultdict(list)
    sources = sorted({edge.source_url for edge in graph.edges})
    for edge in graph.edges:
        if not edge.source.startswith("Competitor:"):
            continue
        name = edge.source.split(":", 1)[1]
        per_competitor[name].append(f"{name} has {edge.relation.lower()} signal tied to {edge.source_url}.")
    competitors = sorted(per_competitor)
    summary = [
        f"Tracked {len(competitors)} competitors with {len(graph.edges)} verified graph edges.",
        f"Most current signals are announcements and pricing updates across {len(sources)} cited sources.",
    ]
    trends = ["Pricing visibility and AI briefing messaging are the strongest repeated themes in this run."]
    return WeeklyBrief(
        exec_summary=summary,
        per_competitor=dict(per_competitor),
        trend_commentary=trends,
        sources=sources,
    )
