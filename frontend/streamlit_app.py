from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.graph import discover_market, run_weekly

RUN_PATH = Path("data/runs/latest_run.json")
APPROVAL_DIR = Path("data/approvals")
PROFILE_PATH = Path("data/company_profile.yaml")
OUR_METRICS_PATH = Path("data/our_metrics.yaml")

st.set_page_config(page_title="Market Watch Command Center", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    .metric-card {border: 1px solid #d8dee9; border-radius: 8px; padding: 14px; background: #ffffff;}
    .metric-label {font-size: 0.82rem; color: #5b6575; margin-bottom: 4px;}
    .metric-value {font-size: 1.6rem; font-weight: 700; color: #151922;}
    .metric-note {font-size: 0.78rem; color: #6b7280;}
    .move-card {border-left: 4px solid #2f80ed; padding: 10px 12px; background: #f7f9fc; margin-bottom: 8px;}
    .draft-box {border: 1px solid #d8dee9; border-radius: 8px; padding: 14px; margin-bottom: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)


def load_run() -> dict | None:
    if not RUN_PATH.exists():
        return None
    return json.loads(RUN_PATH.read_text(encoding="utf-8"))


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def source_health(run: dict) -> tuple[int, int]:
    pages = run.get("public_pages", [])
    ok = sum(1 for page in pages if page.get("status_code") and page["status_code"] < 400)
    return ok, len(pages)


def write_approval(run_id: str, draft_index: int, decision: str, draft: dict) -> Path:
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    path = APPROVAL_DIR / f"{run_id}-{draft_index}-{decision}.json"
    path.write_text(
        json.dumps({"run_id": run_id, "draft_index": draft_index, "decision": decision, "draft": draft}, indent=2),
        encoding="utf-8",
    )
    return path


def read_yaml(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


with st.sidebar:
    st.title("Market Agent")
    st.caption("Enter company, discover market, run scan")
    profile = read_yaml(
        PROFILE_PATH,
        {
            "name": "",
            "one_liner": "",
            "icp": "",
            "voice": "direct, specific, useful",
            "banned_moves": ["fake urgency", "unverifiable stats"],
            "platforms": ["LinkedIn", "X"],
        },
    )
    our_metrics = read_yaml(
        OUR_METRICS_PATH,
        {
            "company": profile.get("name", ""),
            "website_visits": 0,
            "followers_linkedin": 0,
            "followers_x": 0,
            "posts_last_30d": 0,
            "avg_engagement_rate": 0.0,
            "demo_requests": 0,
            "pipeline_value": 0,
            "conversion_rate": 0.0,
            "confidence": "user input",
        },
    )
    with st.form("company-profile"):
        name = st.text_input("Company", value=str(profile.get("name", "")))
        one_liner = st.text_area("What do you sell?", value=str(profile.get("one_liner", "")), height=90)
        icp = st.text_area("Best customer / ICP", value=str(profile.get("icp", "")), height=80)
        voice = st.text_input("Brand voice", value=str(profile.get("voice", "direct, specific, useful")))
        platforms = st.multiselect("Channels", ["LinkedIn", "X", "TikTok", "Instagram", "YouTube", "Website"], default=list(profile.get("platforms", ["LinkedIn", "X"])))
        visits = st.number_input("Website visits / month", min_value=0, value=int(our_metrics.get("website_visits", 0)), step=100)
        linkedin = st.number_input("LinkedIn followers", min_value=0, value=int(our_metrics.get("followers_linkedin", 0)), step=100)
        x_followers = st.number_input("X followers", min_value=0, value=int(our_metrics.get("followers_x", 0)), step=100)
        posts = st.number_input("Posts last 30d", min_value=0, value=int(our_metrics.get("posts_last_30d", 0)), step=1)
        engagement = st.number_input("Avg engagement rate %", min_value=0.0, value=float(our_metrics.get("avg_engagement_rate", 0.0)), step=0.1)
        demos = st.number_input("Demo requests / month", min_value=0, value=int(our_metrics.get("demo_requests", 0)), step=1)
        pipeline = st.number_input("Pipeline value", min_value=0, value=int(our_metrics.get("pipeline_value", 0)), step=1000)
        conversion = st.number_input("Conversion rate %", min_value=0.0, value=float(our_metrics.get("conversion_rate", 0.0)), step=0.1)
        saved = st.form_submit_button("Save profile", use_container_width=True)
        if saved:
            write_yaml(
                PROFILE_PATH,
                {
                    "name": name,
                    "one_liner": one_liner,
                    "icp": icp,
                    "voice": voice,
                    "banned_moves": ["fake urgency", "unverifiable stats", "naming a customer without permission"],
                    "platforms": platforms or ["LinkedIn", "X"],
                },
            )
            write_yaml(
                OUR_METRICS_PATH,
                {
                    "company": name,
                    "website_visits": visits,
                    "followers_linkedin": linkedin,
                    "followers_x": x_followers,
                    "posts_last_30d": posts,
                    "avg_engagement_rate": engagement,
                    "demo_requests": demos,
                    "pipeline_value": pipeline,
                    "conversion_rate": conversion,
                    "confidence": "user input",
                },
            )
            st.success("Profile saved")
    with st.expander("Groq keys"):
        k1 = st.text_input("GROQ_API_KEY_1", type="password")
        k2 = st.text_input("GROQ_API_KEY_2", type="password")
        k3 = st.text_input("GROQ_API_KEY_3", type="password")
        if st.button("Save Groq keys", use_container_width=True):
            existing = {}
            env_path = Path(".env")
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.split("=", 1)
                        existing[key] = value
            for key, value in {"GROQ_API_KEY_1": k1, "GROQ_API_KEY_2": k2, "GROQ_API_KEY_3": k3}.items():
                if value:
                    existing[key] = value
                    os.environ[key] = value
            env_path.write_text("\n".join(f"{key}={value}" for key, value in existing.items()) + "\n", encoding="utf-8")
            st.success("Groq keys saved to local .env")
    if st.button("Discover competitors", use_container_width=True):
        with st.spinner("Using Groq + web search to discover competitors..."):
            insight, competitors = discover_market()
        if competitors:
            st.success(f"Discovered {len(competitors)} competitors for {insight.market}")
        else:
            st.warning("No Groq-backed discovery ran. Add Groq keys, then try again.")
    if st.button("Run full market agent", use_container_width=True):
        with st.spinner("Discovering, scraping public sources, scoring, drafting..."):
            run_weekly(auto_discover=True)
        st.rerun()
    st.divider()
    st.write("Local scope")
    st.write("- Groq profile understanding")
    st.write("- Web competitor discovery")
    st.write("- Public web scraping")
    st.write("- JSON storage")
    st.write("- No Docker")
    st.write("- No GitHub Actions")

run = load_run()
if not run:
    st.title("Market Watch Command Center")
    st.info("Run first scan from sidebar.")
    st.stop()

metrics = pd.DataFrame(run.get("competitor_metrics", []))
company = run.get("company_metrics") or {}
company_name = company.get("company") or read_yaml(PROFILE_PATH, {}).get("name", "Our company")
drafts = run.get("drafts", [])
verified = [item for item in run.get("verified_findings", []) if item["status"] == "verified"]
ok_sources, total_sources = source_health(run)

st.title("Market Watch Command Center")
st.caption(f"Run {run['run_id']} | public sources {ok_sources}/{total_sources} reachable | drafts require approval")

top_pressure = int(metrics["market_pressure"].max()) if not metrics.empty else 0
share_leader = metrics.iloc[0]["competitor"] if not metrics.empty else "n/a"
avg_hook = round(metrics["avg_hook_score"].mean(), 1) if not metrics.empty else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Market pressure", str(top_pressure), f"Leader: {share_leader}")
with col2:
    metric_card("Verified moves", str(len(verified)), "2-source rule where available")
with col3:
    metric_card("Our pipeline", f"${company.get('pipeline_value', 0):,}", f"{company.get('demo_requests', 0)} demo requests")
with col4:
    metric_card("Avg hook score", str(avg_hook), f"{len(drafts)} posts pending")

overview, competitors_tab, social_tab, our_tab, recs_tab, sources_tab = st.tabs(
    ["Executive", "Competitors", "Social & Posts", "Our Business", "Actions", "Sources"]
)

with overview:
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Who is moving")
        if not metrics.empty:
            fig = px.bar(
                metrics.head(8),
                x="market_pressure",
                y="competitor",
                orientation="h",
                color="share_of_voice",
                color_continuous_scale="Blues",
                labels={"market_pressure": "Market pressure", "competitor": ""},
            )
            fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"}, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Board-level readout")
        if run.get("market_insight"):
            insight = run["market_insight"]
            st.write(f"Market: {insight['market']}")
            st.write(f"Positioning: {insight['positioning']}")
        for line in run["brief"]["exec_summary"]:
            st.write(line)
        st.subheader("Top moves")
        for item in metrics.head(4).to_dict("records"):
            st.markdown(
                f"""
                <div class="move-card">
                  <b>{item['competitor']}</b><br>
                  {item['top_move']}<br>
                  <small>Pressure {item['market_pressure']} | SOV {item['share_of_voice']}%</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.subheader("Strategic signal mix")
    if not metrics.empty:
        radar_source = metrics.head(5)
        fig = go.Figure()
        for row in radar_source.to_dict("records"):
            fig.add_trace(
                go.Scatterpolar(
                    r=[
                        row["pricing_transparency"],
                        row["ai_message_score"],
                        row["hiring_signal_score"],
                        row["social_momentum"],
                        row["content_velocity"],
                    ],
                    theta=["Pricing", "AI message", "Hiring", "Social", "Content"],
                    fill="toself",
                    name=row["competitor"],
                )
            )
        fig.update_layout(height=460, polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

with competitors_tab:
    st.subheader("Competitor scorecards")
    display_cols = [
        "competitor",
        "category",
        "market_pressure",
        "share_of_voice",
        "signal_count",
        "verified_count",
        "pricing_transparency",
        "ai_message_score",
        "social_momentum",
        "content_velocity",
        "avg_hook_score",
    ]
    st.dataframe(metrics[display_cols] if not metrics.empty else metrics, use_container_width=True, hide_index=True)

    st.subheader("What changed")
    findings = pd.DataFrame(run.get("findings", []))
    if not findings.empty:
        st.dataframe(
            findings[["competitor", "claim_type", "claim_text", "source_url"]].head(80),
            use_container_width=True,
            hide_index=True,
        )

with social_tab:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Hook performance")
        scored = pd.DataFrame(run.get("scored_posts", []))
        if not scored.empty:
            hook_summary = scored.groupby("hook_type", as_index=False)["score"].mean().sort_values("score", ascending=False)
            fig = px.bar(hook_summary, x="score", y="hook_type", orientation="h", labels={"score": "Avg score", "hook_type": ""})
            fig.update_layout(height=360, yaxis={"categoryorder": "total ascending"}, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(scored[["competitor", "platform", "hook_type", "score", "text"]].head(30), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Our post queue")
        for idx, draft in enumerate(drafts, start=1):
            st.markdown(
                f"""
                <div class="draft-box">
                  <b>{draft['platform']} | {draft['hook_type']} | score {draft['self_score']}</b><br><br>
                  {draft['text'].replace(chr(10), '<br>')}<br><br>
                  <small>{draft['why']}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns([1, 1, 4])
            if c1.button("Approve", key=f"approve-{idx}"):
                path = write_approval(run["run_id"], idx, "approved", draft)
                st.toast(f"Approved: {path.name}")
            if c2.button("Reject", key=f"reject-{idx}"):
                path = write_approval(run["run_id"], idx, "rejected", draft)
                st.toast(f"Rejected: {path.name}")
            c3.caption("Decision logged locally. No auto-posting.")

with our_tab:
    st.subheader("Our business numbers")
    a, b, c, d = st.columns(4)
    a.metric("Website visits", f"{company.get('website_visits', 0):,}")
    b.metric("LinkedIn followers", f"{company.get('followers_linkedin', 0):,}")
    c.metric("Demo requests", f"{company.get('demo_requests', 0):,}")
    d.metric("Conversion rate", f"{company.get('conversion_rate', 0)}%")

    st.subheader("Us vs market")
    if not metrics.empty:
        our_social = min(100, round(company.get("avg_engagement_rate", 0) * 15 + company.get("posts_last_30d", 0) * 1.2))
        our_reach = min(100, round((company.get("followers_linkedin", 0) + company.get("followers_x", 0)) / 100))
        market_avg = {
            "Social momentum": round(metrics["social_momentum"].mean()),
            "Content velocity": round(metrics["content_velocity"].mean()),
            "AI message": round(metrics["ai_message_score"].mean()),
            "Pricing clarity": round(metrics["pricing_transparency"].mean()),
        }
        compare = pd.DataFrame(
            [
                {"metric": "Social momentum", company_name: our_social, "Competitor avg": market_avg["Social momentum"]},
                {"metric": "Content velocity", company_name: min(100, company.get("posts_last_30d", 0) * 3), "Competitor avg": market_avg["Content velocity"]},
                {"metric": "AI message", company_name: 78, "Competitor avg": market_avg["AI message"]},
                {"metric": "Pricing clarity", company_name: 66, "Competitor avg": market_avg["Pricing clarity"]},
                {"metric": "Reach index", company_name: our_reach, "Competitor avg": 55},
            ]
        )
        fig = px.bar(compare, x="metric", y=[company_name, "Competitor avg"], barmode="group")
        fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Index")
        st.plotly_chart(fig, use_container_width=True)

with recs_tab:
    st.subheader("What we should do next")
    for rec in run.get("recommendations", []):
        st.markdown(
            f"""
            <div class="move-card">
              <b>{rec['priority'].upper()} | {rec['channel']}</b><br>
              {rec['action']}<br>
              <small>{rec['rationale']}</small><br>
              <small><b>Hook:</b> {rec['suggested_hook']}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if run.get("market_insight"):
        st.subheader("Market understanding")
        insight = run["market_insight"]
        st.write(f"Audience: {insight['target_audience']}")
        st.write(f"Keywords: {', '.join(insight['keywords'])}")
        st.write(f"Buying triggers: {', '.join(insight['buying_triggers'])}")
        st.caption(f"Source: {insight['source']}")

with sources_tab:
    st.subheader("Scraped public sources")
    pages = pd.DataFrame(run.get("public_pages", []))
    if not pages.empty:
        pages["ok"] = pages["status_code"].fillna(0).astype(int).between(200, 399)
        st.dataframe(
            pages[["competitor", "label", "url", "status_code", "ok", "title", "error"]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Source URLs used by scorecards")
    for item in metrics.to_dict("records"):
        with st.expander(item["competitor"]):
            for url in item["source_urls"]:
                st.write(url)
