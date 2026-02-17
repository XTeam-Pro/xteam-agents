"""Tests for platform errors."""

from xteam_agents.platform.errors import (
    AgentSpecNotFoundError,
    BudgetExhaustedError,
    ConditionNotFoundError,
    MaxDepthExceededError,
    PipelineSpecNotFoundError,
    PlatformError,
    SpawnNotAllowedError,
)


class TestPlatformErrors:
    def test_budget_exhausted(self):
        e = BudgetExhaustedError({"tokens_used": 1000})
        assert "budget exhausted" in str(e).lower()
        assert e.budget_info == {"tokens_used": 1000}

    def test_budget_exhausted_defaults(self):
        e = BudgetExhaustedError()
        assert e.budget_info == {}

    def test_max_depth_exceeded(self):
        e = MaxDepthExceededError(4, 3)
        assert e.current_depth == 4
        assert e.max_depth == 3
        assert "4 > 3" in str(e)

    def test_agent_spec_not_found(self):
        e = AgentSpecNotFoundError("cognitive.analyst")
        assert e.agent_id == "cognitive.analyst"
        assert "cognitive.analyst" in str(e)

    def test_pipeline_spec_not_found(self):
        e = PipelineSpecNotFoundError("pipeline.missing")
        assert e.pipeline_id == "pipeline.missing"

    def test_spawn_not_allowed(self):
        e = SpawnNotAllowedError("agent.x")
        assert e.agent_id == "agent.x"
        assert "not allowed" in str(e).lower()

    def test_condition_not_found(self):
        e = ConditionNotFoundError("missing_cond")
        assert e.condition_name == "missing_cond"

    def test_inheritance(self):
        assert issubclass(BudgetExhaustedError, PlatformError)
        assert issubclass(MaxDepthExceededError, PlatformError)
        assert issubclass(AgentSpecNotFoundError, PlatformError)
        assert issubclass(PlatformError, Exception)
