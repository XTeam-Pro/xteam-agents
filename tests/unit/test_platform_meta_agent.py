"""Tests for MetaAgent and TopologyOptimizer."""

from xteam_agents.platform.meta_agent import (
    AgentPerformanceMetrics,
    MetaAgent,
    OptimizationSuggestion,
    PipelinePerformanceMetrics,
)
from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry
from xteam_agents.platform.spec import AgentSpec
from xteam_agents.platform.topology_optimizer import TopologyOptimizer


def _agent(agent_id, **kwargs):
    defaults = dict(name="Agent", role="agent", persona="Test")
    defaults.update(kwargs)
    return AgentSpec(id=agent_id, **defaults)


class TestAgentPerformanceMetrics:
    def test_success_rate_empty(self):
        m = AgentPerformanceMetrics(agent_id="test")
        assert m.success_rate == 0.0

    def test_success_rate(self):
        m = AgentPerformanceMetrics(
            agent_id="test", total_invocations=10, success_count=7
        )
        assert abs(m.success_rate - 0.7) < 0.01


class TestPipelinePerformanceMetrics:
    def test_success_rate(self):
        m = PipelinePerformanceMetrics(
            pipeline_id="test", total_executions=4, success_count=3
        )
        assert abs(m.success_rate - 0.75) < 0.01


class TestMetaAgent:
    def _make_meta(self):
        return MetaAgent(
            agent_registry=AgentRegistry(),
            pipeline_registry=PipelineRegistry(),
        )

    def test_record_pipeline_execution(self):
        meta = self._make_meta()
        meta.record_pipeline_execution(
            pipeline_id="p1",
            success=True,
            execution_time=10.0,
            tokens_used=5000,
            depth_reached=1,
        )
        metrics = meta.get_pipeline_metrics()
        assert "p1" in metrics
        assert metrics["p1"].total_executions == 1
        assert metrics["p1"].success_count == 1

    def test_record_multiple_executions(self):
        meta = self._make_meta()
        for i in range(5):
            meta.record_pipeline_execution(
                pipeline_id="p1",
                success=i < 3,
                execution_time=10.0 + i,
                tokens_used=1000,
                depth_reached=0,
            )
        m = meta.get_pipeline_metrics()["p1"]
        assert m.total_executions == 5
        assert m.success_count == 3

    def test_record_agent_stats(self):
        meta = self._make_meta()
        meta.record_pipeline_execution(
            pipeline_id="p1",
            success=True,
            execution_time=5.0,
            tokens_used=1000,
            depth_reached=0,
            agent_stats={
                "agent.1": {"success": True, "tokens_used": 500, "execution_time": 2.0},
                "agent.2": {"success": False, "tokens_used": 300},
            },
        )
        ametrics = meta.get_agent_metrics()
        assert "agent.1" in ametrics
        assert "agent.2" in ametrics
        assert ametrics["agent.1"].success_count == 1
        assert ametrics["agent.2"].failure_count == 1

    def test_analyze_low_success_rate(self):
        meta = self._make_meta()
        for i in range(6):
            meta.record_pipeline_execution(
                pipeline_id="p1",
                success=True,
                execution_time=5.0,
                tokens_used=1000,
                depth_reached=0,
                agent_stats={
                    "bad_agent": {"success": i < 2, "tokens_used": 500},
                },
            )
        suggestions = meta.analyze()
        agent_suggestions = [s for s in suggestions if s.suggestion_type == "adjust_agent"]
        assert len(agent_suggestions) >= 1
        assert agent_suggestions[0].target_id == "bad_agent"

    def test_analyze_slow_pipeline(self):
        meta = self._make_meta()
        for _ in range(3):
            meta.record_pipeline_execution(
                pipeline_id="slow",
                success=True,
                execution_time=200.0,
                tokens_used=1000,
                depth_reached=0,
            )
        suggestions = meta.analyze()
        pipeline_suggestions = [s for s in suggestions if s.suggestion_type == "optimize_pipeline"]
        assert len(pipeline_suggestions) >= 1
        assert pipeline_suggestions[0].target_id == "slow"

    def test_analyze_token_heavy_agent(self):
        meta = self._make_meta()
        for _ in range(3):
            meta.record_pipeline_execution(
                pipeline_id="p1",
                success=True,
                execution_time=5.0,
                tokens_used=1000,
                depth_reached=0,
                agent_stats={"heavy": {"success": True, "tokens_used": 15000}},
            )
        suggestions = meta.analyze()
        token_suggestions = [s for s in suggestions if s.suggestion_type == "reduce_tokens"]
        assert len(token_suggestions) >= 1
        assert token_suggestions[0].target_id == "heavy"

    def test_recommend_pipeline_for_task(self):
        meta = self._make_meta()
        for _ in range(5):
            meta.record_pipeline_execution("good", True, 5.0, 1000, 0)
            meta.record_pipeline_execution("bad", False, 5.0, 1000, 0)

        # Only good has enough success
        best = meta.recommend_pipeline_for_task("test task")
        assert best == "good"

    def test_recommend_none_insufficient_data(self):
        meta = self._make_meta()
        meta.record_pipeline_execution("p1", True, 5.0, 1000, 0)
        assert meta.recommend_pipeline_for_task("test") is None


