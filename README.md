# Competitive Intel Agent

Local CEO/marketing dashboard for competitive intelligence, public web signals, social hook analysis, and our-vs-market comparison.

## Run

```powershell
copy .env.example .env
# add Groq keys to .env if you want live LLM drafting
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/health`, then run a market scan:

```powershell
python -m app.graph
```

Optional dashboard:

```powershell
streamlit run frontend/streamlit_app.py
```

Open `http://localhost:8501`. Use **Run market scan** in the sidebar to refresh public-source scraping and dashboard data.

Sidebar workflow:

1. Fill company profile and current business numbers.
2. Add Groq keys in the Groq keys expander.
3. Click **Discover competitors** to infer the market, search the web, and rewrite `data/competitors.yaml` plus `data/competitor_sources.yaml`.
4. Click **Run full market agent** to scrape sources, score competitors, draft posts, and produce recommendations.

## Test

```powershell
python -m unittest discover -s tests
```

Optional Groq smoke after `.env` has keys:

```powershell
python -m scripts.check_groq
```

## Scope

## Dashboard

- Executive pressure ranking across 10 competitors.
- Competitor scorecards: share of voice, pricing clarity, AI messaging, hiring signal, social momentum, content velocity.
- "Who did what" source-backed findings table.
- Social hook performance and our pending post queue.
- Our business numbers from `data/our_metrics.yaml` vs competitor averages.
- Action tab with marketing recommendations, hooks, and next moves.
- Scraped source health and raw URLs.

## Scope

This build uses Groq-assisted market understanding, web competitor discovery, public web scraping, fixture social posts, JSON storage, FastAPI, and Streamlit.
Docker and GitHub Actions are intentionally skipped. Neo4j, Qdrant, and Postgres are deferred until the step before productionization.
