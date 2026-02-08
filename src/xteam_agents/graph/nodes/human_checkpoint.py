"""Human checkpoint node - gates pipeline stages for human review.

This is a system node (NOT an LLM agent), similar to commit_node.
When MAGIC is disabled, it's a passthrough that returns {}.
"""

from typing import Any, Callable

import structlog

from xteam_agents.magic.core import MAGICCore
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.magic import (
    CheckpointStage,
    HumanResponseType,
)
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


def create_human_checkpoint_node(
    magic_core: MAGICCore,
    memory_manager: MemoryManager,
    stage: CheckpointStage,
) -> Callable[[AgentState], dict[str, Any]]:
    """Create a human checkpoint node for a specific pipeline stage.

    Returns a passthrough ({}) when MAGIC is disabled or no escalation is needed.
    """

    async def human_checkpoint(state: AgentState) -> dict[str, Any]:
        # If MAGIC is not configured or disabled, passthrough
        if not state.magic_config or not state.magic_config.enabled:
            return {}

        logger.info(
            "human_checkpoint_enter",
            task_id=str(state.task_id),
            stage=stage.value,
        )

        # Get confidence score for this stage (if already assessed)
        confidence = None
        node_map = {
            CheckpointStage.AFTER_ANALYZE: "analyze",
            CheckpointStage.AFTER_PLAN: "plan",
            CheckpointStage.AFTER_EXECUTE: "execute",
            CheckpointStage.AFTER_VALIDATE: "validate",
        }
        node_name = node_map.get(stage, "unknown")
        confidence_data = state.confidence_scores.get(node_name)
        if confidence_data:
            from xteam_agents.models.magic import ConfidenceScore
            if isinstance(confidence_data, dict):
                confidence = ConfidenceScore(**confidence_data)
            elif isinstance(confidence_data, ConfidenceScore):
                confidence = confidence_data

        # Check if escalation is needed
        escalation = magic_core.create_escalation(state, confidence, stage)

        if not escalation:
            logger.debug(
                "human_checkpoint_no_escalation",
                task_id=str(state.task_id),
                stage=stage.value,
            )
            return {}

        # Log escalation
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.HUMAN_ESCALATION_CREATED,
                node_name=f"checkpoint_{stage.value}",
                description=f"Escalation created: {escalation.question[:100]}",
                data={
                    "escalation_id": str(escalation.id),
                    "reason": escalation.reason.value,
                    "priority": escalation.priority.value,
                },
            )
        )

        # Set state to paused while waiting
        updates: dict[str, Any] = {
            "is_human_paused": True,
            "pending_escalation": escalation.model_dump(mode="json"),
        }

        # Wait for human response
        timeout = state.magic_config.escalation_timeout
        response = await magic_core.wait_for_response(escalation.id, timeout)

        if response is None:
            # Timeout - apply fallback
            fallback = state.magic_config.fallback_on_timeout

            await memory_manager.log_audit(
                AuditEntry(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    event_type=AuditEventType.HUMAN_ESCALATION_TIMEOUT,
                    node_name=f"checkpoint_{stage.value}",
                    description=f"Escalation timed out after {timeout}s, fallback: {fallback}",
                    data={"escalation_id": str(escalation.id)},
                )
            )

            if fallback == "continue":
                return {
                    "is_human_paused": False,
                    "pending_escalation": None,
                }
            elif fallback == "pause":
                return {
                    "is_human_paused": True,
                    "pending_escalation": escalation.model_dump(mode="json"),
                }
            elif fallback == "fail":
                return {
                    "is_human_paused": False,
                    "pending_escalation": None,
                    "is_failed": True,
                    "error": "Human escalation timed out with fail policy",
                }
            # Default: continue
            return {
                "is_human_paused": False,
                "pending_escalation": None,
            }

        # Process the human response
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.HUMAN_ESCALATION_RESOLVED,
                node_name=f"checkpoint_{stage.value}",
                description=f"Human responded: {response.response_type.value}",
                data={
                    "escalation_id": str(escalation.id),
                    "response_type": response.response_type.value,
                    "content": response.content[:200] if response.content else "",
                },
            )
        )

        state_updates = magic_core.process_human_response(state, response)

        logger.info(
            "human_checkpoint_resolved",
            task_id=str(state.task_id),
            stage=stage.value,
            response_type=response.response_type.value,
        )

        return state_updates

    return human_checkpoint
