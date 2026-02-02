"""MCP admin and system tools."""

from typing import Any

from fastmcp import FastMCP

from xteam_agents.models.action import Capability, HandlerType
from xteam_agents.orchestrator import TaskOrchestrator


def register_admin_tools(mcp: FastMCP, orchestrator: TaskOrchestrator) -> None:
    """Register admin and system tools with the MCP server."""

    @mcp.tool()
    async def list_agents() -> dict[str, Any]:
        """
        List all agents in the cognitive system.

        Returns metadata about each agent including their role,
        capabilities, and current status.

        Returns:
            Dictionary with agent information
        """
        agents = [
            {
                "name": "analyst",
                "role": "Analyze tasks and gather context",
                "node": "analyze",
                "capabilities": ["read_memory", "search_knowledge"],
                "writes_to": "episodic (private)",
            },
            {
                "name": "architect",
                "role": "Design solutions and create plans",
                "node": "plan",
                "capabilities": ["read_memory", "search_knowledge"],
                "writes_to": "episodic (private)",
            },
            {
                "name": "worker",
                "role": "Execute plans and perform actions",
                "node": "execute",
                "capabilities": ["read_memory", "execute_actions"],
                "writes_to": "episodic (private)",
            },
            {
                "name": "reviewer",
                "role": "Validate execution results",
                "node": "validate",
                "capabilities": ["read_memory", "search_knowledge"],
                "writes_to": "episodic (private)",
            },
            {
                "name": "commit_node",
                "role": "Commit validated results to shared memory",
                "node": "commit",
                "capabilities": [],
                "writes_to": "semantic, procedural (shared)",
                "note": "System function, not an LLM agent",
            },
        ]

        return {
            "agents": agents,
            "total": len(agents),
            "graph_flow": "analyze → plan → execute → validate → (commit | replan | fail)",
        }

    @mcp.tool()
    async def get_audit_log(
        task_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Get audit log entries.

        Can filter by task_id or event_type. Returns chronological
        list of system events.

        Args:
            task_id: Optional task UUID to filter by
            event_type: Optional event type filter
            limit: Maximum entries to return (default 100)

        Returns:
            Dictionary with audit entries
        """
        if orchestrator.memory_manager is None:
            return {"error": "Memory manager not initialized"}

        from uuid import UUID

        from xteam_agents.models.audit import AuditEventType

        if task_id:
            try:
                task_uuid = UUID(task_id)
                entries = await orchestrator.memory_manager.audit.get_by_task(
                    task_uuid, limit=limit
                )
            except ValueError:
                return {"error": f"Invalid task_id: {task_id}"}
        elif event_type:
            try:
                event_type_enum = AuditEventType(event_type)
                entries = await orchestrator.memory_manager.audit.get_by_event_type(
                    event_type_enum, limit=limit
                )
            except ValueError:
                return {"error": f"Invalid event_type: {event_type}"}
        else:
            entries = await orchestrator.memory_manager.audit.get_recent(limit=limit)

        return {
            "entries": [
                {
                    "id": str(e.id),
                    "task_id": str(e.task_id) if e.task_id else None,
                    "event_type": e.event_type.value,
                    "description": e.description,
                    "agent_name": e.agent_name,
                    "node_name": e.node_name,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in entries
            ],
            "total": len(entries),
        }

    @mcp.tool()
    async def register_capability(
        name: str,
        description: str,
        handler_type: str,
        requires_approval: bool = False,
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        """
        Register a new capability for agents to use.

        Capabilities define what actions agents can perform.

        Args:
            name: Unique name for the capability
            description: What this capability does
            handler_type: Type of handler - 'code', 'http', 'shell', or 'ci'
            requires_approval: Whether to require human approval before execution
            timeout_seconds: Execution timeout (default 30)

        Returns:
            Dictionary with registered capability info
        """
        if orchestrator.capability_registry is None:
            return {"error": "Capability registry not initialized"}

        # Validate handler type
        try:
            handler_type_enum = HandlerType(handler_type)
        except ValueError:
            return {
                "error": f"Invalid handler_type: {handler_type}. Must be one of: code, http, shell, ci"
            }

        capability = Capability(
            name=name,
            description=description,
            handler_type=handler_type_enum,
            requires_approval=requires_approval,
            timeout_seconds=timeout_seconds,
        )

        registered = orchestrator.capability_registry.register(capability)

        return {
            "id": str(registered.id),
            "name": registered.name,
            "description": registered.description,
            "handler_type": registered.handler_type.value,
            "requires_approval": registered.requires_approval,
            "timeout_seconds": registered.timeout_seconds,
            "message": f"Capability '{name}' registered successfully",
        }

    @mcp.tool()
    async def list_capabilities() -> dict[str, Any]:
        """
        List all registered capabilities.

        Returns:
            Dictionary with all capabilities
        """
        if orchestrator.capability_registry is None:
            return {"error": "Capability registry not initialized"}

        capabilities = orchestrator.capability_registry.list_capabilities()

        return {
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "handler_type": c.handler_type.value,
                    "enabled": c.enabled,
                    "requires_approval": c.requires_approval,
                    "timeout_seconds": c.timeout_seconds,
                }
                for c in capabilities
            ],
            "total": len(capabilities),
        }

    @mcp.tool()
    async def system_health() -> dict[str, Any]:
        """
        Get system health status.

        Returns health information for all components:
        orchestrator, memory backends, and active tasks.

        Returns:
            Dictionary with health status of all components
        """
        health = await orchestrator.system_health()

        return {
            "status": "healthy" if health.get("orchestrator") == "healthy" else "degraded",
            "components": health,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

    @mcp.tool()
    async def get_system_config() -> dict[str, Any]:
        """
        Get current system configuration (non-sensitive values only).

        Returns:
            Dictionary with configuration values
        """
        settings = orchestrator.settings

        return {
            "llm_provider": settings.llm_provider.value,
            "llm_model": settings.llm_model,
            "llm_temperature": settings.llm_temperature,
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "task_timeout_seconds": settings.task_timeout_seconds,
            "max_retries": settings.max_retries,
            "max_replan_iterations": settings.max_replan_iterations,
            "server_port": settings.server_port,
            "log_level": settings.log_level.value,
        }
