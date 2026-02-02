"""XTeam Agents - Cognitive Operating System with MCP Control Surface."""

__version__ = "0.1.0"

from xteam_agents.config import Settings
from xteam_agents.orchestrator import TaskOrchestrator
from xteam_agents.server.app import create_mcp_server

__all__ = ["Settings", "TaskOrchestrator", "create_mcp_server", "__version__"]
