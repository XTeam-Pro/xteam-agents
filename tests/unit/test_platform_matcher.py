"""Tests for CapabilityMatcher."""

from xteam_agents.platform.matcher import CapabilityMatcher, MatchResult
from xteam_agents.platform.registry import AgentRegistry
from xteam_agents.platform.spec import AgentSpec


def _agent(agent_id: str, caps=None, tags=None, name="Agent", role="agent"):
    return AgentSpec(
        id=agent_id,
        name=name,
        role=role,
        persona="Test",
        capabilities=caps or [],
        tags=tags or [],
    )


class TestCapabilityMatcher:
    def test_match_by_capability(self):
        reg = AgentRegistry()
        reg.register(_agent("a1", caps=["security_audit", "testing"]))
        reg.register(_agent("a2", caps=["coding"]))
        reg.register(_agent("a3", caps=["security_audit"]))

        matcher = CapabilityMatcher(reg)
        results = matcher.match(required_capabilities=["security_audit"])

        assert len(results) == 2
        ids = {r.agent.id for r in results}
        assert "a1" in ids
        assert "a3" in ids
        assert "security_audit" in results[0].matched_capabilities

    def test_match_by_tags(self):
        reg = AgentRegistry()
        reg.register(_agent("a1", tags=["backend", "security"]))
        reg.register(_agent("a2", tags=["frontend"]))
        reg.register(_agent("a3", tags=["backend"]))

        matcher = CapabilityMatcher(reg)
        results = matcher.match(required_tags=["backend"])

        assert len(results) == 2
        ids = {r.agent.id for r in results}
        assert "a1" in ids
        assert "a3" in ids

    def test_match_by_keywords(self):
        reg = AgentRegistry()
        reg.register(_agent("a1", name="SecurityAgent", role="security_analyst"))
        reg.register(_agent("a2", name="DataAgent", role="data_engineer"))

        matcher = CapabilityMatcher(reg)
        results = matcher.match(keywords=["security"])

        assert len(results) >= 1
        assert results[0].agent.id == "a1"

    def test_combined_scoring(self):
        reg = AgentRegistry()
        reg.register(_agent("a1", caps=["security"], tags=["security"], name="SecurityAgent"))
        reg.register(_agent("a2", caps=["security"]))

        matcher = CapabilityMatcher(reg)
        results = matcher.match(
            required_capabilities=["security"],
            required_tags=["security"],
            keywords=["security"],
        )

        # a1 should have higher score (matches caps + tags + keywords)
        assert len(results) >= 1
        assert results[0].agent.id == "a1"
        assert results[0].score > results[1].score if len(results) > 1 else True

    def test_min_score_filter(self):
        reg = AgentRegistry()
        reg.register(_agent("a1", caps=["coding"]))
        reg.register(_agent("a2", caps=["testing"]))

        matcher = CapabilityMatcher(reg)
        results = matcher.match(required_capabilities=["security"], min_score=0.1)

        assert len(results) == 0

    def test_empty_criteria_returns_nothing(self):
        reg = AgentRegistry()
        reg.register(_agent("a1"))

        matcher = CapabilityMatcher(reg)
        results = matcher.match()

        assert len(results) == 0

    def test_sorted_by_score(self):
        reg = AgentRegistry()
        reg.register(_agent("a1", caps=["security"]))
        reg.register(_agent("a2", caps=["security", "testing"]))

        matcher = CapabilityMatcher(reg)
        results = matcher.match(required_capabilities=["security", "testing"])

        # a2 has both capabilities, should score higher
        assert results[0].agent.id == "a2"
