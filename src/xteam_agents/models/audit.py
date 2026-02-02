"""Audit logging models."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Task lifecycle
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"

    # Graph transitions
    NODE_ENTERED = "node_entered"
    NODE_EXITED = "node_exited"
    EDGE_TRAVERSED = "edge_traversed"

    # Memory operations
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    MEMORY_VALIDATED = "memory_validated"

    # Action execution
    ACTION_REQUESTED = "action_requested"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"

    # Validation
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    REPLAN_TRIGGERED = "replan_triggered"

    # System events
    SYSTEM_ERROR = "system_error"
    CAPABILITY_REGISTERED = "capability_registered"
    CONFIG_CHANGED = "config_changed"


class AuditEntry(BaseModel):
    """
    An immutable audit log entry.

    Audit entries are append-only and cannot be modified or deleted.
    They provide a complete trail of all system activities.
    """

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID | None = None
    session_id: UUID | None = None

    # Event classification
    event_type: AuditEventType
    agent_name: str | None = None
    node_name: str | None = None

    # Event details
    description: str
    data: dict[str, Any] = Field(default_factory=dict)

    # Context
    context: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: UUID | None = None  # For linking related events

    # Optional metrics
    duration_ms: int | None = None
    token_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id) if self.task_id else None,
            "session_id": str(self.session_id) if self.session_id else None,
            "event_type": self.event_type.value,
            "agent_name": self.agent_name,
            "node_name": self.node_name,
            "description": self.description,
            "data": self.data,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "duration_ms": self.duration_ms,
            "token_count": self.token_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]),
            task_id=UUID(data["task_id"]) if data.get("task_id") else None,
            session_id=UUID(data["session_id"]) if data.get("session_id") else None,
            event_type=AuditEventType(data["event_type"]),
            agent_name=data.get("agent_name"),
            node_name=data.get("node_name"),
            description=data["description"],
            data=data.get("data", {}),
            context=data.get("context", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=UUID(data["correlation_id"]) if data.get("correlation_id") else None,
            duration_ms=data.get("duration_ms"),
            token_count=data.get("token_count"),
        )
