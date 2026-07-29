"""
RouteAgent (ADK LlmAgent)

Reads active bin reports and available trucks from Firestore, then assigns
each bin to whichever available truck is currently nearest to it — like a
ride-hailing dispatch, not a single fixed-depot route. Each truck gets its
own ordered stop list; capacity limits how many stops a truck can take
before it's considered full for this run.

If no trucks are registered yet, falls back to the original single
imaginary-depot route so the demo still works before any truck is onboarded.

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

from backend.firebase_service import get_active_reports, get_available_trucks

SEVERITY_WEIGHT = {"overflowing": 3, "full": 2, "half_full": 1, "empty": 0}
DEFAULT_DEPOT = (13.0827, 80.2707)  # fallback only, used when no trucks exist


def _dist(a, b):
    return math.dist(a, b)


def get_priority_bins() -> dict:
    """Tool: assigns active bin reports to available trucks and returns each
    truck's ordered stop list.

    Assignment = severity first (all overflowing bins considered before any
    full/half_full bin), then for each bin in that order, pick whichever
    available truck is currently closest to it (from the truck's live
    position, updated as it "moves" through its assigned stops) and that
    still has capacity left. This mirrors how a ride-hailing dispatcher
    assigns the nearest free driver rather than running one fixed route.
    """
    reports = get_active_reports()
    if not reports:
        return {"trucks": [], "unassigned": [], "message": "No active reports."}

    reports.sort(key=lambda r: SEVERITY_WEIGHT.get(r["status"], 0), reverse=True)

    trucks = get_available_trucks()

    if not trucks:
        # No trucks registered yet — fall back to a single imaginary depot
        # so the route feature still works before any truck is onboarded.
        route, current = [], DEFAULT_DEPOT
        for r in reports:
            route.append(r)
            current = (r["lat"], r["lng"])
        return {
            "trucks": [{
                "truck_id": None,
                "name": "Unassigned depot route",
                "driver_name": None,
                "stops": [
                    {"stop": i + 1, "id": r["id"], "city": r.get("city") or "(no city set)",
                     "lat": r["lat"], "lng": r["lng"], "status": r["status"]}
                    for i, r in enumerate(route)
                ],
            }],
            "unassigned": [],
            "message": "No trucks registered — showing a single default-depot route. Register trucks for real dispatch.",
        }

    fleet = {
        t["id"]: {
            "name": t.get("name", t["id"]),
            "driver_name": t.get("driver_name"),
            "pos": (t["lat"], t["lng"]),
            "capacity": t.get("capacity", 8),
            "load": 0,
            "stops": [],
        }
        for t in trucks
    }

    unassigned = []
    for r in reports:
        candidates = [tid for tid, tr in fleet.items() if tr["load"] < tr["capacity"]]
        if not candidates:
            unassigned.append(r)
            continue
        nearest_id = min(candidates, key=lambda tid: _dist(fleet[tid]["pos"], (r["lat"], r["lng"])))
        truck = fleet[nearest_id]
        truck["stops"].append(r)
        truck["pos"] = (r["lat"], r["lng"])
        truck["load"] += 1

    return {
        "trucks": [
            {
                "truck_id": tid,
                "name": tr["name"],
                "driver_name": tr["driver_name"],
                "stops": [
                    {"stop": i + 1, "id": r["id"], "city": r.get("city") or "(no city set)",
                     "lat": r["lat"], "lng": r["lng"], "status": r["status"]}
                    for i, r in enumerate(tr["stops"])
                ],
            }
            for tid, tr in fleet.items() if tr["stops"]
        ],
        "unassigned": [
            {"id": r["id"], "city": r.get("city") or "(no city set)", "status": r["status"]}
            for r in unassigned
        ],
    }


root_agent = Agent(
    name="route_agent",
    model="gemini-flash-latest",
    description="Assigns active bin reports to the nearest available truck and plans each truck's route.",
    instruction=(
        "You are a municipal waste-collection dispatcher. When asked for "
        "today's routes, call the get_priority_bins tool and then summarize "
        "the result for the operations team in 2-3 short sentences: how many "
        "trucks are in use, how many stops each has, and whether any bins "
        "were left unassigned due to full truck capacity."
    ),
    tools=[get_priority_bins],
)

# Expose this agent over A2A so other agents (e.g. TriageAgent) can call it
# as a remote agent. Serve with: uvicorn backend.agents.route_agent:a2a_app --port 8001
a2a_app = to_a2a(root_agent, port=8001)
