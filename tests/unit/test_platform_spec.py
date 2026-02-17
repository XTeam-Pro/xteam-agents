"""Tests for platform spec models."""

import pytest

from xteam_agents.platform.spec import (
    AgentSpec,
    ConditionalEdgeSpec,
    CriticSpec,
    CriticStrategy,
    EdgeSpec,
    MemoryPermissions,
    NodeSpec,
    PairConfig,
    PairSpec,
    PipelineSpec,
    TeamSpec,
)


class TestAgentSpec:
    def test_minimal_creation(self):
        spec = AgentSpec(
            id="test.agent",
            name="TestAgent",
            role="tester",
            persona="You are a test agent.",
        )
        assert spec.id == "test.agent"
        assert spec.name == "TestAgent"
        assert spec.model == "claude-sonnet-4-5"
        assert spec.temperature == 0.5
        assert spec.memory_permissions == MemoryPermissions.EPISODIC_ONLY
        assert spec.can_spawn is False
        assert spec.critic is None
        assert spec.tags == []

    def test_full_creation(self):
        spec = AgentSpec(
            id="adversarial.security",
            name="SecurityAgent",
            version="2.0",
            role="security_blue_team",
            persona="You are a security expert.",
            capabilities=["security_audit", "threat_modeling"],
            tools=["search_knowledge"],
            model="claude-opus-4-5",
            temperature=0.1,
            max_tokens=8192,
            memory_permissions=MemoryPermissions.SHARED_READ,
            can_spawn=True,
            max_spawn_depth=3,
            critic=CriticSpec(
                id="adversarial.security_critic",
                name="SecurityCritic",
                role="security_red_team",
                persona="You are a red team specialist.",
                model="claude-opus-4-5",
                temperature=0.9,
                strategy=CriticStrategy.ADVERSARIAL,
            ),
            pair_config=PairConfig(
                max_iterations=5,
                approval_threshold=9.0,
                min_score_threshold=7.0,
            ),
            tags=["adversarial", "security"],
            source="yaml",
        )
        assert spec.has_critic()
        assert spec.critic.strategy == CriticStrategy.ADVERSARIAL
        assert spec.pair_config.approval_threshold == 9.0

    def test_has_critic(self):
        spec_no_critic = AgentSpec(id="a", name="A", role="r", persona="p")
        assert spec_no_critic.has_critic() is False
        assert spec_no_critic.get_critic_spec() is None

        spec_with = AgentSpec(
            id="b", name="B", role="r", persona="p",
            critic=CriticSpec(id="c", name="C", role="cr", persona="cp"),
        )
        assert spec_with.has_critic() is True
        assert spec_with.get_critic_spec().id == "c"

    def test_serialization(self):
        spec = AgentSpec(
            id="test.ser",
            name="Serializable",
            role="test",
            persona="Test persona",
            capabilities=["cap1"],
            tags=["tag1"],
        )
        data = spec.model_dump()
        assert data["id"] == "test.ser"
        assert data["capabilities"] == ["cap1"]

        restored = AgentSpec(**data)
        assert restored.id == spec.id
        assert restored.capabilities == spec.capabilities


class TestCriticSpec:
    def test_defaults(self):
        critic = CriticSpec(id="c", name="C", role="cr", persona="p")
        assert critic.strategy == CriticStrategy.CONSTRUCTIVE
        assert critic.model == "claude-sonnet-4-5"
        assert critic.temperature == 0.7


class TestPipelineSpec:
    def test_creation(self):
        spec = PipelineSpec(
            id="pipeline.test",
            name="Test Pipeline",
            entry_point="start",
            nodes=[
                NodeSpec(node_name="start", agent_id="agent.a"),
                NodeSpec(node_name="end", agent_id="agent.b"),
            ],
            edges=[
                EdgeSpec(source="start", target="end"),
            ],
        )
        assert len(spec.nodes) == 2
        assert len(spec.edges) == 1
        assert spec.entry_point == "start"

    def test_conditional_edges(self):
        spec = PipelineSpec(
            id="pipeline.cond",
            name="Conditional",
            entry_point="validate",
            nodes=[
                NodeSpec(node_name="validate", agent_id="agent.v"),
                NodeSpec(node_name="commit", agent_id="agent.c"),
                NodeSpec(node_name="plan", agent_id="agent.p"),
            ],
            conditional_edges=[
                ConditionalEdgeSpec(
                    source="validate",
                    condition="validation_router",
                    routes={"commit": "commit", "plan": "plan"},
                ),
            ],
        )
        assert len(spec.conditional_edges) == 1
        assert spec.conditional_edges[0].condition == "validation_router"

    def test_resource_budget(self):
        spec = PipelineSpec(
            id="p.budgeted",
            name="Budgeted",
            entry_point="a",
            resource_budget={
                "max_tokens": 50000,
                "max_time_seconds": 120,
                "max_depth": 2,
            },
        )
        assert spec.resource_budget["max_tokens"] == 50000


class TestTeamSpec:
    def test_creation(self):
        team = TeamSpec(
            id="team.test",
            name="Test Team",
            pipeline="pipeline.adversarial",
            orchestrator="adversarial.orchestrator",
            pairs=[
                PairSpec(agent="adversarial.backend", critic="adversarial.backend_critic"),
                PairSpec(agent="adversarial.frontend", critic="adversarial.frontend_critic"),
            ],
            max_iterations=3,
            approval_threshold=7.5,
        )
        assert len(team.pairs) == 2
        assert team.orchestrator == "adversarial.orchestrator"


class TestNodeSpec:
    def test_config_overrides(self):
        node = NodeSpec(
            node_name="custom",
            agent_id="agent.x",
            config_overrides={"temperature": 0.9},
        )
        assert node.config_overrides["temperature"] == 0.9
