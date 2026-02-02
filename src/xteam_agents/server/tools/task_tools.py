"""MCP task management tools."""

from typing import Any
from uuid import UUID

from fastmcp import FastMCP

from xteam_agents.models.task import Priority, TaskRequest
from xteam_agents.orchestrator import TaskOrchestrator


def register_task_tools(mcp: FastMCP, orchestrator: TaskOrchestrator) -> None:
    """Register task management tools with the MCP server."""

    @mcp.tool()
    async def submit_task(
        description: str,
        context: dict[str, Any] | None = None,
        priority: int = 3,
    ) -> dict[str, Any]:
        """
        Submit a new task for the cognitive system to execute.

        The task will flow through the cognitive graph:
        ANALYZE → PLAN → EXECUTE → VALIDATE → COMMIT

        Args:
            description: Natural language description of what to accomplish
            context: Optional additional context (key-value pairs)
            priority: Task priority 1-5 (1=lowest, 5=critical), default 3

        Returns:
            Dictionary with task_id and initial status
        """
        # Validate priority
        try:
            priority_enum = Priority(priority)
        except ValueError:
            priority_enum = Priority.MEDIUM

        request = TaskRequest(
            description=description,
            context=context or {},
            priority=priority_enum,
        )

        task_id = await orchestrator.submit_task(request)

        return {
            "task_id": str(task_id),
            "status": "pending",
            "message": f"Task submitted successfully. Use get_task_status to monitor progress.",
        }

    @mcp.tool()
    async def get_task_status(task_id: str) -> dict[str, Any]:
        """
        Get the current status of a task.

        Args:
            task_id: UUID of the task to check

        Returns:
            Dictionary with current status and progress information
        """
        try:
            uuid = UUID(task_id)
        except ValueError:
            return {"error": f"Invalid task_id: {task_id}"}

        task_info = await orchestrator.get_task_info(uuid)

        if task_info is None:
            return {"error": f"Task not found: {task_id}"}

        return {
            "task_id": str(task_info.id),
            "status": task_info.status.value,
            "description": task_info.description,
            "priority": task_info.priority.value,
            "current_node": task_info.current_node,
            "iteration_count": task_info.iteration_count,
            "subtasks_total": task_info.subtasks_total,
            "subtasks_completed": task_info.subtasks_completed,
            "created_at": task_info.created_at.isoformat(),
            "started_at": task_info.started_at.isoformat() if task_info.started_at else None,
            "completed_at": task_info.completed_at.isoformat() if task_info.completed_at else None,
            "error": task_info.error,
        }

    @mcp.tool()
    async def get_task_result(task_id: str) -> dict[str, Any]:
        """
        Get the result of a completed task.

        Only available for tasks with status 'completed' or 'failed'.

        Args:
            task_id: UUID of the task

        Returns:
            Dictionary with task result, artifacts, and metadata
        """
        try:
            uuid = UUID(task_id)
        except ValueError:
            return {"error": f"Invalid task_id: {task_id}"}

        result = await orchestrator.get_task_result(uuid)

        if result is None:
            # Check if task exists
            task_info = await orchestrator.get_task_info(uuid)
            if task_info is None:
                return {"error": f"Task not found: {task_id}"}
            return {
                "error": f"Task not yet complete. Current status: {task_info.status.value}",
                "status": task_info.status.value,
            }

        return {
            "task_id": str(result.task_id),
            "status": result.status.value,
            "result": result.result,
            "artifacts": result.artifacts,
            "error": result.error,
            "iteration_count": result.iteration_count,
            "created_at": result.created_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        }

    @mcp.tool()
    async def cancel_task(task_id: str) -> dict[str, Any]:
        """
        Cancel a running task.

        Only tasks with status 'pending', 'analyzing', 'planning',
        'executing', or 'validating' can be cancelled.

        Args:
            task_id: UUID of the task to cancel

        Returns:
            Dictionary indicating success or failure
        """
        try:
            uuid = UUID(task_id)
        except ValueError:
            return {"error": f"Invalid task_id: {task_id}"}

        success = await orchestrator.cancel_task(uuid)

        if success:
            return {
                "task_id": task_id,
                "cancelled": True,
                "message": "Task cancelled successfully",
            }
        else:
            task_info = await orchestrator.get_task_info(uuid)
            if task_info is None:
                return {"error": f"Task not found: {task_id}"}
            return {
                "task_id": task_id,
                "cancelled": False,
                "message": f"Task cannot be cancelled. Status: {task_info.status.value}",
            }

    @mcp.tool()
    async def list_tasks(
        status: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        List tasks, optionally filtered by status.

        Args:
            status: Optional status filter (pending, analyzing, planning,
                   executing, validating, completed, failed, cancelled)
            limit: Maximum number of tasks to return (default 20)

        Returns:
            Dictionary with list of tasks
        """
        from xteam_agents.models.task import TaskStatus

        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                return {"error": f"Invalid status: {status}"}

        tasks = await orchestrator.list_tasks(status=status_enum, limit=limit)

        return {
            "tasks": [
                {
                    "task_id": str(t.id),
                    "description": t.description[:100],
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "created_at": t.created_at.isoformat(),
                }
                for t in tasks
            ],
            "total": len(tasks),
        }
