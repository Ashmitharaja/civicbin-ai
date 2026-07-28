# Deploying TriageAgent & RouteAgent to Vertex AI Agent Engine

Agent Engine gives the two ADK agents a persistent, managed runtime instead
of running them as ad-hoc local processes — this is what makes the A2A
handoff (TriageAgent -> RouteAgent) work in production instead of only on
`localhost`.

## 1. Install the deployment extras

```bash
pip install google-cloud-aiplatform[adk,agent_engines]
```

## 2. Deploy RouteAgent first (it's the one TriageAgent depends on)

```python
import vertexai
from vertexai import agent_engines
from backend.agents.route_agent import root_agent as route_root_agent

vertexai.init(
    project="YOUR_GCP_PROJECT",
    location="us-central1",
    staging_bucket="gs://YOUR_STAGING_BUCKET",
)

remote_route_agent = agent_engines.create(
    route_root_agent,
    requirements=["google-adk", "google-cloud-aiplatform"],
    display_name="civicbin-route-agent",
)
print(remote_route_agent.resource_name)  # copy this
```

## 3. Point TriageAgent's RemoteA2aAgent at the deployed agent's URL

Update `backend/agents/triage_agent.py`'s `agent_card` URL to the Agent
Engine endpoint printed above (Agent Engine serves the A2A agent card
automatically at the reasoning-engine's public endpoint), then deploy
TriageAgent the same way:

```python
from backend.agents.triage_agent import root_agent as triage_root_agent

remote_triage_agent = agent_engines.create(
    triage_root_agent,
    requirements=["google-adk", "google-cloud-aiplatform"],
    display_name="civicbin-triage-agent",
)
```

## 4. Point the FastAPI backend at the deployed agents

In production, swap the direct `get_priority_bins()` call in
`backend/main.py`'s `/route` endpoint for a call to
`remote_triage_agent.query(...)`, so the live HTTP path exercises the same
deployed agents used elsewhere.

## Local dev vs. production

- **Local dev**: run `route_agent.py` (port 8001) and use `adk web` on
  `triage_agent.py` to test the A2A handoff before deploying anything.
- **Production**: both agents run on Agent Engine; Cloud Run only hosts the
  thin FastAPI layer and the two Streamlit apps talk to it.