class TestTopologyOptimizer:
    def test_adjust_agent_temperature(self):
        reg = AgentRegistry()
        reg.register(_agent("slow", temperature=0.5))

        meta = MetaAgent(agent_registry=reg, pipeline_registry=PipelineRegistry())
        optimizer = TopologyOptimizer(agent_registry=reg, meta_agent=meta)

        suggestion = OptimizationSuggestion(
            suggestion_type="adjust_agent",
            target_id="slow",
            description="Low success rate",
            expected_impact="Better",
            confidence=0.7,
        )
        assert optimizer.apply_suggestion(suggestion) is True
        assert reg.get("slow").temperature == 0.6

    def test_reduce_tokens(self):
        reg = AgentRegistry()
        reg.register(_agent("heavy", max_tokens=8000))

        meta = MetaAgent(agent_registry=reg, pipeline_registry=PipelineRegistry())
        optimizer = TopologyOptimizer(agent_registry=reg, meta_agent=meta)

        suggestion = OptimizationSuggestion(
            suggestion_type="reduce_tokens",
            target_id="heavy",
            description="Too many tokens",
            expected_impact="Cost reduction",
            confidence=0.5,
        )
        assert optimizer.apply_suggestion(suggestion) is True
        assert reg.get("heavy").max_tokens == 6000  # 8000 * 0.75

    def test_apply_unknown_suggestion(self):
        reg = AgentRegistry()
        meta = MetaAgent(agent_registry=reg, pipeline_registry=PipelineRegistry())
        optimizer = TopologyOptimizer(agent_registry=reg, meta_agent=meta)

        suggestion = OptimizationSuggestion(
            suggestion_type="unknown_type",
            target_id="x",
            description="Test",
            expected_impact="None",
            confidence=0.1,
        )
        assert optimizer.apply_suggestion(suggestion) is False

    def test_apply_to_nonexistent_agent(self):
        reg = AgentRegistry()
        meta = MetaAgent(agent_registry=reg, pipeline_registry=PipelineRegistry())
        optimizer = TopologyOptimizer(agent_registry=reg, meta_agent=meta)

        suggestion = OptimizationSuggestion(
            suggestion_type="adjust_agent",
            target_id="nonexistent",
            description="Test",
            expected_impact="None",
            confidence=0.5,
        )
        assert optimizer.apply_suggestion(suggestion) is False

    def test_get_applied_optimizations(self):
        reg = AgentRegistry()
        reg.register(_agent("a1", temperature=0.5))

        meta = MetaAgent(agent_registry=reg, pipeline_registry=PipelineRegistry())
        optimizer = TopologyOptimizer(agent_registry=reg, meta_agent=meta)

        suggestion = OptimizationSuggestion(
            suggestion_type="adjust_agent",
            target_id="a1",
            description="Test",
            expected_impact="Better",
            confidence=0.7,
        )
        optimizer.apply_suggestion(suggestion)
        applied = optimizer.get_applied_optimizations()
        assert len(applied) == 1
        assert "temperature" in applied[0]["change"]
