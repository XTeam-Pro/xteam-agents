"""Observation models for the perception system."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ObservationType(str, Enum):
    """Types of observations from sensors."""

    # System sensors
    TASK_STATE = "task_state"
    ERROR = "error"
    BUDGET = "budget"

    # Environment sensors
    API_RESPONSE = "api_response"
    CI_STATUS = "ci_status"
    GIT_EVENT = "git_event"
    USER_FEEDBACK = "user_feedback"

    # Temporal sensors
    DEADLINE = "deadline"
    TIMEOUT = "timeout"
    CRON = "cron"


class ObservationSeverity(str, Enum):
    """Severity level of an observation."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Observation(BaseModel):
    """
    An observation from the perception system.

    Observations are produced by sensors and consumed by agents
    to inform their decision-making process.
    """

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID | None = None
    session_id: UUID | None = None

    # Classification
    observation_type: ObservationType
    severity: ObservationSeverity = ObservationSeverity.INFO
    source: str  # Sensor name that produced this

    # Content
    title: str
    description: str
    data: dict[str, Any] = Field(default_factory=dict)

    # Context
    context: dict[str, Any] = Field(default_factory=dict)

    # Flags
    requires_immediate_action: bool = False
    is_blocking: bool = False

    # Timestamps
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if observation has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_message(self) -> str:
        """Convert observation to a message string for agents."""
        parts = [f"[{self.severity.value.upper()}] {self.title}"]
        if self.description:
            parts.append(self.description)
        if self.data:
            parts.append(f"Data: {self.data}")
        return "\n".join(parts)
