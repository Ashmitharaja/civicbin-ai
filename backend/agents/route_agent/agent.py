"""
RouteAgent (ADK LlmAgent)

Reads active bin reports from Firestore and produces a prioritized
collection route (simple severity + nearest-neighbor ordering, with the
LLM used to explain/justify the ordering to the ops team in plain language).

This agent is exposed over A2A via `to_a2a()` at the bottom of this file, so
TriageAgent (a separate process) can call it as a remote agent instead of
importing it directly. Run standalone with:

    uvicorn backend.agents.route_agent.agent:a2a_app --port 8001
"""
import math
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))  # repo root on path

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from backend.firebase_service import get_active_reports

SEVERITY_WEIGHT = {"overflowing": 3, "full": 2, "half_full": 1, "empty": 0}


def get_priority_bins() -> dict:
    """Tool: returns active bin reports ordered into a collection route.

    Ordering = severity first (overflowing bins first), then a simple
    nearest-neighbor walk within each severity tier starting from a fixed
    depot coordinate, so the truck path doesn't zig-zag across the city.
    """
    reports = get_active_reports()
    if not reports:
        return {"route": [], "message": "No active reports."}

    depot = (13.0827, 80.2707)  # example depot coordinate; adjust per city

    def dist(a, b):
        return math.dist(a, b)

    tiers: dict[str, list[dict]] = {"overflowing": [], "full": [], "half_full": []}
    for r in reports:
        tiers.setdefault(r["status"], []).append(r)

    route: list[dict] = []
    current = depot
    for tier_name in ["overflowing", "full", "half_full"]:
        remaining = tiers.get(tier_name, [])
        while remaining:
            nearest = min(remaining, key=lambda r: dist(current, (r["lat"], r["lng"])))
            route.append(nearest)
            current = (nearest["lat"], nearest["lng"])
            remaining.remove(nearest)

    return {
        "route": [
            {"id": r["id"], "lat": r["lat"], "lng": r["lng"], "status": r["status"]}
            for r in route
        ],
        "stop_count": len(route),
    }


root_agent = Agent(
    name="route_agent",
    model="gemini-flash-latest",
    description="Plans a prioritized bin-collection route from active overflow reports.",
    instruction=(
        "You are a municipal waste-collection route planner. When asked for "
        "today's route, call the get_priority_bins tool and then summarize "
        "the route for a truck driver in 2-3 short sentences: how many stops, "
        "how many are urgent (overflowing), and the general order."
    ),
    tools=[get_priority_bins],
)

# Expose this agent over A2A so other agents (e.g. TriageAgent) can call it
# as a remote agent. Serve with: uvicorn backend.agents.route_agent:a2a_app --port 8001
a2a_app = to_a2a(root_agent, port=8001)
