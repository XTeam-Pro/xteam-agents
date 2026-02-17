"""Core runtime for executing agents and pipelines with resource tracking.

Supports recursive pipeline execution where agents can spawn child pipelines
within their resource budget.
"""

from __future__ import annotations

import time
from typing import Any, Callable, TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from xteam_agents.platform.budget import ResourceBudget
from xteam_agents.platform.conditions import ConditionRegistry
from xteam_agents.platform.context import ExecutionContext, PipelineResult, PipelineStatus
from xteam_agents.platform.errors import (
    BudgetExhaustedError,
    MaxDepthExceededError,
    PipelineSpecNotFoundError,
)
from xteam_agents.platform.graph_builder import DynamicGraphBuilder
from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry
from xteam_agents.models.state import AgentState

if TYPE_CHECKING:
    from xteam_agents.memory.manager import MemoryManager
    from xteam_agents.llm.provider import LLMProvider
    from xteam_agents.action.executor import ActionExecutor

logger = structlog.get_logger()


class AgentRuntime:
    """Core runtime — executes pipelines with resource tracking and recursive spawning."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        pipeline_registry: PipelineRegistry,
        condition_registry: ConditionRegistry,
        memory_manager: MemoryManager | None = None,
        llm_provider: LLMProvider | None = None,
        action_executor: ActionExecutor | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.pipeline_registry = pipeline_registry
        self.condition_registry = condition_registry
        self.memory_manager = memory_manager
        self.llm_provider = llm_provider
        self.action_executor = action_executor

        self.graph_builder = DynamicGraphBuilder(
            agent_registry=agent_registry,
            condition_registry=condition_registry,
        )

        self._active_contexts: dict[UUID, ExecutionContext] = {}

    def set_node_factory(self, factory: Callable[[str, dict], Callable]) -> None:
        """Set the factory that creates LangGraph node functions from agent specs."""
        self.graph_builder.set_node_factory(factory)

    async def execute_pipeline(
        self,
        pipeline_id: str,
        initial_state: AgentState,
        budget: ResourceBudget | None = None,
        parent_context: ExecutionContext | None = None,
    ) -> PipelineResult:
        """Execute a pipeline with resource tracking."""
        start_time = time.time()

        spec = self.pipeline_registry.get_or_none(pipeline_id)
        if spec is None:
            raise PipelineSpecNotFoundError(pipeline_id)

        if budget is None:
            if spec.resource_budget:
                budget = ResourceBudget.from_dict(spec.resource_budget)
            else:
                budget = ResourceBudget()

        if budget.is_exhausted():
            return PipelineResult(
                pipeline_id=pipeline_id,
                status=PipelineStatus.BUDGET_EXHAUSTED,
                error="Budget exhausted before pipeline start",
                budget_consumed=budget.to_dict(),
            )

        depth = parent_context.depth + 1 if parent_context else 0
        if depth > budget.max_depth:
            return PipelineResult(
                pipeline_id=pipeline_id,
                status=PipelineStatus.DEPTH_EXCEEDED,
                error=f"Max depth {budget.max_depth} exceeded at depth {depth}",
                budget_consumed=budget.to_dict(),
            )

        context = ExecutionContext(
            pipeline_id=pipeline_id,
            task_id=initial_state.task_id,
            depth=depth,
            parent_context_id=parent_context.context_id if parent_context else None,
            budget=budget,
        )
        context.start()
        self._active_contexts[context.context_id] = context

        logger.info(
            "pipeline_execution_start",
            pipeline_id=pipeline_id,
            depth=depth,
            budget_tokens=budget.remaining_tokens(),
        )

        try:
            compiled_graph = self.graph_builder.build(spec)

            final_state = None
            async for event in compiled_graph.astream(initial_state):
                for node_name, node_state in event.items():
                    context.visit_node(node_name)
                    final_state = node_state

                    if budget.is_exhausted():
                        logger.warning("budget_exhausted_during_execution", pipeline_id=pipeline_id)
                        context.complete(PipelineStatus.BUDGET_EXHAUSTED)
                        return PipelineResult(
                            pipeline_id=pipeline_id,
                            status=PipelineStatus.BUDGET_EXHAUSTED,
                            result=str(final_state) if final_state else None,
                            budget_consumed=budget.to_dict(),
                            execution_time_seconds=time.time() - start_time,
                        )

            execution_time = time.time() - start_time
            context.complete(PipelineStatus.COMPLETED)

            result_text = None
            artifacts = []
            if isinstance(final_state, dict):
                result_text = final_state.get("execution_result")
                artifacts = final_state.get("artifacts", [])

            logger.info(
                "pipeline_execution_complete",
                pipeline_id=pipeline_id,
                depth=depth,
                execution_time=round(execution_time, 2),
            )

            return PipelineResult(
                pipeline_id=pipeline_id,
                status=PipelineStatus.COMPLETED,
                result=result_text,
                artifacts=artifacts,
                budget_consumed=budget.to_dict(),
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            context.complete(PipelineStatus.FAILED)
            logger.error("pipeline_execution_failed", pipeline_id=pipeline_id, error=str(e))

            return PipelineResult(
                pipeline_id=pipeline_id,
                status=PipelineStatus.FAILED,
                error=str(e),
                budget_consumed=budget.to_dict(),
                execution_time_seconds=execution_time,
            )

        finally:
            self._active_contexts.pop(context.context_id, None)

    async def spawn_sub_pipeline(
        self,
        pipeline_id: str,
        parent_context: ExecutionContext,
        task_description: str,
        budget_fraction: float = 0.3,
        context: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Spawn a child pipeline from within an agent."""
        if not parent_context.can_spawn_child():
            raise MaxDepthExceededError(
                parent_context.depth + 1,
                parent_context.budget.max_depth,
            )

        child_context = parent_context.create_child_context(
            pipeline_id=pipeline_id,
            task_id=uuid4(),
            budget_fraction=budget_fraction,
        )

        child_state = AgentState(
            task_id=child_context.task_id,
            description=task_description,
            context={
                "parent_task_id": str(parent_context.task_id),
                "parent_pipeline": parent_context.pipeline_id,
                "spawn_depth": child_context.depth,
                **(context or {}),
            },
        )

        logger.info(
            "spawning_sub_pipeline",
            pipeline_id=pipeline_id,
            parent_pipeline=parent_context.pipeline_id,
            depth=child_context.depth,
        )

        return await self.execute_pipeline(
            pipeline_id=pipeline_id,
            initial_state=child_state,
            budget=child_context.budget,
            parent_context=parent_context,
        )

    def get_active_contexts(self) -> list[ExecutionContext]:
        return list(self._active_contexts.values())

    def get_context(self, context_id: UUID) -> ExecutionContext | None:
        return self._active_contexts.get(context_id)
