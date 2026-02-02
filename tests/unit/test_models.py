"""Unit tests for Pydantic models."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from xteam_agents.models.action import (
    ActionRequest,
    ActionResult,
    Capability,
    HandlerType,
)
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import (
    MemoryArtifact,
    MemoryQuery,
    MemoryScope,
    MemoryType,
)
from xteam_agents.models.observation import Observation, ObservationSeverity, ObservationType
from xteam_agents.models.state import AgentState, SubTask, SubTaskStatus
from xteam_agents.models.task import Priority, TaskInfo, TaskRequest, TaskResult, TaskStatus


class TestAgentState:
    """Tests for AgentState model."""

    def test_create_minimal(self):
        """Test creating agent state with minimal fields."""
        task_id = uuid4()
        state = AgentState(task_id=task_id, description="Test task")

        assert state.task_id == task_id
        assert state.description == "Test task"
        assert state.priority == 1
        assert state.messages == []
        assert state.is_validated is False
        assert state.iteration_count == 0

    def test_increment_iteration(self, agent_state):
        """Test iteration increment."""
        original_count = agent_state.iteration_count
        new_state = agent_state.increment_iteration()

        assert new_state.iteration_count == original_count + 1
        assert new_state.updated_at > agent_state.updated_at

    def test_max_iterations_exceeded(self, agent_state):
        """Test max iterations check."""
        assert agent_state.has_exceeded_max_iterations() is False

        # Set iteration to max
        state = agent_state.model_copy(update={"iteration_count": 10})
        assert state.has_exceeded_max_iterations() is True

    def test_subtask_filtering(self, agent_state):
        """Test filtering subtasks by status."""
        subtasks = [
            SubTask(description="Task 1", status=SubTaskStatus.PENDING),
            SubTask(description="Task 2", status=SubTaskStatus.COMPLETED),
            SubTask(description="Task 3", status=SubTaskStatus.PENDING),
        ]
        state = agent_state.model_copy(update={"subtasks": subtasks})

        pending = state.get_pending_subtasks()
        completed = state.get_completed_subtasks()

        assert len(pending) == 2
        assert len(completed) == 1

    def test_message_merge(self):
        """Test message list merging."""
        task_id = uuid4()
        state1 = AgentState(
            task_id=task_id,
            description="Test",
            messages=[HumanMessage(content="Hello")],
        )

        # Simulate update with new messages
        new_messages = [AIMessage(content="Hi there")]
        merged = state1.messages + new_messages

        assert len(merged) == 2
        assert merged[0].content == "Hello"
        assert merged[1].content == "Hi there"


class TestSubTask:
    """Tests for SubTask model."""

    def test_create(self, subtask):
        """Test creating a subtask."""
        assert subtask.description == "Write unit tests"
        assert subtask.status == SubTaskStatus.PENDING
        assert subtask.result is None

    def test_mark_completed(self, subtask):
        """Test marking subtask as completed."""
        completed = subtask.mark_completed("Tests written")

        assert completed.status == SubTaskStatus.COMPLETED
        assert completed.result == "Tests written"
        assert completed.completed_at is not None

    def test_mark_failed(self, subtask):
        """Test marking subtask as failed."""
        failed = subtask.mark_failed("Timeout")

        assert failed.status == SubTaskStatus.FAILED
        assert failed.error == "Timeout"
        assert failed.completed_at is not None


class TestMemoryArtifact:
    """Tests for MemoryArtifact model."""

    def test_create(self, memory_artifact):
        """Test creating a memory artifact."""
        assert memory_artifact.memory_type == MemoryType.SEMANTIC
        assert memory_artifact.scope == MemoryScope.SHARED
        assert memory_artifact.is_validated is False

    def test_validate_artifact(self, memory_artifact):
        """Test validating an artifact."""
        validated = memory_artifact.validate_artifact("reviewer")

        assert validated.is_validated is True
        assert validated.validated_by == "reviewer"
        assert validated.validated_at is not None

    def test_can_write_to_shared_private(self, task_id, session_id):
        """Test private artifacts can always write."""
        artifact = MemoryArtifact(
            task_id=task_id,
            session_id=session_id,
            content="Private note",
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.PRIVATE,
            created_by="agent",
        )

        assert artifact.can_write_to_shared() is True

    def test_can_write_to_shared_unvalidated(self, memory_artifact):
        """Test unvalidated shared artifacts cannot write."""
        assert memory_artifact.can_write_to_shared() is False

    def test_can_write_to_shared_validated(self, memory_artifact):
        """Test validated shared artifacts can write."""
        validated = memory_artifact.validate_artifact("reviewer")
        assert validated.can_write_to_shared() is True


class TestMemoryQuery:
    """Tests for MemoryQuery model."""

    def test_create_minimal(self):
        """Test creating a minimal query."""
        query = MemoryQuery(query_text="Find relevant docs")

        assert query.query_text == "Find relevant docs"
        assert query.limit == 10
        assert query.use_semantic_search is True

    def test_create_full(self, task_id):
        """Test creating a full query."""
        query = MemoryQuery(
            query_text="Find code examples",
            memory_types=[MemoryType.SEMANTIC, MemoryType.PROCEDURAL],
            scope=MemoryScope.SHARED,
            task_id=task_id,
            limit=20,
            similarity_threshold=0.8,
        )

        assert len(query.memory_types) == 2
        assert query.scope == MemoryScope.SHARED
        assert query.limit == 20


class TestTaskModels:
    """Tests for task-related models."""

    def test_task_request(self, task_request):
        """Test creating a task request."""
        assert task_request.description == "Implement a function to calculate factorial"
        assert task_request.priority == Priority.HIGH
        assert task_request.context["language"] == "python"

    def test_task_info(self, task_id):
        """Test creating task info."""
        info = TaskInfo(
            id=task_id,
            description="Test task",
            status=TaskStatus.EXECUTING,
            subtasks_total=5,
            subtasks_completed=2,
        )

        assert info.status == TaskStatus.EXECUTING
        assert info.subtasks_total == 5

    def test_task_info_to_result(self, task_id):
        """Test converting task info to result."""
        info = TaskInfo(
            id=task_id,
            description="Test task",
            status=TaskStatus.COMPLETED,
        )

        result = info.to_result(result="Done", artifacts=["file1.py"])

        assert result.task_id == task_id
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "Done"
        assert "file1.py" in result.artifacts


class TestActionModels:
    """Tests for action-related models."""

    def test_capability(self, capability):
        """Test creating a capability."""
        assert capability.name == "execute_python"
        assert capability.handler_type == HandlerType.CODE
        assert capability.enabled is True

    def test_action_request(self, action_request):
        """Test creating an action request."""
        assert action_request.capability_name == "execute_python"
        assert action_request.parameters["code"] == "print('hello')"

    def test_action_result(self, task_id):
        """Test creating an action result."""
        request_id = uuid4()
        result = ActionResult(
            request_id=request_id,
            task_id=task_id,
            capability_name="execute_python",
            success=True,
            output="hello\n",
            duration_seconds=0.5,
            exit_code=0,
            stdout="hello\n",
        )

        assert result.success is True
        assert result.exit_code == 0


class TestObservation:
    """Tests for Observation model."""

    def test_create(self, task_id):
        """Test creating an observation."""
        obs = Observation(
            task_id=task_id,
            observation_type=ObservationType.TASK_STATE,
            source="task_state_sensor",
            title="Task Started",
            description="Task execution has begun",
        )

        assert obs.observation_type == ObservationType.TASK_STATE
        assert obs.severity == ObservationSeverity.INFO

    def test_is_expired(self, task_id):
        """Test expiration check."""
        # Not expired
        obs1 = Observation(
            task_id=task_id,
            observation_type=ObservationType.TIMEOUT,
            source="timeout_sensor",
            title="Timeout Warning",
            description="Task approaching timeout",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert obs1.is_expired() is False

        # Expired
        obs2 = Observation(
            task_id=task_id,
            observation_type=ObservationType.TIMEOUT,
            source="timeout_sensor",
            title="Timeout",
            description="Task timed out",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert obs2.is_expired() is True

    def test_to_message(self, task_id):
        """Test converting to message."""
        obs = Observation(
            task_id=task_id,
            observation_type=ObservationType.ERROR,
            severity=ObservationSeverity.ERROR,
            source="error_sensor",
            title="Execution Failed",
            description="The code raised an exception",
            data={"error_type": "ValueError"},
        )

        message = obs.to_message()
        assert "[ERROR]" in message
        assert "Execution Failed" in message


class TestAuditEntry:
    """Tests for AuditEntry model."""

    def test_create(self, audit_entry):
        """Test creating an audit entry."""
        assert audit_entry.event_type == AuditEventType.TASK_CREATED
        assert audit_entry.agent_name == "system"

    def test_to_dict(self, audit_entry):
        """Test converting to dictionary."""
        d = audit_entry.to_dict()

        assert "id" in d
        assert d["event_type"] == "task_created"
        assert d["agent_name"] == "system"
        assert "timestamp" in d

    def test_from_dict(self, audit_entry):
        """Test creating from dictionary."""
        d = audit_entry.to_dict()
        restored = AuditEntry.from_dict(d)

        assert restored.id == audit_entry.id
        assert restored.event_type == audit_entry.event_type
        assert restored.description == audit_entry.description
