"""Task orchestrator for managing graph invocations."""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from xteam_agents.action.executor import ActionExecutor
from xteam_agents.action.registry import CapabilityRegistry
from xteam_agents.config import Settings
from xteam_agents.graph.builder import build_cognitive_graph, compile_graph
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.state import AgentState
from xteam_agents.models.task import Priority, TaskInfo, TaskRequest, TaskResult, TaskStatus
from xteam_agents.perception.engine import PerceptionEngine

logger = structlog.get_logger()


class TaskOrchestrator:
    """
    Orchestrates task execution through the cognitive graph.

    Manages:
    - Task lifecycle (create, execute, cancel)
    - Graph invocations
    - State persistence
    - Task status tracking
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._tasks: dict[UUID, TaskInfo] = {}
        self._running_tasks: dict[UUID, asyncio.Task] = {}
        self._initialized = False

        # Components (initialized in setup)
        self.memory_manager: MemoryManager | None = None
        self.llm_provider: LLMProvider | None = None
        self.action_executor: ActionExecutor | None = None
        self.perception_engine: PerceptionEngine | None = None
        self.capability_registry: CapabilityRegistry | None = None
        self._graph = None

    async def setup(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return

        logger.info("orchestrator_setup_start")

        # Initialize components
        self.memory_manager = MemoryManager(self.settings)
        await self.memory_manager.connect()

        self.llm_provider = LLMProvider(self.settings)
        self.capability_registry = CapabilityRegistry()
        self.action_executor = ActionExecutor(self.settings, self.capability_registry)
        self.perception_engine = PerceptionEngine(self.settings)
        await self.perception_engine.setup()

        # Build the graph
        graph = build_cognitive_graph(
            self.settings,
            self.llm_provider,
            self.memory_manager,
            self.action_executor,
        )
        self._graph = compile_graph(graph)

        self._initialized = True
        logger.info("orchestrator_setup_complete")

    async def teardown(self) -> None:
        """Cleanup all components."""
        logger.info("orchestrator_teardown_start")

        # Cancel running tasks
        for task_id, task in list(self._running_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Cleanup components
        if self.perception_engine:
            await self.perception_engine.teardown()

        if self.memory_manager:
            await self.memory_manager.disconnect()

        self._initialized = False
        logger.info("orchestrator_teardown_complete")

    async def submit_task(self, request: TaskRequest) -> UUID:
        """
        Submit a new task for execution.

        Args:
            request: The task request

        Returns:
            UUID of the created task
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized. Call setup() first.")

        task_id = uuid4()
        now = datetime.utcnow()

        # Create task info
        task_info = TaskInfo(
            id=task_id,
            description=request.description,
            status=TaskStatus.PENDING,
            priority=request.priority,
            created_at=now,
        )

        self._tasks[task_id] = task_info

        # Log task creation
        await self.memory_manager.log_audit(
            AuditEntry(
                task_id=task_id,
                event_type=AuditEventType.TASK_CREATED,
                description=f"Task created: {request.description[:100]}",
                data={
                    "priority": request.priority.value,
                    "context": request.context,
                },
            )
        )

        # Start task execution in background
        async_task = asyncio.create_task(
            self._execute_task(task_id, request)
        )
        self._running_tasks[task_id] = async_task

        logger.info(
            "task_submitted",
            task_id=str(task_id),
            priority=request.priority.value,
        )

        return task_id

    async def _execute_task(self, task_id: UUID, request: TaskRequest) -> None:
        """Execute a task through the graph."""
        try:
            # Update status
            self._tasks[task_id] = self._tasks[task_id].model_copy(
                update={
                    "status": TaskStatus.ANALYZING,
                    "started_at": datetime.utcnow(),
                }
            )

            await self.memory_manager.log_audit(
                AuditEntry(
                    task_id=task_id,
                    event_type=AuditEventType.TASK_STARTED,
                    description="Task execution started",
                )
            )

            # Create initial state
            initial_state = AgentState(
                task_id=task_id,
                description=request.description,
                context=request.context,
                priority=request.priority.value,
                max_iterations=self.settings.max_replan_iterations * 4,  # Allow for replans
            )

            # Store initial state
            await self.memory_manager.set_task_state(
                task_id,
                initial_state.model_dump(mode="json"),
            )

            # Run the graph
            final_state = None
            async for event in self._graph.astream(initial_state):
                # Update task info based on graph events
                for node_name, node_state in event.items():
                    if isinstance(node_state, dict):
                        current_node = node_state.get("current_node", node_name)

                        # Map node to status
                        status_map = {
                            "analyze": TaskStatus.ANALYZING,
                            "plan": TaskStatus.PLANNING,
                            "execute": TaskStatus.EXECUTING,
                            "validate": TaskStatus.VALIDATING,
                            "commit": TaskStatus.COMMITTING,
                        }

                        new_status = status_map.get(current_node)
                        if new_status:
                            self._tasks[task_id] = self._tasks[task_id].model_copy(
                                update={
                                    "status": new_status,
                                    "current_node": current_node,
                                    "iteration_count": node_state.get(
                                        "iteration_count",
                                        self._tasks[task_id].iteration_count,
                                    ),
                                }
                            )

                        final_state = node_state

            # Determine final status
            if final_state:
                if final_state.get("is_failed"):
                    status = TaskStatus.FAILED
                    error = final_state.get("error")
                elif final_state.get("current_node") == "end" and final_state.get("is_validated"):
                    status = TaskStatus.COMPLETED
                    error = None
                else:
                    status = TaskStatus.COMPLETED
                    error = None
            else:
                status = TaskStatus.FAILED
                error = "No final state returned from graph"

            # Update final task info
            self._tasks[task_id] = self._tasks[task_id].model_copy(
                update={
                    "status": status,
                    "error": error,
                    "completed_at": datetime.utcnow(),
                }
            )

            logger.info(
                "task_completed",
                task_id=str(task_id),
                status=status.value,
            )

        except asyncio.CancelledError:
            self._tasks[task_id] = self._tasks[task_id].model_copy(
                update={
                    "status": TaskStatus.CANCELLED,
                    "completed_at": datetime.utcnow(),
                }
            )
            await self.memory_manager.log_audit(
                AuditEntry(
                    task_id=task_id,
                    event_type=AuditEventType.TASK_CANCELLED,
                    description="Task cancelled",
                )
            )
            raise

        except Exception as e:
            logger.error(
                "task_execution_error",
                task_id=str(task_id),
                error=str(e),
            )
            self._tasks[task_id] = self._tasks[task_id].model_copy(
                update={
                    "status": TaskStatus.FAILED,
                    "error": str(e),
                    "completed_at": datetime.utcnow(),
                }
            )
            await self.memory_manager.log_audit(
                AuditEntry(
                    task_id=task_id,
                    event_type=AuditEventType.TASK_FAILED,
                    description=f"Task failed with error: {str(e)}",
                )
            )

        finally:
            # Cleanup
            self._running_tasks.pop(task_id, None)

    async def get_task_status(self, task_id: UUID) -> TaskStatus | None:
        """Get the status of a task."""
        task_info = self._tasks.get(task_id)
        if task_info:
            return task_info.status
        return None

    async def get_task_info(self, task_id: UUID) -> TaskInfo | None:
        """Get full task info."""
        return self._tasks.get(task_id)

    async def get_task_result(self, task_id: UUID) -> TaskResult | None:
        """Get the result of a completed task."""
        task_info = self._tasks.get(task_id)
        if task_info is None:
            return None

        if task_info.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return None

        # Get stored state for artifacts
        state = await self.memory_manager.get_task_state(task_id)
        artifacts = state.get("artifacts", []) if state else []

        return TaskResult(
            task_id=task_id,
            status=task_info.status,
            result=state.get("execution_result") if state else None,
            artifacts=artifacts,
            error=task_info.error,
            iteration_count=task_info.iteration_count,
            created_at=task_info.created_at,
            completed_at=task_info.completed_at,
        )

    async def cancel_task(self, task_id: UUID) -> bool:
        """Cancel a running task."""
        async_task = self._running_tasks.get(task_id)
        if async_task and not async_task.done():
            async_task.cancel()
            try:
                await async_task
            except asyncio.CancelledError:
                pass
            return True
        return False

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        limit: int = 100,
    ) -> list[TaskInfo]:
        """List tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    async def system_health(self) -> dict[str, Any]:
        """Get system health status."""
        health = {
            "orchestrator": "healthy" if self._initialized else "not_initialized",
            "active_tasks": len(self._running_tasks),
            "total_tasks": len(self._tasks),
        }

        if self.memory_manager:
            health["memory"] = await self.memory_manager.health_check()

        return health
