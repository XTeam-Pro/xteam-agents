"""MCP tools for the MAGIC human-AI collaboration system."""

from uuid import UUID

import structlog

from xteam_agents.orchestrator import TaskOrchestrator

logger = structlog.get_logger()


def register_magic_tools(mcp, orchestrator: TaskOrchestrator) -> None:
    """Register MAGIC tools with the MCP server."""

    @mcp.tool()
    async def configure_magic(
        task_id: str,
        enabled: bool = True,
        autonomy_level: str = "collaborative",
        confidence_threshold: float = 0.6,
        checkpoints: str = "",
        escalation_timeout: int = 300,
        fallback_on_timeout: str = "continue",
    ) -> dict:
        """Configure MAGIC human-AI collaboration for a task.

        Args:
            task_id: The task ID to configure
            enabled: Whether MAGIC is enabled
            autonomy_level: supervised, guided, collaborative, autonomous, trusted
            confidence_threshold: Confidence threshold for escalation (0.0-1.0)
            checkpoints: Comma-separated checkpoint stages (after_analyze, after_plan, after_execute, after_validate)
            escalation_timeout: Timeout in seconds for human responses
            fallback_on_timeout: What to do on timeout: continue, pause, fail
        """
        if not orchestrator._initialized:
            return {"error": "System not initialized"}

        magic_core = getattr(orchestrator, "_magic_core", None)
        if not magic_core:
            return {"error": "MAGIC system not enabled. Set MAGIC_ENABLED=true in config."}

        from xteam_agents.models.magic import (
            AutonomyLevel,
            CheckpointStage,
            MAGICTaskConfig,
        )

        try:
            autonomy = AutonomyLevel(autonomy_level)
        except ValueError:
            return {"error": f"Invalid autonomy_level: {autonomy_level}. Valid: supervised, guided, collaborative, autonomous, trusted"}

        checkpoint_list = []
        if checkpoints:
            for cp in checkpoints.split(","):
                cp = cp.strip()
                try:
                    checkpoint_list.append(CheckpointStage(cp))
                except ValueError:
                    return {"error": f"Invalid checkpoint: {cp}. Valid: after_analyze, after_plan, after_execute, after_validate"}

        config = MAGICTaskConfig(
            enabled=enabled,
            autonomy_level=autonomy,
            confidence_threshold=confidence_threshold,
            checkpoints=checkpoint_list,
            escalation_timeout=escalation_timeout,
            fallback_on_timeout=fallback_on_timeout,
        )

        return {
            "task_id": task_id,
            "magic_config": config.model_dump(mode="json"),
            "status": "configured",
        }

    @mcp.tool()
    async def respond_to_escalation(
        escalation_id: str,
        response_type: str,
        content: str = "",
        data: str = "{}",
        human_id: str = "default",
    ) -> dict:
        """Respond to a pending MAGIC escalation.

        Args:
            escalation_id: UUID of the escalation to respond to
            response_type: approval, rejection, modification, guidance, override, deferral
            content: Response text/explanation
            data: JSON string of additional data (for modifications/overrides)
            human_id: Human identifier
        """
        magic_core = getattr(orchestrator, "_magic_core", None)
        if not magic_core:
            return {"error": "MAGIC system not enabled"}

        from xteam_agents.models.magic import HumanResponse, HumanResponseType
        import json

        try:
            rt = HumanResponseType(response_type)
        except ValueError:
            return {"error": f"Invalid response_type: {response_type}"}

        try:
            response_data = json.loads(data) if data else {}
        except json.JSONDecodeError:
            response_data = {}

        esc_uuid = UUID(escalation_id)
        response = HumanResponse(
            escalation_id=esc_uuid,
            response_type=rt,
            content=content,
            data=response_data,
            human_id=human_id,
        )

        # Find the task_id for this escalation
        pending = magic_core.escalation_router.get_pending_escalations()
        task_id = None
        for esc in pending:
            if esc.id == esc_uuid:
                task_id = esc.task_id
                break

        if task_id:
            await magic_core.submit_response(esc_uuid, response, task_id)
            return {"status": "submitted", "escalation_id": escalation_id}
        else:
            # Still submit to unblock any waiting coroutine
            magic_core.session_manager.submit_response(esc_uuid, response)
            return {"status": "submitted_no_task", "escalation_id": escalation_id}

    @mcp.tool()
    async def list_pending_escalations(task_id: str = "") -> dict:
        """List all pending MAGIC escalations.

        Args:
            task_id: Optional task ID to filter by
        """
        magic_core = getattr(orchestrator, "_magic_core", None)
        if not magic_core:
            return {"error": "MAGIC system not enabled"}

        tid = UUID(task_id) if task_id else None
        pending = magic_core.escalation_router.get_pending_escalations(tid)

        return {
            "escalations": [
                {
                    "id": str(e.id),
                    "task_id": str(e.task_id),
                    "reason": e.reason.value,
                    "priority": e.priority.value,
                    "stage": e.stage.value,
                    "question": e.question,
                    "options": e.options,
                    "default_action": e.default_action,
                    "created_at": e.created_at.isoformat(),
                    "confidence": e.confidence_score.to_dict() if e.confidence_score else None,
                }
                for e in pending
            ],
            "count": len(pending),
        }

    @mcp.tool()
    async def submit_feedback(
        task_id: str,
        feedback_type: str,
        content: str,
        target_node: str = "",
        rating: float = -1,
        should_persist: bool = False,
        applies_to: str = "",
        human_id: str = "default",
    ) -> dict:
        """Submit human feedback on system output.

        Args:
            task_id: The task this feedback is about
            feedback_type: correction, preference, guideline, rating, comment
            content: The feedback content
            target_node: Which pipeline node this applies to (analyze, plan, execute, validate)
            rating: Optional rating 0.0-1.0 (-1 for no rating)
            should_persist: If true, this feedback will be saved as a permanent guideline
            applies_to: Domain/category this applies to
            human_id: Human identifier
        """
        magic_core = getattr(orchestrator, "_magic_core", None)
        if not magic_core:
            return {"error": "MAGIC system not enabled"}

        from xteam_agents.models.magic import FeedbackType, HumanFeedback

        try:
            ft = FeedbackType(feedback_type)
        except ValueError:
            return {"error": f"Invalid feedback_type: {feedback_type}"}

        feedback = HumanFeedback(
            task_id=UUID(task_id),
            feedback_type=ft,
            content=content,
            target_node=target_node or None,
            rating=rating if rating >= 0 else None,
            should_persist=should_persist,
            applies_to=applies_to or None,
            human_id=human_id,
        )

        await magic_core.feedback_collector.record_feedback(feedback)
        magic_core.evolution_engine.record_feedback(
            converted_to_guideline=should_persist
        )

        return {
            "feedback_id": str(feedback.id),
            "status": "recorded",
            "will_persist": should_persist,
        }

    @mcp.tool()
    async def get_confidence_scores(task_id: str) -> dict:
        """Get confidence scores for each pipeline stage of a task.

        Args:
            task_id: The task ID to get confidence scores for
        """
        magic_core = getattr(orchestrator, "_magic_core", None)
        if not magic_core:
            return {"error": "MAGIC system not enabled"}

        # Get from task state
        tid = UUID(task_id)
        if orchestrator.memory_manager:
            task_state = await orchestrator.memory_manager.get_task_state(tid)
            if task_state:
                return {
                    "task_id": task_id,
                    "scores": task_state.get("confidence_scores", {}),
                }

        return {"task_id": task_id, "scores": {}}

    @mcp.tool()
    async def get_magic_session(task_id: str) -> dict:
        """Get the MAGIC collaborative session for a task.

        Args:
            task_id: The task ID
        """
        magic_core = getattr(orchestrator, "_magic_core", None)
        if not magic_core:
            return {"error": "MAGIC system not enabled"}

        session = magic_core.session_manager.get_session_for_task(UUID(task_id))
        if not session:
            return {"task_id": task_id, "session": None}

        return {
            "task_id": task_id,
            "session": {
                "id": str(session.id),
                "status": session.status.value,
                "human_id": session.human_id,
                "messages": session.messages,
                "pending_escalations": [str(e) for e in session.pending_escalations],
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "is_expired": session.is_expired(),
            },
        }

    @mcp.tool()
    async def get_evolution_metrics() -> dict:
        """Get MAGIC system evolution and improvement metrics."""
        magic_core = getattr(orchestrator, "_magic_core", None)
        if not magic_core:
            return {"error": "MAGIC system not enabled"}

        metrics = magic_core.compute_metrics()
        proposals = magic_core.get_improvement_proposals()

        return {
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "trend": m.trend,
                    "period_days": m.period_days,
                }
                for m in metrics
            ],
            "improvement_proposals": proposals,
        }
