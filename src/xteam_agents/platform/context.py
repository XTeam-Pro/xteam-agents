"""Execution context for tracking pipeline runs and results.

Provides hierarchical context management for recursive pipeline execution.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from xteam_agents.platform.budget import ResourceBudget


class PipelineStatus(str, Enum):
    """Status of a pipeline execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    DEPTH_EXCEEDED = "depth_exceeded"
    CANCELLED = "cancelled"


class PipelineResult(BaseModel):
    """Result of a pipeline execution."""

    pipeline_id: str
    status: PipelineStatus
    result: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    error: str | None = None
    budget_consumed: dict[str, Any] = Field(default_factory=dict)
    child_results: list[PipelineResult] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def summary(self) -> str:
        if self.status == PipelineStatus.COMPLETED:
            return self.result[:500] if self.result else "Completed successfully"
        elif self.status == PipelineStatus.FAILED:
            return f"Failed: {self.error or 'Unknown error'}"
        elif self.status == PipelineStatus.BUDGET_EXHAUSTED:
            return f"Budget exhausted: {self.budget_consumed}"
        return f"Status: {self.status.value}"


class ExecutionContext(BaseModel):
    """Hierarchical execution context for pipeline runs."""

    context_id: UUID = Field(default_factory=uuid4)
    pipeline_id: str
    task_id: UUID

    # Hierarchy
    depth: int = 0
    parent_context_id: UUID | None = None
    child_context_ids: list[UUID] = Field(default_factory=list)

    # Budget
    budget: ResourceBudget

    # Tracking
    status: PipelineStatus = PipelineStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    nodes_visited: list[str] = Field(default_factory=list)

    def start(self) -> None:
        self.status = PipelineStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, status: PipelineStatus = PipelineStatus.COMPLETED) -> None:
        self.status = status
        self.completed_at = datetime.utcnow()

    def visit_node(self, node_name: str) -> None:
        self.nodes_visited.append(node_name)

    def can_spawn_child(self) -> bool:
        return self.depth < self.budget.max_depth and not self.budget.is_exhausted()

    def create_child_context(
        self,
        pipeline_id: str,
        task_id: UUID,
        budget_fraction: float = 0.3,
    ) -> ExecutionContext:
        child_budget = self.budget.allocate_child(budget_fraction)
        child = ExecutionContext(
            pipeline_id=pipeline_id,
            task_id=task_id,
            depth=self.depth + 1,
            parent_context_id=self.context_id,
            budget=child_budget,
        )
        self.child_context_ids.append(child.context_id)
        return child

    def execution_time(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
