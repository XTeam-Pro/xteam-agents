"""FastMCP server application."""

import structlog
from fastmcp import FastMCP

from xteam_agents.config import Settings
from xteam_agents.orchestrator import TaskOrchestrator
from xteam_agents.server.tools.admin_tools import register_admin_tools
from xteam_agents.server.tools.code_tools import register_code_tools
from xteam_agents.server.tools.filesystem_tools import register_filesystem_tools
from xteam_agents.server.tools.magic_tools import register_magic_tools
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
    register_magic_tools(mcp, orchestrator)

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

    # --- Task API ---
    @mcp.custom_route("/api/tasks", methods=["GET"])
    async def list_tasks_endpoint(request: Request) -> JSONResponse:
        """List all tasks."""
        try:
            # Get tasks from PostgreSQL via orchestrator
            import asyncpg
            conn_str = mcp._settings.postgres_url
            conn = await asyncpg.connect(conn_str)

            rows = await conn.fetch("""
                SELECT task_id, description, status, priority, created_at, updated_at
                FROM tasks
                ORDER BY created_at DESC
                LIMIT 100
            """)

            await conn.close()

            tasks = [dict(row) for row in rows]
            return JSONResponse({"tasks": tasks})
        except Exception as e:
            logger.error("api_list_tasks_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/tasks/{task_id}", methods=["GET"])
    async def get_task_endpoint(request: Request) -> JSONResponse:
        """Get task details including execution history."""
        try:
            task_id = request.path_params["task_id"]

            import asyncpg
            conn_str = mcp._settings.postgres_url
            conn = await asyncpg.connect(conn_str)

            # Get task info
            task_row = await conn.fetchrow("""
                SELECT task_id, description, status, priority, created_at, updated_at, result
                FROM tasks
                WHERE task_id = $1
            """, task_id)

            if not task_row:
                await conn.close()
                return JSONResponse({"error": "Task not found"}, status_code=404)

            # Get audit log for task
            audit_rows = await conn.fetch("""
                SELECT timestamp, agent_name, event_type, description, data
                FROM audit_log
                WHERE task_id = $1
                ORDER BY timestamp ASC
            """, task_id)

            await conn.close()

            task = dict(task_row)
            task["audit_log"] = [dict(row) for row in audit_rows]

            return JSONResponse({"task": task})
        except Exception as e:
            logger.error("api_get_task_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    # --- Agents API ---
    @mcp.custom_route("/api/agents/status", methods=["GET"])
    async def get_agents_status_endpoint(request: Request) -> JSONResponse:
        """Get status of all agents including adversarial team."""
        try:
            # Get current active tasks and their states
            import asyncpg
            conn_str = mcp._settings.postgres_url
            conn = await asyncpg.connect(conn_str)

            # Get recent active tasks with their current nodes
            rows = await conn.fetch("""
                SELECT DISTINCT ON (a.task_id)
                    a.task_id,
                    t.description,
                    t.status as task_status,
                    a.agent_name,
                    a.event_type,
                    a.timestamp,
                    a.data
                FROM audit_log a
                JOIN tasks t ON a.task_id = t.task_id
                WHERE a.event_type IN ('node_entered', 'node_exited')
                    AND t.status IN ('analyzing', 'planning', 'executing', 'validating', 'committing')
                ORDER BY a.task_id, a.timestamp DESC
            """)

            await conn.close()

            # Structure: cognitive agents + adversarial team
            cognitive_agents = {
                "analyze": {"status": "idle", "task_id": None},
                "plan": {"status": "idle", "task_id": None},
                "execute": {"status": "idle", "task_id": None},
                "validate": {"status": "idle", "task_id": None},
                "commit": {"status": "idle", "task_id": None},
                "reflect": {"status": "idle", "task_id": None},
            }

            adversarial_agents = {
                "orchestrator": {"status": "idle", "task_id": None},
                "tech_lead": {"status": "idle", "task_id": None, "critic": "idle"},
                "architect": {"status": "idle", "task_id": None, "critic": "idle"},
                "backend": {"status": "idle", "task_id": None, "critic": "idle"},
                "frontend": {"status": "idle", "task_id": None, "critic": "idle"},
                "data": {"status": "idle", "task_id": None, "critic": "idle"},
                "devops": {"status": "idle", "task_id": None, "critic": "idle"},
                "qa": {"status": "idle", "task_id": None, "critic": "idle"},
                "ai_architect": {"status": "idle", "task_id": None, "critic": "idle"},
                "security": {"status": "idle", "task_id": None, "critic": "idle"},
                "performance": {"status": "idle", "task_id": None, "critic": "idle"},
            }

            # Update status based on audit log
            for row in rows:
                agent_name = row["agent_name"]
                if agent_name in cognitive_agents:
                    status = "active" if row["event_type"] == "node_entered" else "idle"
                    cognitive_agents[agent_name] = {
                        "status": status,
                        "task_id": str(row["task_id"]),
                        "timestamp": row["timestamp"].isoformat(),
                    }

            return JSONResponse({
                "cognitive_agents": cognitive_agents,
                "adversarial_agents": adversarial_agents,
                "total_agents": len(cognitive_agents) + len(adversarial_agents),
            })
        except Exception as e:
            logger.error("api_agents_status_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    # --- Metrics API ---
    @mcp.custom_route("/api/metrics/quality", methods=["GET"])
    async def get_quality_metrics_endpoint(request: Request) -> JSONResponse:
        """Get quality metrics and 5D scoring data."""
        try:
            task_id = request.query_params.get("task_id")

            import asyncpg
            conn_str = mcp._settings.postgres_url
            conn = await asyncpg.connect(conn_str)

            if task_id:
                # Get quality scores for specific task
                rows = await conn.fetch("""
                    SELECT timestamp, agent_name, data
                    FROM audit_log
                    WHERE task_id = $1
                        AND event_type = 'quality_score'
                    ORDER BY timestamp DESC
                """, task_id)
            else:
                # Get recent quality scores across all tasks
                rows = await conn.fetch("""
                    SELECT task_id, timestamp, agent_name, data
                    FROM audit_log
                    WHERE event_type = 'quality_score'
                    ORDER BY timestamp DESC
                    LIMIT 50
                """)

            await conn.close()

            # Parse quality scores
            quality_data = []
            for row in rows:
                data = row["data"] or {}
                if "quality_scores" in data:
                    quality_data.append({
                        "task_id": str(row.get("task_id", "")),
                        "timestamp": row["timestamp"].isoformat(),
                        "agent": row["agent_name"],
                        "scores": data["quality_scores"],
                    })

            # Calculate aggregate stats
            if quality_data:
                # Average scores across all dimensions
                avg_scores = {
                    "correctness": 0,
                    "completeness": 0,
                    "efficiency": 0,
                    "maintainability": 0,
                    "security": 0,
                }

                for item in quality_data:
                    scores = item["scores"]
                    for dim in avg_scores:
                        avg_scores[dim] += scores.get(dim, 0)

                count = len(quality_data)
                avg_scores = {k: v / count for k, v in avg_scores.items()}
            else:
                avg_scores = None

            return JSONResponse({
                "quality_data": quality_data,
                "average_scores": avg_scores,
                "total_evaluations": len(quality_data),
            })
        except Exception as e:
            logger.error("api_quality_metrics_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    # --- MAGIC API ---
    @mcp.custom_route("/api/magic/escalations", methods=["GET"])
    async def list_magic_escalations(request: Request) -> JSONResponse:
        """List pending MAGIC escalations."""
        try:
            magic_core = getattr(mcp._orchestrator, "_magic_core", None)
            if not magic_core:
                return JSONResponse({"escalations": [], "count": 0, "magic_enabled": False})

            task_id = request.query_params.get("task_id")
            from uuid import UUID as _UUID
            tid = _UUID(task_id) if task_id else None
            pending = magic_core.escalation_router.get_pending_escalations(tid)

            return JSONResponse({
                "escalations": [
                    {
                        "id": str(e.id),
                        "task_id": str(e.task_id),
                        "reason": e.reason.value,
                        "priority": e.priority.value,
                        "stage": e.stage.value,
                        "question": e.question,
                        "options": e.options,
                        "default_action": e.default_action,
                        "created_at": e.created_at.isoformat(),
                        "confidence": e.confidence_score.to_dict() if e.confidence_score else None,
                    }
                    for e in pending
                ],
                "count": len(pending),
                "magic_enabled": True,
            })
        except Exception as e:
            logger.error("api_magic_escalations_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/magic/escalations/{escalation_id}/respond", methods=["POST"])
    async def respond_magic_escalation(request: Request) -> JSONResponse:
        """Respond to a MAGIC escalation."""
        try:
            magic_core = getattr(mcp._orchestrator, "_magic_core", None)
            if not magic_core:
                return JSONResponse({"error": "MAGIC not enabled"}, status_code=400)

            escalation_id = request.path_params["escalation_id"]
            body = await request.json()

            from uuid import UUID as _UUID
            from xteam_agents.models.magic import HumanResponse, HumanResponseType

            esc_uuid = _UUID(escalation_id)
            response = HumanResponse(
                escalation_id=esc_uuid,
                response_type=HumanResponseType(body.get("response_type", "approval")),
                content=body.get("content", ""),
                data=body.get("data", {}),
                human_id=body.get("human_id", "dashboard"),
            )

            # Find task_id
            pending = magic_core.escalation_router.get_pending_escalations()
            task_id = None
            for esc in pending:
                if esc.id == esc_uuid:
                    task_id = esc.task_id
                    break

            if task_id:
                await magic_core.submit_response(esc_uuid, response, task_id)

            return JSONResponse({"status": "submitted", "escalation_id": escalation_id})
        except Exception as e:
            logger.error("api_magic_respond_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/magic/sessions", methods=["GET"])
    async def list_magic_sessions(request: Request) -> JSONResponse:
        """List active MAGIC collaborative sessions."""
        try:
            magic_core = getattr(mcp._orchestrator, "_magic_core", None)
            if not magic_core:
                return JSONResponse({"sessions": [], "magic_enabled": False})

            sessions = magic_core.session_manager.list_active_sessions()
            return JSONResponse({
                "sessions": [
                    {
                        "id": str(s.id),
                        "task_id": str(s.task_id),
                        "human_id": s.human_id,
                        "status": s.status.value,
                        "messages": s.messages[-20:],  # Last 20 messages
                        "pending_escalations": [str(e) for e in s.pending_escalations],
                        "created_at": s.created_at.isoformat(),
                        "updated_at": s.updated_at.isoformat(),
                    }
                    for s in sessions
                ],
                "count": len(sessions),
                "magic_enabled": True,
            })
        except Exception as e:
            logger.error("api_magic_sessions_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/magic/feedback", methods=["POST"])
    async def submit_magic_feedback(request: Request) -> JSONResponse:
        """Submit human feedback."""
        try:
            magic_core = getattr(mcp._orchestrator, "_magic_core", None)
            if not magic_core:
                return JSONResponse({"error": "MAGIC not enabled"}, status_code=400)

            body = await request.json()
            from uuid import UUID as _UUID
            from xteam_agents.models.magic import FeedbackType, HumanFeedback

            feedback = HumanFeedback(
                task_id=_UUID(body["task_id"]),
                feedback_type=FeedbackType(body.get("feedback_type", "comment")),
                content=body.get("content", ""),
                target_node=body.get("target_node"),
                rating=body.get("rating"),
                should_persist=body.get("should_persist", False),
                applies_to=body.get("applies_to"),
                human_id=body.get("human_id", "dashboard"),
            )

            await magic_core.feedback_collector.record_feedback(feedback)
            magic_core.evolution_engine.record_feedback(
                converted_to_guideline=feedback.should_persist
            )

            return JSONResponse({"feedback_id": str(feedback.id), "status": "recorded"})
        except Exception as e:
            logger.error("api_magic_feedback_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/magic/confidence/{task_id}", methods=["GET"])
    async def get_magic_confidence(request: Request) -> JSONResponse:
        """Get confidence scores for a task."""
        try:
            task_id = request.path_params["task_id"]
            from uuid import UUID as _UUID

            if mcp._orchestrator.memory_manager:
                task_state = await mcp._orchestrator.memory_manager.get_task_state(
                    _UUID(task_id)
                )
                if task_state:
                    return JSONResponse({
                        "task_id": task_id,
                        "scores": task_state.get("confidence_scores", {}),
                    })

            return JSONResponse({"task_id": task_id, "scores": {}})
        except Exception as e:
            logger.error("api_magic_confidence_error", error=str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    @mcp.custom_route("/api/magic/evolution", methods=["GET"])
    async def get_magic_evolution(request: Request) -> JSONResponse:
        """Get evolution metrics."""
        try:
            magic_core = getattr(mcp._orchestrator, "_magic_core", None)
            if not magic_core:
                return JSONResponse({"metrics": [], "proposals": [], "magic_enabled": False})

            metrics = magic_core.compute_metrics()
            proposals = magic_core.get_improvement_proposals()

            return JSONResponse({
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "trend": m.trend,
                        "period_days": m.period_days,
                    }
                    for m in metrics
                ],
                "proposals": proposals,
                "magic_enabled": True,
            })
        except Exception as e:
            logger.error("api_magic_evolution_error", error=str(e))
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
