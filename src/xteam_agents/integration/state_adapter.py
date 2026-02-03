"""State adapter for converting between AgentState and AdversarialAgentState."""

from typing import Any
from uuid import UUID

import structlog

from xteam_agents.agents.adversarial_config import AgentPairType, PairStatus
from xteam_agents.agents.adversarial_state import (
    AdversarialAgentState,
    OrchestratorFinalDecision,
    PairResult,
)
from xteam_agents.models.state import AgentState, SubTask, SubTaskStatus

logger = structlog.get_logger()


class StateAdapter:
    """
    Adapter for converting between AgentState and AdversarialAgentState.

    This enables the Adversarial Agent Team to work within the Cognitive OS.
    """

    @staticmethod
    def to_adversarial(state: AgentState) -> AdversarialAgentState:
        """
        Convert AgentState to AdversarialAgentState.

        Args:
            state: Cognitive OS agent state

        Returns:
            AdversarialAgentState ready for adversarial team execution
        """
        logger.info(
            "converting_to_adversarial",
            task_id=str(state.task_id),
            complexity=state.context.get("complexity", "unknown"),
        )

        # Create adversarial state
        adversarial_state = AdversarialAgentState(
            task_id=str(state.task_id),
            original_request=state.description,
            context=state.context.copy(),
            created_at=state.created_at,
        )

        logger.debug(
            "adversarial_state_created",
            task_id=str(state.task_id),
            request_length=len(state.description),
        )

        return adversarial_state

    @staticmethod
    def from_adversarial(
        adversarial_state: AdversarialAgentState,
        original_state: AgentState,
    ) -> dict[str, Any]:
        """
        Extract updates from AdversarialAgentState to apply to AgentState.

        Args:
            adversarial_state: Result from adversarial team execution
            original_state: Original cognitive OS state

        Returns:
            Dictionary of updates to apply to AgentState
        """
        logger.info(
            "converting_from_adversarial",
            task_id=adversarial_state.task_id,
            has_final_decision=adversarial_state.orchestrator_final_decision is not None,
        )

        updates: dict[str, Any] = {}

        # Check if we have a final decision
        if not adversarial_state.orchestrator_final_decision:
            logger.warning(
                "no_final_decision",
                task_id=adversarial_state.task_id,
                status=adversarial_state.current_phase,
            )
            return {
                "error": "Adversarial team did not produce a final decision",
                "is_failed": True,
            }

        final_decision = adversarial_state.orchestrator_final_decision

        # Build execution result from final decision
        execution_result = StateAdapter._build_execution_result(
            adversarial_state, final_decision
        )
        updates["execution_result"] = execution_result

        # Map artifacts
        if final_decision.artifacts_to_commit:
            updates["artifacts"] = final_decision.artifacts_to_commit

        # Set validation status
        # If adversarial team approved, mark as validated
        # Otherwise, validation will need to happen in validate node
        updates["is_validated"] = final_decision.approved

        if not final_decision.approved:
            updates["validation_feedback"] = final_decision.rationale

        # Convert pair results to subtasks for tracking
        subtasks = StateAdapter._pair_results_to_subtasks(adversarial_state)
        if subtasks:
            # Append to existing subtasks
            updates["subtasks"] = original_state.subtasks + subtasks

        # Update context with adversarial metadata
        context = original_state.context.copy()
        context["adversarial_execution"] = {
            "quality_score": final_decision.quality_score,
            "all_pairs_passed": final_decision.all_pairs_passed,
            "conflicts_resolved": final_decision.conflicts_resolved,
            "total_pairs": len(adversarial_state.pair_results),
            "approved_pairs": len(
                [
                    p
                    for p in adversarial_state.pair_results.values()
                    if p.status == PairStatus.APPROVED
                ]
            ),
        }
        updates["context"] = context

        logger.info(
            "adversarial_conversion_complete",
            task_id=adversarial_state.task_id,
            approved=final_decision.approved,
            quality_score=final_decision.quality_score,
            artifacts_count=len(final_decision.artifacts_to_commit),
        )

        return updates

    @staticmethod
    def _build_execution_result(
        adversarial_state: AdversarialAgentState,
        final_decision: OrchestratorFinalDecision,
    ) -> str:
        """
        Build a comprehensive execution result from adversarial team output.

        Args:
            adversarial_state: Adversarial state with all pair results
            final_decision: Final decision from orchestrator

        Returns:
            Formatted execution result string
        """
        lines = [
            "# Adversarial Team Execution Result",
            "",
            f"**Status:** {'✅ Approved' if final_decision.approved else '❌ Rejected'}",
            f"**Quality Score:** {final_decision.quality_score}/10",
            "",
            "## Summary",
            final_decision.rationale,
            "",
        ]

        # Add pair results summary
        if adversarial_state.pair_results:
            lines.extend([
                "## Pair Results",
                "",
            ])

            for pair_type, result in adversarial_state.pair_results.items():
                status_icon = {
                    PairStatus.APPROVED: "✅",
                    PairStatus.REJECTED: "❌",
                    PairStatus.ESCALATED: "⚠️",
                    PairStatus.PENDING: "⏳",
                }.get(result.status, "❓")

                lines.append(
                    f"- **{pair_type.value}** {status_icon}: "
                    f"{result.iteration_count} iterations, "
                    f"Score: {result.final_evaluation.average_score() if result.final_evaluation else 'N/A'}/10"
                )

            lines.append("")

        # Add conflicts if any
        if adversarial_state.conflicts:
            lines.extend([
                "## Conflicts Resolved",
                "",
            ])
            for conflict in adversarial_state.conflicts:
                if conflict.resolved:
                    lines.append(
                        f"- **{conflict.pair_type.value}**: {conflict.orchestrator_decision}"
                    )
            lines.append("")

        # Add next steps
        if final_decision.next_steps:
            lines.extend([
                "## Next Steps",
                "",
            ])
            for step in final_decision.next_steps:
                lines.append(f"- {step}")
            lines.append("")

        # Add conditions if any
        if final_decision.conditions:
            lines.extend([
                "## Conditions",
                "",
            ])
            for condition in final_decision.conditions:
                lines.append(f"- {condition}")

        return "\n".join(lines)

    @staticmethod
    def _pair_results_to_subtasks(
        adversarial_state: AdversarialAgentState,
    ) -> list[SubTask]:
        """
        Convert pair results to SubTasks for tracking in AgentState.

        Args:
            adversarial_state: Adversarial state with pair results

        Returns:
            List of SubTasks representing each pair's work
        """
        subtasks: list[SubTask] = []

        for pair_type, result in adversarial_state.pair_results.items():
            # Determine subtask status from pair status
            if result.status == PairStatus.APPROVED:
                status = SubTaskStatus.COMPLETED
                subtask_result = (
                    f"Approved after {result.iteration_count} iterations. "
                    f"Score: {result.final_evaluation.average_score() if result.final_evaluation else 'N/A'}/10"
                )
                error = None
            elif result.status == PairStatus.REJECTED:
                status = SubTaskStatus.FAILED
                subtask_result = None
                error = f"Rejected after {result.iteration_count} iterations"
            elif result.status == PairStatus.ESCALATED:
                status = SubTaskStatus.COMPLETED
                subtask_result = f"Escalated and resolved after {result.iteration_count} iterations"
                error = None
            else:
                status = SubTaskStatus.PENDING
                subtask_result = None
                error = None

            subtask = SubTask(
                description=f"{pair_type.value} pair review",
                status=status,
                result=subtask_result,
                error=error,
                assigned_agent=f"{result.agent_role.value}+{result.critic_role.value}",
                created_at=result.started_at or adversarial_state.created_at,
                completed_at=result.completed_at,
            )

            subtasks.append(subtask)

        return subtasks

    @staticmethod
    def get_complexity_from_state(state: AgentState) -> str:
        """
        Extract complexity level from AgentState.

        Args:
            state: Agent state

        Returns:
            Complexity level: 'simple', 'medium', 'complex', or 'critical'
        """
        return state.context.get("complexity", "simple")

    @staticmethod
    def should_use_adversarial(state: AgentState) -> bool:
        """
        Determine if adversarial execution should be used based on state.

        Args:
            state: Agent state

        Returns:
            True if adversarial execution should be used
        """
        complexity = StateAdapter.get_complexity_from_state(state)
        return complexity in ["complex", "critical"]
