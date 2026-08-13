from __future__ import annotations

import re

from app.models import GraphEdge, GraphSnapshot, VerifiedFinding


def product_name(finding: VerifiedFinding) -> str:
    return f"{finding.competitor} platform"


def price_amount(text: str) -> str:
    match = re.search(r"\$\s?\d+(?:,\d{3})*(?:\.\d+)?", text)
    return match.group(0).replace(" ", "") if match else "pricing updated"


def run(findings: list[VerifiedFinding]) -> GraphSnapshot:
    graph = GraphSnapshot()
    for finding in findings:
        if finding.status != "verified":
            continue
        competitor_id = f"Competitor:{finding.competitor}"
        product_id = f"Product:{product_name(finding)}"
        graph.nodes[competitor_id] = {"type": "Competitor", "name": finding.competitor}
        graph.nodes[product_id] = {"type": "Product", "name": product_name(finding)}
        graph.edges.append(GraphEdge(source=competitor_id, relation="OFFERS", target=product_id, source_url=finding.source_url))
        if finding.claim_type == "pricing":
            target = f"PricePoint:{finding.competitor}:{price_amount(finding.claim_text)}"
            graph.nodes[target] = {"type": "PricePoint", "amount": price_amount(finding.claim_text)}
            graph.edges.append(GraphEdge(source=product_id, relation="PRICED_AT", target=target, source_url=finding.source_url))
        else:
            target = f"Announcement:{finding.competitor}:{abs(hash(finding.claim_text))}"
            graph.nodes[target] = {"type": "Announcement", "text": finding.claim_text, "source_url": finding.source_url}
            graph.edges.append(GraphEdge(source=competitor_id, relation="ANNOUNCED", target=target, source_url=finding.source_url))
    return graph
