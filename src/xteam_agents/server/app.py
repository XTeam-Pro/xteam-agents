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
    from pydantic import BaseModel
    from xteam_agents.models.task import TaskRequest, Priority
    
    class TaskSubmitRequest(BaseModel):
        description: str
        priority: int = 3
        context: dict | None = None

    @mcp.custom_route("/api/tasks", methods=["POST"])
    async def submit_task_endpoint(request: Request) -> JSONResponse:
        """Submit a new task via REST API."""
        try:
            body = await request.json()
            data = TaskSubmitRequest(**body)
            
            task_req = TaskRequest(
                description=data.description,
                priority=Priority(data.priority),
                context=data.context or {}
            )
            
            result = await mcp._orchestrator.submit_task(task_req)
            return JSONResponse({"task_id": str(result)})
        except Exception as e:
            logger.error("api_submit_task_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/tasks/{task_id}/cancel", methods=["POST"])
    async def cancel_task_endpoint(request: Request) -> JSONResponse:
        """Cancel a task via REST API."""
        try:
            task_id = request.path_params["task_id"]
            result = await mcp._orchestrator.cancel_task(task_id)
            return JSONResponse(result)
        except Exception as e:
            logger.error("api_cancel_task_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    # --- Filesystem API ---
    @mcp.custom_route("/api/files/list", methods=["GET"])
    async def list_files_endpoint(request: Request) -> JSONResponse:
        try:
            path = request.query_params.get("path", ".")
            # Reuse the tool logic (hacky but effective)
            # Better would be to access the registered tool directly
            from xteam_agents.server.tools.filesystem_tools import _validate_path
            import os
            
            target_path = _validate_path(path)
            if not target_path.exists() or not target_path.is_dir():
                return JSONResponse({"error": "Invalid directory"}, status_code=400)
                
            entries = []
            for entry in os.scandir(target_path):
                entries.append({
                    "name": entry.name,
                    "type": "directory" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else None,
                })
            return JSONResponse({"entries": sorted(entries, key=lambda x: (x["type"] != "directory", x["name"]))})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/files/read", methods=["GET"])
    async def read_file_endpoint(request: Request) -> JSONResponse:
        try:
            path = request.query_params.get("path")
            if not path:
                return JSONResponse({"error": "Path required"}, status_code=400)
                
            from xteam_agents.server.tools.filesystem_tools import _validate_path
            target_path = _validate_path(path)
            
            if not target_path.is_file():
                return JSONResponse({"error": "Not a file"}, status_code=400)
                
            content = target_path.read_text(encoding="utf-8")
            return JSONResponse({"content": content})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    # --- Memory API ---
    @mcp.custom_route("/api/memory/search", methods=["GET"])
    async def search_memory_endpoint(request: Request) -> JSONResponse:
        try:
            query = request.query_params.get("query")
            if not query:
                return JSONResponse({"error": "Query required"}, status_code=400)
            
            # Use orchestrator's memory manager
            results = await mcp._orchestrator.memory.search_knowledge(query, limit=10)
            return JSONResponse({"results": [r.model_dump() for r in results]})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/chat", methods=["POST"])
    async def chat_endpoint(request: Request) -> JSONResponse:
        try:
            body = await request.json()
            message = body.get("message")
            if not message:
                return JSONResponse({"error": "Message required"}, status_code=400)
            
            # Simple RAG chat logic
            # 1. Search memory
            # Orchestrator does not have 'memory' attribute directly public, 
            # it has 'memory_manager' or we should access it via property if available.
            # Looking at orchestrator.py, it's self.memory = MemoryManager(settings)
            
            # Check if memory is initialized
            if not hasattr(mcp._orchestrator, 'memory'):
                return JSONResponse({"error": "Memory system not initialized"}, status_code=500)

            mem_results = await mcp._orchestrator.memory.search_knowledge(message, limit=3)
            context = "\n".join([f"- {r.content}" for r in mem_results])
            
            # 2. Call LLM (using the analyst model for Q&A)
            # Use 'analyst' agent's LLM via provider
            model = mcp._orchestrator.llm_provider.get_model_for_agent("analyst")
            response = await model.ainvoke(f"Context:\n{context}\n\nUser Question: {message}\n\nAnswer:")
            
            return JSONResponse({"response": response.content})
        except Exception as e:
            logger.error("api_chat_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

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
