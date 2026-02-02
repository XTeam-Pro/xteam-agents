"""Graph edge routing functions."""

from typing import Literal

import structlog

from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


def route_after_validation(
    state: AgentState,
) -> Literal["commit", "plan", "fail"]:
    """
    Route after validation based on the validation result.

    Routes to:
    - commit: If validated and ready to commit
    - plan: If needs replanning (and haven't exceeded max iterations)
    - fail: If failed or exceeded max iterations

    This is the critical decision point that determines whether
    validated content reaches shared memory.
    """
    logger.debug(
        "routing_after_validation",
        task_id=str(state.task_id),
        is_validated=state.is_validated,
        should_replan=state.should_replan,
        is_failed=state.is_failed,
        iteration=state.iteration_count,
    )

    # Check for explicit failure
    if state.is_failed:
        logger.info(
            "route_to_fail",
            task_id=str(state.task_id),
            reason="is_failed",
        )
        return "fail"

    # Check for max iterations exceeded
    if state.has_exceeded_max_iterations():
        logger.warning(
            "route_to_fail",
            task_id=str(state.task_id),
            reason="max_iterations_exceeded",
        )
        return "fail"

    # Check if validated - ready to commit
    if state.is_validated:
        logger.info(
            "route_to_commit",
            task_id=str(state.task_id),
        )
        return "commit"

    # Need to replan
    if state.should_replan:
        logger.info(
            "route_to_plan",
            task_id=str(state.task_id),
            reason="needs_replan",
        )
        return "plan"

    # Default to commit if unclear (shouldn't happen)
    logger.warning(
        "route_default_to_commit",
        task_id=str(state.task_id),
    )
    return "commit"


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """
    Check if the graph should continue or end.

    Used for simple continuation checks.
    """
    if state.is_failed or state.current_node == "end":
        return "end"
    return "continue"
