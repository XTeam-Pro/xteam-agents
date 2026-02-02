"""MCP memory query tools."""

from typing import Any
from uuid import UUID

from fastmcp import FastMCP

from xteam_agents.models.memory import MemoryQuery, MemoryType
from xteam_agents.orchestrator import TaskOrchestrator


def register_memory_tools(mcp: FastMCP, orchestrator: TaskOrchestrator) -> None:
    """Register memory query tools with the MCP server."""

    @mcp.tool()
    async def query_memory(
        query_text: str,
        memory_type: str | None = None,
        task_id: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Query the memory system for relevant information.

        Searches across episodic (short-term), semantic (knowledge),
        and procedural (relationships) memory.

        Args:
            query_text: Natural language query
            memory_type: Optional filter - 'episodic', 'semantic', or 'procedural'
            task_id: Optional task UUID to scope the search
            limit: Maximum results to return (default 10)

        Returns:
            Dictionary with matching memory items
        """
        if orchestrator.memory_manager is None:
            return {"error": "Memory manager not initialized"}

        # Parse memory type
        memory_types = list(MemoryType)
        if memory_type:
            try:
                memory_types = [MemoryType(memory_type)]
            except ValueError:
                return {"error": f"Invalid memory_type: {memory_type}"}

        # Parse task_id
        task_uuid = None
        if task_id:
            try:
                task_uuid = UUID(task_id)
            except ValueError:
                return {"error": f"Invalid task_id: {task_id}"}

        query = MemoryQuery(
            query_text=query_text,
            memory_types=memory_types,
            task_id=task_uuid,
            limit=limit,
        )

        results = await orchestrator.memory_manager.query(query)

        return {
            "results": [
                {
                    "content": r.artifact.content[:500],  # Truncate for response
                    "content_type": r.artifact.content_type,
                    "memory_type": r.source.value,
                    "score": r.score,
                    "created_by": r.artifact.created_by,
                    "created_at": r.artifact.created_at.isoformat(),
                    "is_validated": r.artifact.is_validated,
                }
                for r in results
            ],
            "total": len(results),
            "query": query_text,
        }

    @mcp.tool()
    async def search_knowledge(
        query_text: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Search the shared knowledge base.

        Uses semantic similarity to find relevant knowledge
        from validated, shared memory.

        Args:
            query_text: Natural language query
            limit: Maximum results to return (default 10)

        Returns:
            Dictionary with matching knowledge items
        """
        if orchestrator.memory_manager is None:
            return {"error": "Memory manager not initialized"}

        results = await orchestrator.memory_manager.search_semantic(
            query_text=query_text,
            limit=limit,
        )

        return {
            "results": [
                {
                    "content": r.artifact.content[:500],
                    "content_type": r.artifact.content_type,
                    "score": r.score,
                    "task_id": str(r.artifact.task_id),
                    "created_at": r.artifact.created_at.isoformat(),
                    "metadata": r.artifact.metadata,
                }
                for r in results
            ],
            "total": len(results),
            "query": query_text,
        }

    @mcp.tool()
    async def get_knowledge_graph(
        task_id: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        """
        Get the knowledge graph for a task.

        Returns nodes (knowledge items) and relationships
        from procedural memory.

        Args:
            task_id: UUID of the task
            depth: Relationship traversal depth (default 2)

        Returns:
            Dictionary with nodes and relationships
        """
        if orchestrator.memory_manager is None:
            return {"error": "Memory manager not initialized"}

        try:
            task_uuid = UUID(task_id)
        except ValueError:
            return {"error": f"Invalid task_id: {task_id}"}

        graph = await orchestrator.memory_manager.get_knowledge_graph(
            task_uuid,
            depth=depth,
        )

        return {
            "task_id": task_id,
            "nodes": graph.get("nodes", []),
            "relationships": graph.get("relationships", []),
            "node_count": len(graph.get("nodes", [])),
            "relationship_count": len(graph.get("relationships", [])),
        }

    @mcp.tool()
    async def get_task_audit_log(
        task_id: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get the audit log for a task.

        Returns chronological list of all events during
        task execution.

        Args:
            task_id: UUID of the task
            limit: Maximum entries to return (default 50)

        Returns:
            Dictionary with audit entries
        """
        if orchestrator.memory_manager is None:
            return {"error": "Memory manager not initialized"}

        try:
            task_uuid = UUID(task_id)
        except ValueError:
            return {"error": f"Invalid task_id: {task_id}"}

        entries = await orchestrator.memory_manager.get_audit_log(
            task_uuid,
            limit=limit,
        )

        return {
            "task_id": task_id,
            "entries": [
                {
                    "event_type": e.event_type.value,
                    "description": e.description,
                    "agent_name": e.agent_name,
                    "node_name": e.node_name,
                    "timestamp": e.timestamp.isoformat(),
                    "data": e.data,
                }
                for e in entries
            ],
            "total": len(entries),
        }
