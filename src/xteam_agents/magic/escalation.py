"""EscalationRouter - Intelligent routing of decisions to humans."""

from uuid import UUID

import structlog

from xteam_agents.models.magic import (
    AutonomyLevel,
    CheckpointStage,
    ConfidenceScore,
    EscalationPriority,
    EscalationReason,
    EscalationRequest,
)
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


class EscalationRouter:
    """Routes decisions to humans based on autonomy level, confidence, and config."""

    def __init__(self) -> None:
        self._pending: dict[UUID, EscalationRequest] = {}

    def should_escalate(
        self,
        state: AgentState,
        confidence: ConfidenceScore | None,
        stage: CheckpointStage,
    ) -> EscalationRequest | None:
        """Determine if human escalation is needed at this stage."""
        config = state.magic_config
        if not config or not config.enabled:
            return None

        autonomy = config.autonomy_level

        # TRUSTED: never escalate
        if autonomy == AutonomyLevel.TRUSTED:
            return None

        # Check explicit checkpoints first
        if stage in config.checkpoints:
            return self._create_escalation(
                state, stage, EscalationReason.EXPLICIT_CHECKPOINT, confidence
            )

        # SUPERVISED: every step
        if autonomy == AutonomyLevel.SUPERVISED:
            return self._create_escalation(
                state, stage, EscalationReason.EXPLICIT_CHECKPOINT, confidence
            )

        # GUIDED: after analysis + after validation
        if autonomy == AutonomyLevel.GUIDED:
            if stage in (CheckpointStage.AFTER_ANALYZE, CheckpointStage.AFTER_EXECUTE):
                return self._create_escalation(
                    state, stage, EscalationReason.EXPLICIT_CHECKPOINT, confidence
                )

        # COLLABORATIVE: on low confidence
        if autonomy == AutonomyLevel.COLLABORATIVE:
            if confidence and confidence.should_escalate(config.confidence_threshold):
                return self._create_escalation(
                    state, stage, EscalationReason.LOW_CONFIDENCE, confidence
                )

        # AUTONOMOUS: only on failures
        if autonomy == AutonomyLevel.AUTONOMOUS:
            if state.is_failed or (state.should_replan and state.validation_attempts >= 2):
                return self._create_escalation(
                    state, stage, EscalationReason.VALIDATION_FAILURE, confidence
                )

        # Confidence-based escalation (applies to all levels except TRUSTED)
        if confidence and confidence.should_escalate(config.confidence_threshold):
            # Only escalate for very low confidence in non-autonomous modes
            if autonomy != AutonomyLevel.AUTONOMOUS and confidence.overall < 0.3:
                return self._create_escalation(
                    state, stage, EscalationReason.LOW_CONFIDENCE, confidence
                )

        return None

    def _create_escalation(
        self,
        state: AgentState,
        stage: CheckpointStage,
        reason: EscalationReason,
        confidence: ConfidenceScore | None,
    ) -> EscalationRequest:
        """Create an escalation request."""
        question = self._generate_question(state, stage, reason)
        options = self._generate_options(stage, reason)
        default_action = self._get_default_action(stage, reason)
        priority = self._compute_priority(reason, confidence)

        config = state.magic_config
        timeout = config.escalation_timeout if config else 300

        request = EscalationRequest(
            task_id=state.task_id,
            session_id=state.session_id,
            reason=reason,
            priority=priority,
            stage=stage,
            question=question,
            context=self._build_context(state, stage),
            options=options,
            default_action=default_action,
            confidence_score=confidence,
            timeout_seconds=timeout,
        )

        self._pending[request.id] = request
        logger.info(
            "escalation_created",
            escalation_id=str(request.id),
            task_id=str(state.task_id),
            reason=reason.value,
            stage=stage.value,
        )
        return request

    def get_pending_escalations(
        self, task_id: UUID | None = None
    ) -> list[EscalationRequest]:
        """Get pending (unresolved) escalations."""
        pending = [e for e in self._pending.values() if not e.is_resolved]
        if task_id:
            pending = [e for e in pending if e.task_id == task_id]
        return pending

    def resolve_escalation(self, escalation_id: UUID) -> None:
        """Mark an escalation as resolved."""
        if escalation_id in self._pending:
            req = self._pending[escalation_id]
            self._pending[escalation_id] = req.model_copy(
                update={"is_resolved": True}
            )

    def _generate_question(
        self, state: AgentState, stage: CheckpointStage, reason: EscalationReason
    ) -> str:
        stage_labels = {
            CheckpointStage.AFTER_ANALYZE: "analysis",
            CheckpointStage.AFTER_PLAN: "plan",
            CheckpointStage.AFTER_EXECUTE: "execution result",
            CheckpointStage.AFTER_VALIDATE: "validation",
        }
        stage_label = stage_labels.get(stage, "output")

        if reason == EscalationReason.LOW_CONFIDENCE:
            return (
                f"The system has low confidence in the {stage_label} for task: "
                f"'{state.description[:100]}'. Please review and provide guidance."
            )
        elif reason == EscalationReason.VALIDATION_FAILURE:
            return (
                f"Validation failed for task: '{state.description[:100]}'. "
                f"Feedback: {(state.validation_feedback or '')[:200]}. "
                "How should we proceed?"
            )
        elif reason == EscalationReason.EXPLICIT_CHECKPOINT:
            return (
                f"Checkpoint reached after {stage_label} for task: "
                f"'{state.description[:100]}'. Please review and approve."
            )
        return f"Human review requested for {stage_label}."

    def _generate_options(
        self, stage: CheckpointStage, reason: EscalationReason
    ) -> list[str]:
        base = ["Approve and continue", "Reject and replan", "Provide guidance"]
        if stage == CheckpointStage.AFTER_EXECUTE:
            base.append("Override with custom result")
        if reason == EscalationReason.VALIDATION_FAILURE:
            base.append("Force approve despite failure")
        return base

    def _get_default_action(
        self, stage: CheckpointStage, reason: EscalationReason
    ) -> str:
        if reason == EscalationReason.EXPLICIT_CHECKPOINT:
            return "Approve and continue"
        return "Provide guidance"

    def _compute_priority(
        self, reason: EscalationReason, confidence: ConfidenceScore | None
    ) -> EscalationPriority:
        if reason == EscalationReason.VALIDATION_FAILURE:
            return EscalationPriority.HIGH
        if reason == EscalationReason.HIGH_RISK_TASK:
            return EscalationPriority.CRITICAL
        if confidence and confidence.overall < 0.3:
            return EscalationPriority.HIGH
        return EscalationPriority.MEDIUM

    def _build_context(self, state: AgentState, stage: CheckpointStage) -> str:
        parts = [f"Task: {state.description}"]
        if state.analysis and stage != CheckpointStage.AFTER_ANALYZE:
            parts.append(f"Analysis: {state.analysis[:300]}")
        if state.plan and stage in (
            CheckpointStage.AFTER_EXECUTE,
            CheckpointStage.AFTER_VALIDATE,
        ):
            parts.append(f"Plan: {state.plan[:300]}")
        if state.execution_result and stage == CheckpointStage.AFTER_VALIDATE:
            parts.append(f"Result: {state.execution_result[:300]}")
        return "\n\n".join(parts)
