"""FastMCP server application."""

import structlog
from fastmcp import FastMCP

from xteam_agents.config import Settings
from xteam_agents.orchestrator import TaskOrchestrator
from xteam_agents.server.tools.admin_tools import register_admin_tools
from xteam_agents.server.tools.code_tools import register_code_tools
from xteam_agents.server.tools.filesystem_tools import register_filesystem_tools
from xteam_agents.server.tools.memory_tools import register_memory_tools
from xteam_agents.server.tools.task_tools import register_task_tools
from xteam_agents.server.tools.web_tools import register_web_tools

logger = structlog.get_logger()


def create_mcp_server(
    settings: Settings | None = None,
    orchestrator: TaskOrchestrator | None = None,
) -> FastMCP:
    """
    Create and configure the MCP server.

    Args:
        settings: Application settings (uses defaults if not provided)
        orchestrator: Task orchestrator (creates new if not provided)

    Returns:
        Configured FastMCP server instance
    """
    if settings is None:
        settings = Settings()

    if orchestrator is None:
        orchestrator = TaskOrchestrator(settings)

    # Create the MCP server
    mcp = FastMCP(
        name="xteam-agents",
        instructions="""
XTeam Agents - Cognitive Operating System

This MCP server provides access to a multi-agent cognitive system
with persistent memory and validated knowledge management.

## Available Tools

### Task Management
- submit_task: Submit a new task for execution
- get_task_status: Check task progress
- get_task_result: Get completed task results
- cancel_task: Cancel a running task
- list_tasks: List all tasks

### Memory & Knowledge
- query_memory: Search across all memory types
- search_knowledge: Semantic search in validated knowledge
- get_knowledge_graph: Get task knowledge relationships
- get_task_audit_log: Get task execution history

### Administration
- list_agents: See all cognitive agents
- get_audit_log: System-wide audit log
- register_capability: Add new action capabilities
- list_capabilities: See available actions
- system_health: Check system status
- get_system_config: View configuration

## Architecture

Tasks flow through a cognitive graph:
1. ANALYZE: Understand the task
2. PLAN: Design a solution
3. EXECUTE: Perform actions
4. VALIDATE: Verify results
5. COMMIT: Store validated knowledge

Only validated results are stored in shared memory,
ensuring knowledge quality and consistency.
""",
    )

    # Store references
    mcp._orchestrator = orchestrator
    mcp._settings = settings

    # Register all tools
    register_task_tools(mcp, orchestrator)
    register_memory_tools(mcp, orchestrator)
    register_admin_tools(mcp, orchestrator)
    register_code_tools(mcp, orchestrator)
    register_web_tools(mcp, orchestrator)
    register_filesystem_tools(mcp, orchestrator)

    # Add health check endpoint
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok", 
            "service": "xteam-agents",
            "version": "0.1.0"
        })

    # Setup and teardown hooks
    # FastMCP does not support on_event directly in current version
    # Instead, we rely on the orchestrator setup/teardown being called manually
    # or by the context manager if we were running it differently.
    # For now, we'll initialize it here if needed, but really it should be
    # managed by the lifecycle of the application.
    
    # Since FastMCP doesn't have startup hooks, we will initialize the orchestrator
    # lazily or assume the runner handles it.
    # However, to ensure it's ready, we can schedule it on the loop if running.
    pass

    logger.info(
        "mcp_server_created",
        tool_count=len(mcp._tool_manager._tools) if hasattr(mcp, "_tool_manager") else "unknown",
    )

    return mcp


def get_mcp_server() -> FastMCP:
    """
    Get or create the global MCP server instance.

    This is useful for running with uvicorn or other ASGI servers.
    """
    from xteam_agents.config import get_settings

    settings = get_settings()
    return create_mcp_server(settings)
