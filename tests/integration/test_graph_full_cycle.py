"""Integration tests for the full graph cycle."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from xteam_agents.config import Settings
from xteam_agents.models.state import AgentState
from xteam_agents.models.task import TaskRequest, Priority


@pytest.fixture
def integration_settings():
    """Create settings for integration tests."""
    return Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        redis_url="redis://localhost:6379/0",
        qdrant_url="http://localhost:6333",
        neo4j_url="bolt://localhost:7687",
        neo4j_password="password",
        postgres_url="postgresql://postgres:password@localhost:5432/xteam",
    )


class TestGraphCycleSimulated:
    """Tests for graph cycle with mocked components."""

    @pytest.mark.asyncio
    async def test_state_progression(self):
        """Test that state progresses through expected nodes."""
        task_id = uuid4()

        # Create initial state
        state = AgentState(
            task_id=task_id,
            description="Test task",
            context={},
            priority=3,
        )

        assert state.current_node == "analyze"
        assert state.is_validated is False
        assert state.iteration_count == 0

        # Simulate analyze → plan
        state = state.model_copy(update={
            "analysis": "Task analyzed",
            "current_node": "plan",
        })
        assert state.current_node == "plan"

        # Simulate plan → execute
        state = state.model_copy(update={
            "plan": "Plan created",
            "current_node": "execute",
        })
        assert state.current_node == "execute"

        # Simulate execute → validate
        state = state.model_copy(update={
            "execution_result": "Executed successfully",
            "current_node": "validate",
        })
        assert state.current_node == "validate"

        # Simulate validate → commit (approved)
        state = state.model_copy(update={
            "is_validated": True,
            "current_node": "commit",
        })
        assert state.is_validated is True

    @pytest.mark.asyncio
    async def test_replan_cycle(self):
        """Test that replan cycle works correctly."""
        task_id = uuid4()

        state = AgentState(
            task_id=task_id,
            description="Test task",
            iteration_count=0,
        )

        # First iteration
        state = state.model_copy(update={
            "analysis": "Analyzed",
            "plan": "Plan v1",
            "execution_result": "Failed validation",
            "is_validated": False,
            "should_replan": True,
            "validation_feedback": "Need to fix X",
            "iteration_count": 1,
        })

        # Should route back to plan
        from xteam_agents.graph.edges import route_after_validation
        route = route_after_validation(state)
        assert route == "plan"

        # Second iteration (after replan)
        state = state.model_copy(update={
            "plan": "Plan v2",
            "execution_result": "Success",
            "is_validated": True,
            "should_replan": False,
            "iteration_count": 2,
        })

        route = route_after_validation(state)
        assert route == "commit"

    @pytest.mark.asyncio
    async def test_max_iterations_failure(self):
        """Test that max iterations causes failure."""
        task_id = uuid4()

        state = AgentState(
            task_id=task_id,
            description="Test task",
            iteration_count=10,
            max_iterations=10,
            should_replan=True,  # Would normally replan
        )

        from xteam_agents.graph.edges import route_after_validation
        route = route_after_validation(state)

        # Should fail instead of replanning
        assert route == "fail"


class TestTaskRequestValidation:
    """Tests for task request validation."""

    def test_valid_task_request(self):
        """Test creating a valid task request."""
        request = TaskRequest(
            description="Implement a function",
            context={"language": "python"},
            priority=Priority.HIGH,
        )

        assert request.description == "Implement a function"
        assert request.priority == Priority.HIGH

    def test_task_request_default_priority(self):
        """Test default priority is MEDIUM."""
        request = TaskRequest(description="Test task")
        assert request.priority == Priority.MEDIUM

    def test_task_request_minimum_description(self):
        """Test minimum description length."""
        request = TaskRequest(description="x")
        assert len(request.description) >= 1

    def test_task_request_empty_description_fails(self):
        """Test that empty description fails validation."""
        with pytest.raises(ValueError):
            TaskRequest(description="")
