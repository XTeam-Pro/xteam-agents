"""Pytest configuration and fixtures."""

import os
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage

from xteam_agents.config import Settings
from xteam_agents.models.action import ActionRequest, Capability, HandlerType
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState, SubTask
from xteam_agents.models.task import Priority, TaskRequest


# Set test environment variables
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("NEO4J_URL", "bolt://localhost:7687")
os.environ.setdefault("POSTGRES_URL", "postgresql://postgres:password@localhost:5432/xteam")


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        redis_url="redis://localhost:6379/0",
        qdrant_url="http://localhost:6333",
        neo4j_url="bolt://localhost:7687",
        postgres_url="postgresql://postgres:password@localhost:5432/xteam",
    )


@pytest.fixture
def task_id():
    """Generate a test task ID."""
    return uuid4()


@pytest.fixture
def session_id():
    """Generate a test session ID."""
    return uuid4()


@pytest.fixture
def task_request() -> TaskRequest:
    """Create a sample task request."""
    return TaskRequest(
        description="Implement a function to calculate factorial",
        context={"language": "python", "test_required": True},
        priority=Priority.HIGH,
    )


@pytest.fixture
def agent_state(task_id, session_id) -> AgentState:
    """Create a sample agent state."""
    return AgentState(
        task_id=task_id,
        session_id=session_id,
        description="Test task description",
        context={"test": True},
        priority=3,
        messages=[HumanMessage(content="Start task")],
    )


@pytest.fixture
def subtask(task_id) -> SubTask:
    """Create a sample subtask."""
    return SubTask(
        description="Write unit tests",
    )


@pytest.fixture
def memory_artifact(task_id, session_id) -> MemoryArtifact:
    """Create a sample memory artifact."""
    return MemoryArtifact(
        task_id=task_id,
        session_id=session_id,
        content="Important finding from analysis",
        content_type="text",
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.SHARED,
        created_by="analyst",
    )


@pytest.fixture
def capability() -> Capability:
    """Create a sample capability."""
    return Capability(
        name="execute_python",
        description="Execute Python code in a sandbox",
        handler_type=HandlerType.CODE,
        config={"sandbox": True, "timeout": 30},
    )


@pytest.fixture
def action_request(task_id) -> ActionRequest:
    """Create a sample action request."""
    return ActionRequest(
        task_id=task_id,
        capability_name="execute_python",
        parameters={"code": "print('hello')"},
        requested_by="worker",
    )


@pytest.fixture
def audit_entry(task_id, session_id) -> AuditEntry:
    """Create a sample audit entry."""
    return AuditEntry(
        task_id=task_id,
        session_id=session_id,
        event_type=AuditEventType.TASK_CREATED,
        agent_name="system",
        description="Task created",
        data={"priority": 3},
    )
