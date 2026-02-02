"""LangGraph agent state definitions."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any
from uuid import UUID, uuid4

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


def merge_messages(left: list[BaseMessage], right: list[BaseMessage]) -> list[BaseMessage]:
    """Merge message lists by appending."""
    return left + right


def merge_artifacts(left: list[str], right: list[str]) -> list[str]:
    """Merge artifact lists by appending unique items."""
    seen = set(left)
    result = list(left)
    for item in right:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


class SubTaskStatus(str, Enum):
    """Status of a subtask."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SubTask(BaseModel):
    """A subtask created during planning."""

    id: UUID = Field(default_factory=uuid4)
    description: str
    status: SubTaskStatus = SubTaskStatus.PENDING
    result: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def mark_completed(self, result: str) -> "SubTask":
        """Mark subtask as completed."""
        return self.model_copy(
            update={
                "status": SubTaskStatus.COMPLETED,
                "result": result,
                "completed_at": datetime.utcnow(),
            }
        )

    def mark_failed(self, error: str) -> "SubTask":
        """Mark subtask as failed."""
        return self.model_copy(
            update={
                "status": SubTaskStatus.FAILED,
                "error": error,
                "completed_at": datetime.utcnow(),
            }
        )


class AgentState(BaseModel):
    """
    LangGraph state for the cognitive agent system.

    This state flows through all nodes in the graph and contains
    both the task context and intermediate results.
    """

    # Core identifiers
    task_id: UUID
    session_id: UUID = Field(default_factory=uuid4)

    # Original request
    description: str
    context: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=5)

    # Message history (for LLM context)
    messages: Annotated[list[BaseMessage], merge_messages] = Field(default_factory=list)

    # Planning outputs
    analysis: str | None = None
    plan: str | None = None
    subtasks: list[SubTask] = Field(default_factory=list)

    # Execution outputs
    execution_result: str | None = None
    artifacts: Annotated[list[str], merge_artifacts] = Field(default_factory=list)

    # Validation state
    is_validated: bool = False
    validation_feedback: str | None = None
    validation_attempts: int = 0

    # Control flow
    current_node: str = "analyze"
    iteration_count: int = 0
    max_iterations: int = 10
    should_replan: bool = False

    # Error handling
    error: str | None = None
    is_failed: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def increment_iteration(self) -> "AgentState":
        """Increment iteration count and update timestamp."""
        return self.model_copy(
            update={
                "iteration_count": self.iteration_count + 1,
                "updated_at": datetime.utcnow(),
            }
        )

    def has_exceeded_max_iterations(self) -> bool:
        """Check if max iterations exceeded."""
        return self.iteration_count >= self.max_iterations

    def get_pending_subtasks(self) -> list[SubTask]:
        """Get all pending subtasks."""
        return [st for st in self.subtasks if st.status == SubTaskStatus.PENDING]

    def get_completed_subtasks(self) -> list[SubTask]:
        """Get all completed subtasks."""
        return [st for st in self.subtasks if st.status == SubTaskStatus.COMPLETED]

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
