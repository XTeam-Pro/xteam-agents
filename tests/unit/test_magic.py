"""Unit tests for the MAGIC human-AI collaboration system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from xteam_agents.models.magic import (
    AutonomyLevel,
    CheckpointStage,
    ConfidenceScore,
    EscalationPriority,
    EscalationReason,
    EscalationRequest,
    HumanResponse,
    HumanResponseType,
    HumanFeedback,
    FeedbackType,
    CollaborativeSession,
    MAGICTaskConfig,
    EvolutionMetric,
)
from xteam_agents.magic.metacognition import MetacognitionEngine
from xteam_agents.magic.escalation import EscalationRouter
from xteam_agents.magic.feedback import FeedbackCollector
from xteam_agents.magic.session import SessionManager
from xteam_agents.magic.evolution import EvolutionEngine
from xteam_agents.magic.core import MAGICCore
from xteam_agents.models.state import AgentState
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType


class TestConfidenceScore:
    """Tests for ConfidenceScore model."""

    def test_confidence_level_high(self):
        score = ConfidenceScore(
            overall=0.85,
            factual_accuracy=0.9,
            completeness=0.8,
            relevance=0.85,
            coherence=0.85,
            novelty_risk=0.1,
        )
        assert score.level.value == "high"

    def test_confidence_level_medium(self):
        score = ConfidenceScore(overall=0.7)
        assert score.level.value == "medium"

    def test_confidence_level_low(self):
        score = ConfidenceScore(overall=0.5)
        assert score.level.value == "low"

    def test_should_escalate(self):
        score = ConfidenceScore(overall=0.5)
        assert score.should_escalate(threshold=0.6)

    def test_from_score_factory(self):
        score = ConfidenceScore.from_score(0.7, node_name="analyze")
        assert score.overall == 0.7
        assert score.node_name == "analyze"
        assert score.factual_accuracy == 0.7


class TestEscalationRouter:
    """Tests for EscalationRouter."""

    def test_no_escalation_when_magic_disabled(self):
        router = EscalationRouter()
        state = AgentState(
            task_id=uuid4(),
            description="test",
            magic_config=None,
        )
        result = router.should_escalate(state, None, CheckpointStage.AFTER_ANALYZE)
        assert result is None

    def test_escalation_trusted_autonomy(self):
        router = EscalationRouter()
        state = AgentState(
            task_id=uuid4(),
            description="test",
            magic_config=MAGICTaskConfig(
                autonomy_level=AutonomyLevel.TRUSTED,
            ),
        )
        result = router.should_escalate(state, None, CheckpointStage.AFTER_ANALYZE)
        assert result is None

    def test_escalation_supervised_autonomy(self):
        router = EscalationRouter()
        state = AgentState(
            task_id=uuid4(),
            description="test",
            magic_config=MAGICTaskConfig(
                autonomy_level=AutonomyLevel.SUPERVISED,
            ),
        )
        result = router.should_escalate(state, None, CheckpointStage.AFTER_ANALYZE)
        assert result is not None
        assert result.reason == EscalationReason.EXPLICIT_CHECKPOINT

    def test_escalation_on_low_confidence(self):
        router = EscalationRouter()
        state = AgentState(
            task_id=uuid4(),
            description="test",
            magic_config=MAGICTaskConfig(
                autonomy_level=AutonomyLevel.COLLABORATIVE,
                confidence_threshold=0.6,
            ),
        )
        low_confidence = ConfidenceScore(overall=0.4)
        result = router.should_escalate(state, low_confidence, CheckpointStage.AFTER_EXECUTE)
        assert result is not None
        assert result.reason == EscalationReason.LOW_CONFIDENCE


class TestFeedbackCollector:
    """Tests for FeedbackCollector."""

    @pytest.mark.asyncio
    async def test_record_feedback(self):
        memory_manager = AsyncMock()
        collector = FeedbackCollector(memory_manager)

        feedback = HumanFeedback(
            task_id=uuid4(),
            feedback_type=FeedbackType.CORRECTION,
            content="This is wrong",
        )

        await collector.record_feedback(feedback)
        assert len(collector._feedback_log) == 1
        memory_manager.store_episodic.assert_called_once()

    @pytest.mark.asyncio
    async def test_feedback_to_guideline_conversion(self):
        memory_manager = AsyncMock()
        collector = FeedbackCollector(memory_manager)

        feedback = HumanFeedback(
            task_id=uuid4(),
            feedback_type=FeedbackType.GUIDELINE,
            content="Always validate user input",
            should_persist=True,
        )

        await collector.record_feedback(feedback)
        guidelines = collector.get_pending_guidelines()
        assert len(guidelines) == 1
        assert guidelines[0].metadata.get("type") == "guideline"
        assert guidelines[0].is_validated

    def test_convert_response_to_feedback(self):
        memory_manager = AsyncMock()
        collector = FeedbackCollector(memory_manager)

        response = HumanResponse(
            escalation_id=uuid4(),
            response_type=HumanResponseType.APPROVAL,
            content="Looks good",
        )

        feedback = collector.convert_response_to_feedback(response, uuid4())
        assert feedback.feedback_type == FeedbackType.RATING
        assert feedback.rating == 1.0


class TestSessionManager:
    """Tests for SessionManager."""

    def test_create_session(self):
        manager = SessionManager()
        task_id = uuid4()
        session = manager.create_session(task_id, "user1")

        assert session.task_id == task_id
        assert session.human_id == "user1"
        assert manager.get_session(session.id) == session
        assert manager.get_session_for_task(task_id) == session

    def test_add_message(self):
        manager = SessionManager()
        task_id = uuid4()
        session = manager.create_session(task_id)

        manager.add_message(session.id, "user", "Hello")
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_wait_for_response_timeout(self):
        manager = SessionManager()
        escalation_id = uuid4()

        response = await manager.wait_for_response(escalation_id, timeout=0.1)
        assert response is None

    @pytest.mark.asyncio
    async def test_submit_response(self):
        import asyncio

        manager = SessionManager()
        escalation_id = uuid4()

        # Create a task that waits for response
        async def waiter():
            return await manager.wait_for_response(escalation_id, timeout=5)

        wait_task = asyncio.create_task(waiter())

        # Give it time to start waiting
        await asyncio.sleep(0.1)

        # Submit response
        response = HumanResponse(
            escalation_id=escalation_id,
            response_type=HumanResponseType.APPROVAL,
            content="Approved",
        )
        manager.submit_response(escalation_id, response)

        result = await wait_task
        assert result is not None
        assert result.response_type == HumanResponseType.APPROVAL


class TestEvolutionEngine:
    """Tests for EvolutionEngine."""

    def test_compute_metrics_empty(self):
        engine = EvolutionEngine()
        metrics = engine.compute_metrics()
        assert len(metrics) == 0

    def test_record_validation(self):
        engine = EvolutionEngine()
        engine.record_validation(first_pass_approved=True)
        engine.record_validation(first_pass_approved=False)

        metrics = engine.compute_metrics()
        metric_map = {m.name: m for m in metrics}
        assert "first_pass_approval_rate" in metric_map
        assert metric_map["first_pass_approval_rate"].value == 0.5

    def test_autonomy_upgrade_recommendation(self):
        engine = EvolutionEngine()
        from xteam_agents.models.magic import HumanPreferenceProfile

        profile = HumanPreferenceProfile(
            human_id="user1",
            preferred_autonomy=AutonomyLevel.COLLABORATIVE,
            approval_rate=0.95,
            total_interactions=25,
        )

        recommendation = engine.recommend_autonomy_adjustment("user1", profile)
        assert recommendation == AutonomyLevel.AUTONOMOUS


class TestMAGICCore:
    """Tests for MAGICCore."""

    @pytest.mark.asyncio
    async def test_assess_confidence(self):
        llm_provider = AsyncMock()
        memory_manager = AsyncMock()

        magic_core = MAGICCore(llm_provider, memory_manager)

        with patch.object(
            magic_core.metacognition,
            "assess_confidence",
            new_callable=AsyncMock,
        ) as mock_assess:
            score = ConfidenceScore(overall=0.8)
            mock_assess.return_value = score

            result = await magic_core.assess_confidence(
                "task1", "analyze", "output", "description"
            )
            assert result.overall == 0.8

    def test_process_human_response_approval(self):
        llm_provider = AsyncMock()
        memory_manager = AsyncMock()
        magic_core = MAGICCore(llm_provider, memory_manager)

        state = AgentState(task_id=uuid4(), description="test")
        response = HumanResponse(
            escalation_id=uuid4(),
            response_type=HumanResponseType.APPROVAL,
        )

        updates = magic_core.process_human_response(state, response)
        assert updates["is_human_paused"] is False
        assert updates["pending_escalation"] is None

    def test_process_human_response_rejection(self):
        llm_provider = AsyncMock()
        memory_manager = AsyncMock()
        magic_core = MAGICCore(llm_provider, memory_manager)

        state = AgentState(task_id=uuid4(), description="test")
        response = HumanResponse(
            escalation_id=uuid4(),
            response_type=HumanResponseType.REJECTION,
            content="Not ready",
        )

        updates = magic_core.process_human_response(state, response)
        assert updates["should_replan"] is True
        assert updates["validation_feedback"] == "Not ready"


class TestBackwardCompatibility:
    """Test that MAGIC fields don't break existing functionality."""

    def test_agent_state_without_magic(self):
        """AgentState should work without MAGIC fields."""
        state = AgentState(
            task_id=uuid4(),
            description="test task",
        )
        assert state.magic_config is None
        assert state.confidence_scores == {}
        assert state.is_human_paused is False

    def test_magic_config_optional_in_state(self):
        """MAGICTaskConfig should be optional in AgentState."""
        state = AgentState(
            task_id=uuid4(),
            description="test",
            magic_config=MAGICTaskConfig(),
        )
        assert state.magic_config is not None
        assert state.magic_config.enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
