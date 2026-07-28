"""
TriageAgent (ADK LlmAgent)

Looks at newly-submitted reports and decides whether they need urgent
escalation. It delegates the actual route-building work to RouteAgent, which
runs as a *separate process* and is called over the A2A protocol via
RemoteA2aAgent - this is the "agent-to-agent" handoff for the project.

Run RouteAgent first:
    uvicorn backend.agents.route_agent.agent:a2a_app --port 8001

Then explore TriageAgent locally with the ADK web UI:
    cd backend/agents && adk web
"""
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

# RouteAgent is discovered via its A2A agent card, not imported directly.
route_agent_remote = RemoteA2aAgent(
    name="route_agent",
    description=(
        "Remote agent that plans prioritized bin-collection routes from "
        "active overflow reports."
    ),
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)

root_agent = Agent(
    name="triage_agent",
    model="gemini-flash-latest",
    description="Triages new bin-overflow reports and escalates route planning to RouteAgent.",
    instruction=(
        "You are the first responder for municipal bin-overflow reports. "
        "When asked to process today's reports, delegate to the route_agent "
        "sub-agent to build the actual collection route, then relay its "
        "summary back to the user. If the route_agent reports zero stops, "
        "tell the user there is nothing to collect right now."
    ),
    sub_agents=[route_agent_remote],
)
