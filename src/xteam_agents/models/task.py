"""Task-related models."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Priority(int, Enum):
    """Task priority levels."""

    LOWEST = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class TaskStatus(str, Enum):
    """Status of a task in the system."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMMITTING = "committing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRequest(BaseModel):
    """Request to submit a new task."""

    description: str = Field(..., min_length=1, max_length=10000)
    context: dict[str, Any] = Field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    timeout_seconds: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Result of a completed task."""

    task_id: UUID
    status: TaskStatus
    result: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    error: str | None = None

    # Metrics
    duration_seconds: float | None = None
    iteration_count: int = 0
    token_usage: dict[str, int] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    completed_at: datetime | None = None


class TaskInfo(BaseModel):
    """Information about a task for status queries."""

    id: UUID = Field(default_factory=uuid4)
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    current_node: str | None = None

    # Progress
    iteration_count: int = 0
    subtasks_total: int = 0
    subtasks_completed: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Error info
    error: str | None = None

    def to_result(self, result: str | None = None, artifacts: list[str] | None = None) -> TaskResult:
        """Convert to TaskResult."""
        return TaskResult(
            task_id=self.id,
            status=self.status,
            result=result,
            artifacts=artifacts or [],
            error=self.error,
            iteration_count=self.iteration_count,
            created_at=self.created_at,
            completed_at=self.completed_at,
        )
