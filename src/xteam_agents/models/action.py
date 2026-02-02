"""Action-related models."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class HandlerType(str, Enum):
    """Types of action handlers."""

    CODE = "code"  # Code execution
    HTTP = "http"  # HTTP requests
    SHELL = "shell"  # Shell commands
    CI = "ci"  # CI/n8n integration


class Capability(BaseModel):
    """A registered capability that can be invoked."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    handler_type: HandlerType
    enabled: bool = True

    # Configuration
    config: dict[str, Any] = Field(default_factory=dict)

    # Security
    requires_approval: bool = False
    allowed_contexts: list[str] = Field(default_factory=list)  # Empty = all contexts

    # Rate limiting
    max_calls_per_minute: int | None = None
    timeout_seconds: int = Field(default=30, ge=1)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = None


class ActionRequest(BaseModel):
    """Request to execute an action."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    capability_name: str

    # Input
    parameters: dict[str, Any] = Field(default_factory=dict)
    input_data: str | None = None

    # Context
    context: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = None

    # Metadata
    requested_by: str  # Agent name
    requested_at: datetime = Field(default_factory=datetime.utcnow)


class ActionResult(BaseModel):
    """Result of an executed action."""

    request_id: UUID
    task_id: UUID
    capability_name: str

    # Outcome
    success: bool
    output: str | None = None
    error: str | None = None

    # Metadata
    duration_seconds: float
    executed_at: datetime = Field(default_factory=datetime.utcnow)

    # For shell/code execution
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None

    # For HTTP requests
    status_code: int | None = None
    response_body: str | None = None
    response_headers: dict[str, str] | None = None
