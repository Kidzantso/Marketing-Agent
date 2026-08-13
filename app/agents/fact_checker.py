from __future__ import annotations

from urllib.parse import urlparse

from app.models import RawFinding, VerifiedFinding


def domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def claim_key(finding: RawFinding) -> tuple[str, str]:
    return (finding.competitor.lower(), finding.claim_type)


def contradicts(a: str, b: str) -> bool:
    pairs = [("raised", "cut"), ("increased", "decreased"), ("hiring", "layoff")]
    al, bl = a.lower(), b.lower()
    return any((x in al and y in bl) or (y in al and x in bl) for x, y in pairs)


def run(findings: list[RawFinding]) -> list[VerifiedFinding]:
    grouped: dict[tuple[str, str], list[RawFinding]] = {}
    for finding in findings:
        grouped.setdefault(claim_key(finding), []).append(finding)

    checked: list[VerifiedFinding] = []
    for finding in findings:
        peers = grouped[claim_key(finding)]
        peer_domains = {domain(peer.source_url) for peer in peers}
        contradiction = next((peer for peer in peers if peer is not finding and contradicts(finding.claim_text, peer.claim_text)), None)
        if contradiction:
            checked.append(
                VerifiedFinding(
                    **finding.model_dump(),
                    status="dropped",
                    contradiction_note=f"Contradicts {contradiction.source_url}",
                )
            )
        elif len(peer_domains) >= 2:
            checked.append(
                VerifiedFinding(
                    **finding.model_dump(),
                    status="verified",
                    corroborating_sources=sorted({peer.source_url for peer in peers if peer.source_url != finding.source_url}),
                )
            )
        else:
            checked.append(VerifiedFinding(**finding.model_dump(), status="unconfirmed"))
    return checked
