# CivicBin AI — Smart Bin Overflow Detection & Multi-Agent Collection Routing

Civic Tech solution for **Waste Collection & Bin Overflow**.

Citizens report an overflowing bin with a photo + location. Gemini vision scores
the severity. Two ADK agents — a `TriageAgent` and a `RouteAgent` — talk to each
other over **A2A**, and `RouteAgent` exposes its bin data as an **MCP** tool.
The municipal dashboard shows a live map + AI-generated collection route.

## Architecture

```
Citizen (Streamlit) --photo+geo--> FastAPI /report --> Gemini 2.5 Flash (vision)
                                          |
                                          v
                                    Firestore (reports)
                                          |
                    TriageAgent (ADK) --A2A call--> RouteAgent (ADK)
                          ^                                |
                          |                       exposes MCP tool
                          |                       get_priority_bins()
                          |                                |
                    FastAPI /route  <-----------------------
                          |
                          v
              Municipal Streamlit dashboard (map + route + BigQuery analytics)
```

## Folder structure

```
backend/
  main.py               FastAPI app (endpoints: /report, /bins, /route)
  gemini_service.py     Gemini vision call (bin severity classification)
  firebase_service.py   Firestore read/write
  bigquery_service.py   Append historical rows for analytics
  agents/
    triage_agent.py     ADK LlmAgent that clusters/prioritizes new reports
    route_agent.py      ADK LlmAgent that plans the collection route
    mcp_server.py        Exposes route_agent's data as an MCP tool
    a2a_client.py        Handles the A2A call from TriageAgent -> RouteAgent
streamlit_app/
  citizen_app.py         Citizen-facing report form
  dashboard_app.py        Municipal dashboard (map, route, BigQuery charts)
deployment/
  Dockerfile
  cloudrun_deploy.sh
  agent_engine_deploy.md
data/
  bigquery_schema.sql
```

## Setup

1. `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in:
   - `GOOGLE_API_KEY` (from Google AI Studio) — used for Gemini calls
   - `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` — for Vertex AI / BigQuery
   - `FIREBASE_CREDENTIALS_PATH` — path to your Firebase service-account JSON
   - `BIGQUERY_DATASET`, `BIGQUERY_TABLE`
4. Create the BigQuery table: `bq query < data/bigquery_schema.sql` (or run it in the BigQuery console)
5. Run the backend: `uvicorn backend.main:app --reload --port 8000`
6. Run the citizen app: `streamlit run streamlit_app/citizen_app.py`
7. Run the dashboard: `streamlit run streamlit_app/dashboard_app.py --server.port 8502`

## Local agent dev with Gemini CLI / ADK CLI

Before wiring agents into FastAPI, test them standalone:

```bash
cd backend/agents
adk web        # opens ADK's local web UI to chat with TriageAgent / RouteAgent directly
```

Use `gemini` (Gemini CLI) during development to quickly iterate on the vision
classification prompt in `gemini_service.py` before pasting it back in.

## Deploying

- **Cloud Run**: see `deployment/cloudrun_deploy.sh` — deploys the FastAPI service.
- **Agent Engine**: see `deployment/agent_engine_deploy.md` — deploys `TriageAgent`
  and `RouteAgent` so they run independently of the FastAPI process and can be
  reused by other services via A2A.
- **Firebase**: enable Firestore in your Firebase project; no other config needed
  for this MVP (Firebase Hosting is not required since Streamlit isn't a static site).

## What makes this unique vs. a plain "photo classifier" app

Most bin-overflow projects stop at image classification. This project's core is
the **agent handoff**: `TriageAgent` doesn't just call a Python function to plan
routes — it performs a real **A2A** call to a separately-running `RouteAgent`,
which in turn exposes its own capability as a standard **MCP tool** so any other
agent (or Claude, or a different team's agent) could reuse `get_priority_bins()`
without knowing anything about this codebase's internals.
