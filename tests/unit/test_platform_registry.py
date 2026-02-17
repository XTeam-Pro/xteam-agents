"""Tests for platform registries."""

import pytest

from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry, TeamRegistry
from xteam_agents.platform.spec import (
    AgentSpec,
    CriticSpec,
    CriticStrategy,
    EdgeSpec,
    NodeSpec,
    PairSpec,
    PipelineSpec,
    TeamSpec,
)


@pytest.fixture
def agent_registry():
    return AgentRegistry()


@pytest.fixture
def pipeline_registry():
    return PipelineRegistry()


@pytest.fixture
def team_registry():
    return TeamRegistry()


def _make_agent(
    agent_id: str,
    name: str = "Agent",
    role: str = "agent",
    capabilities: list[str] | None = None,
    tags: list[str] | None = None,
    has_critic: bool = False,
) -> AgentSpec:
    critic = None
    if has_critic:
        critic = CriticSpec(
            id=f"{agent_id}_critic",
            name=f"{name}Critic",
            role=f"{role}_critic",
            persona="Critic persona",
        )
    return AgentSpec(
        id=agent_id,
        name=name,
        role=role,
        persona="Test persona",
        capabilities=capabilities or [],
        tags=tags or [],
        critic=critic,
    )


class TestAgentRegistry:
    def test_register_and_get(self, agent_registry):
        spec = _make_agent("test.a", "AgentA")
        agent_registry.register(spec)
        assert agent_registry.get("test.a").name == "AgentA"

    def test_get_not_found(self, agent_registry):
        with pytest.raises(KeyError, match="Agent spec not found"):
            agent_registry.get("nonexistent")

    def test_get_or_none(self, agent_registry):
        assert agent_registry.get_or_none("missing") is None
        agent_registry.register(_make_agent("found"))
        assert agent_registry.get_or_none("found") is not None

    def test_find_by_capability(self, agent_registry):
        agent_registry.register(_make_agent("a1", capabilities=["security_audit", "testing"]))
        agent_registry.register(_make_agent("a2", capabilities=["testing"]))
        agent_registry.register(_make_agent("a3", capabilities=["coding"]))

        results = agent_registry.find_by_capability("testing")
        assert len(results) == 2
        ids = {r.id for r in results}
        assert "a1" in ids
        assert "a2" in ids

    def test_find_by_role(self, agent_registry):
        agent_registry.register(_make_agent("a1", role="analyst"))
        agent_registry.register(_make_agent("a2", role="architect"))
        agent_registry.register(_make_agent("a3", role="analyst"))

        results = agent_registry.find_by_role("analyst")
        assert len(results) == 2

    def test_find_by_tags_any(self, agent_registry):
        agent_registry.register(_make_agent("a1", tags=["adversarial", "security"]))
        agent_registry.register(_make_agent("a2", tags=["cognitive", "core"]))
        agent_registry.register(_make_agent("a3", tags=["adversarial", "backend"]))

        results = agent_registry.find_by_tags(["adversarial"])
        assert len(results) == 2

    def test_find_by_tags_all(self, agent_registry):
        agent_registry.register(_make_agent("a1", tags=["adversarial", "security"]))
        agent_registry.register(_make_agent("a2", tags=["adversarial", "backend"]))

        results = agent_registry.find_by_tags(["adversarial", "security"], match_all=True)
        assert len(results) == 1
        assert results[0].id == "a1"

    def test_list_all(self, agent_registry):
        for i in range(5):
            agent_registry.register(_make_agent(f"a{i}"))
        assert len(agent_registry.list_all()) == 5

    def test_count(self, agent_registry):
        assert agent_registry.count() == 0
        agent_registry.register(_make_agent("a1"))
        assert agent_registry.count() == 1

    def test_has(self, agent_registry):
        assert agent_registry.has("a1") is False
        agent_registry.register(_make_agent("a1"))
        assert agent_registry.has("a1") is True

    def test_unregister(self, agent_registry):
        agent_registry.register(_make_agent("a1"))
        assert agent_registry.unregister("a1") is True
        assert agent_registry.has("a1") is False
        assert agent_registry.unregister("a1") is False

    def test_clear(self, agent_registry):
        for i in range(3):
            agent_registry.register(_make_agent(f"a{i}"))
        agent_registry.clear()
        assert agent_registry.count() == 0

    def test_overwrite(self, agent_registry):
        agent_registry.register(_make_agent("a1", name="First"))
        agent_registry.register(_make_agent("a1", name="Second"))
        assert agent_registry.get("a1").name == "Second"


class TestPipelineRegistry:
    def test_register_and_get(self, pipeline_registry):
        spec = PipelineSpec(
            id="pipeline.test",
            name="Test",
            entry_point="start",
            nodes=[NodeSpec(node_name="start", agent_id="a.1")],
        )
        pipeline_registry.register(spec)
        assert pipeline_registry.get("pipeline.test").name == "Test"

    def test_get_not_found(self, pipeline_registry):
        with pytest.raises(KeyError):
            pipeline_registry.get("missing")

    def test_has(self, pipeline_registry):
        assert pipeline_registry.has("p") is False
        pipeline_registry.register(PipelineSpec(id="p", name="P", entry_point="s"))
        assert pipeline_registry.has("p") is True


class TestTeamRegistry:
    def test_register_and_get(self, team_registry):
        spec = TeamSpec(
            id="team.test",
            name="Test Team",
            pipeline="pipeline.test",
        )
        team_registry.register(spec)
        assert team_registry.get("team.test").name == "Test Team"

    def test_list_all(self, team_registry):
        team_registry.register(TeamSpec(id="t1", name="T1", pipeline="p"))
        team_registry.register(TeamSpec(id="t2", name="T2", pipeline="p"))
        assert team_registry.count() == 2
