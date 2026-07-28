"""
Exposes `get_priority_bins` as a standard MCP tool, independent of the A2A
exposure in route_agent.py. This is what lets *any* MCP-compatible client
(Claude Desktop, another team's agent, Gemini CLI, etc.) query CivicBin's
priority route without knowing anything about Firestore or ADK.

Run with:
    python backend/agents/mcp_server.py
(stdio transport by default - point an MCP client's config at this script)
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from mcp.server.fastmcp import FastMCP

from backend.agents.route_agent.agent import get_priority_bins

mcp = FastMCP("civicbin-route-planner")


@mcp.tool()
def get_priority_bins_tool() -> dict:
    """Returns the current prioritized bin-collection route for the city.

    Ordered by severity (overflowing bins first) then by shortest travel
    distance between consecutive stops.
    """
    return get_priority_bins()


if __name__ == "__main__":
    mcp.run(transport="stdio")
