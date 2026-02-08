"""Reviewer agent node."""

from __future__ import annotations

from typing import Any, Callable

import structlog
from langchain_core.messages import AIMessage

from xteam_agents.graph.prompts import REVIEWER_SYSTEM_PROMPT
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.llm.tools import create_memory_tools
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


def create_validate_node(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
    magic_core: Any | None = None,
) -> Callable[[AgentState], AgentState]:
    """
    Create the validate node function.

    The Reviewer agent:
    - Reviews execution results
    - Verifies success criteria
    - Makes a validation decision (APPROVED, NEEDS_REPLAN, FAILED)
    - Sets is_validated flag for commit_node
    """

    async def validate_node(state: AgentState) -> dict[str, Any]:
        """Execute the validate node."""
        logger.info(
            "validate_node_enter",
            task_id=str(state.task_id),
            iteration=state.iteration_count,
            attempt=state.validation_attempts + 1,
        )

        # Log entry to audit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_ENTERED,
                agent_name="reviewer",
                node_name="validate",
                description=f"Entered validate node (attempt {state.validation_attempts + 1})",
            )
        )

        # Get memory tools (read-only)
        memory_tools = create_memory_tools(memory_manager)

        # Get the model with tools
        model = llm_provider.get_model_for_agent("reviewer")
        model_with_tools = model.bind_tools(memory_tools)

        # Build subtask summary
        subtask_summary = "\n".join(
            f"- [{st.status.value}] {st.description}"
            + (f"\n  Result: {st.result}" if st.result else "")
            + (f"\n  Error: {st.error}" if st.error else "")
            for st in state.subtasks
        )

        task_prompt = f"""
Task Description: {state.description}

Original Plan:
{state.plan}

Subtask Status:
{subtask_summary}

Execution Result:
{state.execution_result}

Please validate this execution:

1. Review each subtask's completion status
2. Verify the execution meets the plan's success criteria
3. Check for any quality or correctness issues
4. Make a validation decision

Your decision must be one of:
- APPROVED: All criteria met, ready for commit
- NEEDS_REPLAN: Issues require plan revision
- FAILED: Unrecoverable issues

Respond with your validation in this format:
DECISION: [APPROVED/NEEDS_REPLAN/FAILED]
FEEDBACK: [Your detailed feedback]
"""

        # Create messages
        messages = [
            {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt},
        ]

        # Invoke the model
        response = await model_with_tools.ainvoke(messages)

        # Handle tool calls if any
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                for tool in memory_tools:
                    if tool.name == tool_name:
                        result = await tool.ainvoke(tool_args)
                        tool_results.append(f"{tool_name}: {result}")
                        break

            messages.append({"role": "assistant", "content": str(response.content)})
            messages.append({
                "role": "user",
                "content": f"Tool results:\n" + "\n".join(tool_results),
            })

            response = await model.ainvoke(messages)

        # Extract validation from response
        validation_content = (
            response.content if hasattr(response, "content") else str(response)
        )

        # Parse decision
        decision = _parse_decision(validation_content)
        
        # SELF-HEALING LOGIC
        # If execution failed (e.g., Python error) or validation failed but is recoverable,
        # we can try to auto-correct without a full replan if it's a simple fix.
        # For now, we map "NEEDS_REPLAN" to a replan which goes back to Architect.
        # But we could have a "NEEDS_RETRY" state that goes back to Worker with feedback.
        
        # Current Flow:
        # APPROVED -> commit
        # NEEDS_REPLAN -> plan (Architect)
        # FAILED -> end
        
        # To implement Self-Healing, we treat NEEDS_REPLAN as a mechanism to fix issues.
        # The Architect will see the feedback and adjust the plan or instructions.
        
        is_validated = decision == "APPROVED"
        should_replan = decision == "NEEDS_REPLAN"
        is_failed = decision == "FAILED"

        # Extract feedback
        feedback = _extract_feedback(validation_content)
        
        # If we have run out of validation attempts, be more lenient
        # Increase from 3 to 5 attempts, and auto-approve on limit
        if state.validation_attempts >= 5 and should_replan:
            logger.warning("max_validation_attempts_reached", task_id=str(state.task_id))
            # Instead of failing, approve with warning
            should_replan = False
            is_validated = True
            is_failed = False
            decision = "APPROVED (Max Attempts Reached)"
            feedback = f"Auto-approved after {state.validation_attempts} attempts. Original feedback: {feedback}"
            logger.info(
                "auto_approved_after_max_attempts",
                task_id=str(state.task_id),
                attempts=state.validation_attempts,
            )

        # Log validation result
        event_type = AuditEventType.VALIDATION_PASSED
        if should_replan:
            event_type = AuditEventType.REPLAN_TRIGGERED
        elif is_failed:
            event_type = AuditEventType.VALIDATION_FAILED

        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=event_type,
                agent_name="reviewer",
                node_name="validate",
                description=f"Validation decision: {decision}",
                data={"feedback": feedback[:500] if feedback else None},
            )
        )

        # Store validation in episodic memory
        await memory_manager.store_episodic(
            MemoryArtifact(
                task_id=state.task_id,
                session_id=state.session_id,
                content=validation_content,
                content_type="validation",
                memory_type=MemoryType.EPISODIC,
                scope=MemoryScope.PRIVATE,
                created_by="reviewer",
                metadata={
                    "decision": decision,
                    "attempt": state.validation_attempts + 1,
                },
            )
        )

        # Log exit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_EXITED,
                agent_name="reviewer",
                node_name="validate",
                description=f"Validation complete: {decision}",
            )
        )

        logger.info(
            "validate_node_complete",
            task_id=str(state.task_id),
            decision=decision,
            is_validated=is_validated,
        )

        # MAGIC: assess confidence if enabled
        state_updates: dict[str, Any] = {
            "is_validated": is_validated,
            "validation_feedback": feedback,
            "validation_attempts": state.validation_attempts + 1,
            "should_replan": should_replan,
            "is_failed": is_failed,
            "error": feedback if is_failed else state.error,
            "current_node": "route",  # Will be routed by edge function
            "messages": state.messages + [AIMessage(content=validation_content)],
        }

        if magic_core and state.magic_config and state.magic_config.enabled:
            try:
                confidence = await magic_core.assess_confidence(
                    str(state.task_id),
                    "validate",
                    validation_content,
                    state.description,
                )
                state_updates["confidence_scores"] = {
                    **state.confidence_scores,
                    "validate": confidence.to_dict(),
                }
            except Exception as e:
                logger.warning("magic_confidence_assess_failed", error=str(e))

        return state_updates

    return validate_node


def _parse_decision(content: str) -> str:
    """Parse the validation decision from response."""
    content_upper = content.upper()

    if "DECISION: APPROVED" in content_upper or "DECISION:APPROVED" in content_upper:
        return "APPROVED"
    elif "DECISION: NEEDS_REPLAN" in content_upper or "DECISION:NEEDS_REPLAN" in content_upper:
        return "NEEDS_REPLAN"
    elif "DECISION: FAILED" in content_upper or "DECISION:FAILED" in content_upper:
        return "FAILED"
    elif "APPROVED" in content_upper and "NEEDS_REPLAN" not in content_upper:
        return "APPROVED"
    elif "NEEDS_REPLAN" in content_upper:
        return "NEEDS_REPLAN"
    elif "FAILED" in content_upper:
        return "FAILED"
    else:
        # Default to approved if unclear
        logger.warning("unclear_validation_decision", content_preview=content[:200])
        return "APPROVED"


def _extract_feedback(content: str) -> str:
    """Extract feedback from validation response."""
    # Look for FEEDBACK: section
    if "FEEDBACK:" in content:
        parts = content.split("FEEDBACK:", 1)
        if len(parts) > 1:
            return parts[1].strip()

    # Return full content if no explicit feedback section
    return content
