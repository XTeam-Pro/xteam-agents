"""Unit tests for graph node routing."""

from uuid import uuid4

import pytest

from xteam_agents.graph.edges import route_after_validation
from xteam_agents.models.state import AgentState


@pytest.fixture
def base_state():
    """Create a base agent state for testing."""
    return AgentState(
        task_id=uuid4(),
        description="Test task",
        is_validated=False,
        should_replan=False,
        is_failed=False,
        iteration_count=0,
        max_iterations=10,
    )


class TestRouteAfterValidation:
    """Tests for the route_after_validation edge function."""

    def test_route_to_commit_when_validated(self, base_state):
        """Test routing to commit when task is validated."""
        state = base_state.model_copy(update={"is_validated": True})
        result = route_after_validation(state)
        assert result == "commit"

    def test_route_to_plan_when_needs_replan(self, base_state):
        """Test routing to plan when replanning is needed."""
        state = base_state.model_copy(update={
            "is_validated": False,
            "should_replan": True,
        })
        result = route_after_validation(state)
        assert result == "plan"

    def test_route_to_fail_when_failed(self, base_state):
        """Test routing to fail when task has failed."""
        state = base_state.model_copy(update={
            "is_failed": True,
        })
        result = route_after_validation(state)
        assert result == "fail"

    def test_route_to_fail_when_max_iterations_exceeded(self, base_state):
        """Test routing to fail when max iterations exceeded."""
        state = base_state.model_copy(update={
            "iteration_count": 10,  # Equal to max_iterations
            "max_iterations": 10,
        })
        result = route_after_validation(state)
        assert result == "fail"

    def test_failed_takes_precedence_over_validated(self, base_state):
        """Test that failed status takes precedence."""
        state = base_state.model_copy(update={
            "is_validated": True,
            "is_failed": True,
        })
        result = route_after_validation(state)
        assert result == "fail"

    def test_failed_takes_precedence_over_replan(self, base_state):
        """Test that failed status takes precedence over replan."""
        state = base_state.model_copy(update={
            "should_replan": True,
            "is_failed": True,
        })
        result = route_after_validation(state)
        assert result == "fail"

    def test_max_iterations_takes_precedence_over_replan(self, base_state):
        """Test that max iterations takes precedence over replan."""
        state = base_state.model_copy(update={
            "should_replan": True,
            "iteration_count": 10,
            "max_iterations": 10,
        })
        result = route_after_validation(state)
        assert result == "fail"


class TestAgentStateHelpers:
    """Tests for AgentState helper methods."""

    def test_has_exceeded_max_iterations_false(self, base_state):
        """Test max iterations check when not exceeded."""
        state = base_state.model_copy(update={
            "iteration_count": 5,
            "max_iterations": 10,
        })
        assert state.has_exceeded_max_iterations() is False

    def test_has_exceeded_max_iterations_true(self, base_state):
        """Test max iterations check when exceeded."""
        state = base_state.model_copy(update={
            "iteration_count": 10,
            "max_iterations": 10,
        })
        assert state.has_exceeded_max_iterations() is True

    def test_has_exceeded_max_iterations_over(self, base_state):
        """Test max iterations check when over."""
        state = base_state.model_copy(update={
            "iteration_count": 15,
            "max_iterations": 10,
        })
        assert state.has_exceeded_max_iterations() is True

    def test_increment_iteration(self, base_state):
        """Test incrementing iteration count."""
        original = base_state.iteration_count
        new_state = base_state.increment_iteration()

        assert new_state.iteration_count == original + 1
        assert new_state.updated_at > base_state.updated_at
        # Original should be unchanged (immutable)
        assert base_state.iteration_count == original
