"""Task orchestrator for managing graph invocations."""

import asyncio
from datetime import datetime
from pathlib import Path
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
from xteam_agents.platform.loader import SpecLoader, get_default_specs_path
from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry, TeamRegistry

import httpx

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
        self._magic_core = None  # MAGICCore instance (when MAGIC is enabled)

        # Platform registries (populated during setup)
        self.agent_registry = AgentRegistry()
        self.pipeline_registry = PipelineRegistry()
        self.team_registry = TeamRegistry()

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

        # Load platform specs
        specs_path = (
            Path(self.settings.specs_dir)
            if self.settings.specs_dir
            else get_default_specs_path()
        )
        spec_loader = SpecLoader(
            self.agent_registry,
            self.pipeline_registry,
            self.team_registry,
        )
        counts = spec_loader.load_directory(specs_path)
        logger.info(
            "platform_specs_loaded",
            agents=counts["agents"],
            pipelines=counts["pipelines"],
            teams=counts["teams"],
        )

        # Initialize MAGIC if enabled
        if self.settings.magic_enabled:
            from xteam_agents.magic.core import MAGICCore
            self._magic_core = MAGICCore(self.llm_provider, self.memory_manager)
            logger.info("magic_core_initialized")

        # Build the graph
        self._graph = build_cognitive_graph(
            self.settings,
            self.llm_provider,
            self.memory_manager,
            self.action_executor,
            magic_core=self._magic_core,
        )
        # graph is already compiled by build_cognitive_graph
        # self._graph = compile_graph(graph)

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
            await self.setup()

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

        # Persist task
        await self.memory_manager.task.save_task(task_info)

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

    async def _send_webhook(self, task_id: UUID, status: str, payload: dict) -> None:
        """Send a webhook notification if configured."""
        webhook_url = self.settings.n8n_url  # Using N8N_URL as base or specific webhook URL
        # Or better, check for a specific WEBHOOK_URL env var
        # For now, we'll assume we send to N8N_URL/webhook/xteam-agents
        
        # If N8N_URL is set, we construct a webhook URL
        if not self.settings.n8n_url:
            return

        url = f"{self.settings.n8n_url}/webhook/xteam-agents"
        
        data = {
            "task_id": str(task_id),
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            **payload
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=data, timeout=5.0)
        except Exception as e:
            logger.warning("webhook_failed", error=str(e), url=url)

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
            
            # Send Webhook: STARTED
            await self._send_webhook(task_id, "started", {"description": request.description})

            # Create MAGIC config if enabled
            magic_config = None
            if self._magic_core and self.settings.magic_enabled:
                from xteam_agents.models.magic import (
                    AutonomyLevel,
                    CheckpointStage,
                    MAGICTaskConfig,
                )

                # Parse default checkpoints from settings
                checkpoint_list = []
                if self.settings.magic_default_checkpoints:
                    for cp in self.settings.magic_default_checkpoints.split(","):
                        cp = cp.strip()
                        if cp:
                            try:
                                checkpoint_list.append(CheckpointStage(cp))
                            except ValueError:
                                pass

                magic_config = MAGICTaskConfig(
                    enabled=True,
                    autonomy_level=AutonomyLevel(self.settings.magic_default_autonomy),
                    confidence_threshold=self.settings.magic_default_confidence_threshold,
                    checkpoints=checkpoint_list,
                    escalation_timeout=self.settings.magic_default_escalation_timeout,
                    fallback_on_timeout=self.settings.magic_default_fallback,
                )

                # Override from request metadata if provided
                magic_meta = request.context.get("magic", {})
                if magic_meta.get("autonomy_level"):
                    magic_config.autonomy_level = AutonomyLevel(magic_meta["autonomy_level"])
                if magic_meta.get("confidence_threshold") is not None:
                    magic_config.confidence_threshold = magic_meta["confidence_threshold"]
                if magic_meta.get("checkpoints"):
                    magic_config.checkpoints = [
                        CheckpointStage(cp) for cp in magic_meta["checkpoints"]
                    ]

            # Create initial state
            initial_state = AgentState(
                task_id=task_id,
                description=request.description,
                context=request.context,
                priority=request.priority.value,
                max_iterations=self.settings.max_replan_iterations * 4,  # Allow for replans
                magic_config=magic_config,
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
                            # Update DB
                            await self.memory_manager.task.save_task(self._tasks[task_id])

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
            
            # Persist final state
            await self.memory_manager.task.save_task(self._tasks[task_id])

            logger.info(
                "task_completed",
                task_id=str(task_id),
                status=status.value,
            )
            
            # Send Webhook: COMPLETED/FAILED
            await self._send_webhook(task_id, status.value, {
                "result": final_state.get("execution_result") if final_state else None,
                "error": error
            })

        except asyncio.CancelledError:
            self._tasks[task_id] = self._tasks[task_id].model_copy(
                update={
                    "status": TaskStatus.CANCELLED,
                    "completed_at": datetime.utcnow(),
                }
            )
            await self.memory_manager.task.save_task(self._tasks[task_id])
            
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
            await self.memory_manager.task.save_task(self._tasks[task_id])
            
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
        # Use DB if available, fallback to memory
        if self.memory_manager and self.memory_manager._connected:
             tasks = await self.memory_manager.task.list_tasks(limit)
             if status:
                 tasks = [t for t in tasks if t.status == status]
             return tasks
        
        # Fallback to in-memory
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
