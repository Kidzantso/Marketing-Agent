from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


ClaimType = Literal["pricing", "announcement", "hiring"]
FindingStatus = Literal["verified", "unconfirmed", "dropped"]
PostFormat = Literal["text", "carousel", "video", "image"]
DraftStatus = Literal["pending_approval", "approved", "rejected"]


class RawFinding(BaseModel):
    competitor: str
    claim_text: str
    source_url: str
    retrieved_at: str = Field(default_factory=now_iso)
    claim_type: ClaimType


class VerifiedFinding(RawFinding):
    status: FindingStatus
    corroborating_sources: list[str] = Field(default_factory=list)
    contradiction_note: str | None = None


class GraphEdge(BaseModel):
    source: str
    relation: str
    target: str
    source_url: str


class GraphSnapshot(BaseModel):
    nodes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    edges: list[GraphEdge] = Field(default_factory=list)


class WeeklyBrief(BaseModel):
    exec_summary: list[str]
    per_competitor: dict[str, list[str]]
    trend_commentary: list[str]
    sources: list[str]


class ChangeLogEntry(BaseModel):
    change_type: Literal["added", "removed", "modified"]
    item: str
    before: Any | None = None
    after: Any | None = None


class SocialPost(BaseModel):
    competitor: str
    platform: str
    text: str
    post_url: str
    posted_at: str
    engagement_signal: str | None = None
    format: PostFormat = "text"


class ScoredPost(SocialPost):
    hook_type: str
    score: int
    features: dict[str, bool | str | int]
    playbook_note: str


class DraftPost(BaseModel):
    platform: str
    text: str
    hook_type: str
    why: str
    self_score: int
    status: DraftStatus = "pending_approval"
    approved_by: str | None = None


class PublicPage(BaseModel):
    competitor: str
    label: str
    url: str
    title: str = ""
    text: str = ""
    status_code: int | None = None
    error: str | None = None
    scraped_at: str = Field(default_factory=now_iso)


class CompetitorMetric(BaseModel):
    competitor: str
    category: str = "Competitive intelligence"
    public_sources: int
    signal_count: int
    verified_count: int
    pricing_transparency: int
    ai_message_score: int
    hiring_signal_score: int
    social_momentum: int
    content_velocity: int
    avg_hook_score: float
    share_of_voice: float
    market_pressure: int
    top_move: str
    source_urls: list[str]


class CompanyMetric(BaseModel):
    company: str
    website_visits: int
    followers_linkedin: int
    followers_x: int
    posts_last_30d: int
    avg_engagement_rate: float
    demo_requests: int
    pipeline_value: int
    conversion_rate: float
    confidence: str = "demo"


class DiscoveredCompetitor(BaseModel):
    name: str
    category: str
    homepage: str
    pricing_url: str | None = None
    blog_url: str | None = None
    linkedin_url: str | None = None
    x_url: str | None = None
    evidence: list[str] = Field(default_factory=list)


class MarketInsight(BaseModel):
    market: str
    target_audience: str
    positioning: str
    keywords: list[str]
    buying_triggers: list[str]
    competitor_queries: list[str]
    source: Literal["groq", "fallback"] = "fallback"


class MarketingRecommendation(BaseModel):
    priority: Literal["high", "medium", "low"]
    channel: str
    action: str
    rationale: str
    suggested_hook: str
    source_competitor: str | None = None


class RunResult(BaseModel):
    run_id: str
    status: Literal["ok", "error"]
    findings: list[RawFinding]
    verified_findings: list[VerifiedFinding]
    graph: GraphSnapshot
    brief: WeeklyBrief
    changelog: list[ChangeLogEntry]
    social_posts: list[SocialPost]
    scored_posts: list[ScoredPost]
    playbook: dict[str, str]
    drafts: list[DraftPost]
    public_pages: list[PublicPage] = Field(default_factory=list)
    competitor_metrics: list[CompetitorMetric] = Field(default_factory=list)
    company_metrics: CompanyMetric | None = None
    market_insight: MarketInsight | None = None
    recommendations: list[MarketingRecommendation] = Field(default_factory=list)
