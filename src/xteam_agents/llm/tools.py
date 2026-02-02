"""LangChain tools for agent memory access.

IMPORTANT: These are READ-ONLY tools. Agents cannot write to shared memory
through these tools - only the commit_node can do that.
"""

from typing import Any
from uuid import UUID

from langchain_core.tools import tool

from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.memory import MemoryQuery, MemoryType


def create_memory_tools(memory_manager: MemoryManager) -> list:
    """
    Create read-only memory tools for agents.

    SECURITY: No write_shared_memory tool is exposed.
    Agents can only read from memory through these tools.

    Args:
        memory_manager: The memory manager instance

    Returns:
        List of LangChain tools
    """

    @tool
    async def search_knowledge(
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search the shared knowledge base for relevant information.

        Use this to find previously learned knowledge, documented procedures,
        or insights from past tasks.

        Args:
            query: Natural language query describing what you're looking for
            limit: Maximum number of results to return (default 10)

        Returns:
            List of relevant knowledge items with content and metadata
        """
        results = await memory_manager.search_semantic(query, limit=limit)
        return [
            {
                "content": r.artifact.content,
                "content_type": r.artifact.content_type,
                "score": r.score,
                "created_by": r.artifact.created_by,
                "metadata": r.artifact.metadata,
            }
            for r in results
        ]

    @tool
    async def query_task_memory(
        query: str,
        task_id: str,
        memory_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Query memory for a specific task.

        Use this to find information related to a specific task,
        including analysis, plans, and execution results.

        Args:
            query: Natural language query
            task_id: UUID of the task to query
            memory_types: Types of memory to search (episodic, semantic, procedural)
            limit: Maximum number of results

        Returns:
            List of relevant memory items
        """
        types = [MemoryType(t) for t in (memory_types or ["episodic", "semantic"])]

        memory_query = MemoryQuery(
            query_text=query,
            task_id=UUID(task_id),
            memory_types=types,
            limit=limit,
        )

        results = await memory_manager.query(memory_query)
        return [
            {
                "content": r.artifact.content,
                "content_type": r.artifact.content_type,
                "memory_type": r.source.value,
                "score": r.score,
                "created_by": r.artifact.created_by,
            }
            for r in results
        ]

    @tool
    async def get_task_history(
        task_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get the audit history for a task.

        Use this to understand what has happened during task execution,
        including which nodes were visited and what actions were taken.

        Args:
            task_id: UUID of the task
            limit: Maximum number of audit entries to return

        Returns:
            List of audit entries in chronological order
        """
        entries = await memory_manager.get_audit_log(UUID(task_id), limit)
        return [
            {
                "event_type": e.event_type.value,
                "description": e.description,
                "agent_name": e.agent_name,
                "node_name": e.node_name,
                "timestamp": e.timestamp.isoformat(),
                "data": e.data,
            }
            for e in entries
        ]

    @tool
    async def get_related_knowledge(
        artifact_id: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        """
        Get knowledge related to a specific artifact from the knowledge graph.

        Use this to explore relationships between pieces of knowledge,
        understanding how concepts connect to each other.

        Args:
            artifact_id: UUID of the artifact to explore from
            depth: How many relationship levels to traverse (default 2)

        Returns:
            Graph structure with nodes and relationships
        """
        # Note: This uses the procedural backend's graph capabilities
        # The artifact_id is used to find the associated task
        artifact = await memory_manager.semantic.retrieve(UUID(artifact_id))
        if artifact is None:
            return {"nodes": [], "relationships": [], "error": "Artifact not found"}

        graph = await memory_manager.get_knowledge_graph(artifact.task_id, depth)
        return graph

    # Return list of read-only tools
    # NOTE: No write tools are exposed to agents!
    return [
        search_knowledge,
        query_task_memory,
        get_task_history,
        get_related_knowledge,
    ]


def create_action_tools(action_executor) -> list:
    """
    Create action tools for the worker agent.

    These tools allow the worker to execute registered capabilities.

    Args:
        action_executor: The action executor instance

    Returns:
        List of LangChain tools for action execution
    """
    from xteam_agents.models.action import ActionRequest

    @tool
    async def execute_action(
        capability_name: str,
        parameters: dict[str, Any],
        task_id: str,
        input_data: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a registered capability.

        Use this to perform actions like running code, making HTTP requests,
        or executing shell commands.

        Args:
            capability_name: Name of the capability to execute
            parameters: Parameters for the capability
            task_id: UUID of the current task
            input_data: Optional input data for the action

        Returns:
            Result of the action execution
        """
        request = ActionRequest(
            task_id=UUID(task_id),
            capability_name=capability_name,
            parameters=parameters,
            input_data=input_data,
            requested_by="worker",
        )

        result = await action_executor.execute(request)

        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_seconds": result.duration_seconds,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    @tool
    async def list_capabilities() -> list[dict[str, Any]]:
        """
        List all available capabilities that can be executed.

        Returns:
            List of capability names and descriptions
        """
        capabilities = action_executor.registry.list_capabilities()
        return [
            {
                "name": c.name,
                "description": c.description,
                "handler_type": c.handler_type.value,
                "requires_approval": c.requires_approval,
            }
            for c in capabilities
        ]

    return [execute_action, list_capabilities]
