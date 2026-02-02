"""Architect agent node."""

import json
from typing import Any, Callable

import structlog
from langchain_core.messages import AIMessage

from xteam_agents.graph.prompts import ARCHITECT_SYSTEM_PROMPT
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.llm.tools import create_memory_tools
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState, SubTask

logger = structlog.get_logger()


def create_plan_node(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
) -> Callable[[AgentState], AgentState]:
    """
    Create the plan node function.

    The Architect agent:
    - Reviews the Analyst's analysis
    - Designs a solution approach
    - Creates subtasks for execution
    - Does NOT write to shared memory (only episodic)
    """

    async def plan_node(state: AgentState) -> dict[str, Any]:
        """Execute the plan node."""
        logger.info(
            "plan_node_enter",
            task_id=str(state.task_id),
            iteration=state.iteration_count,
            is_replan=state.should_replan,
        )

        # Log entry to audit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_ENTERED,
                agent_name="architect",
                node_name="plan",
                description="Entered plan node" + (" (replan)" if state.should_replan else ""),
            )
        )

        # Get memory tools (read-only)
        memory_tools = create_memory_tools(memory_manager)

        # Get the model with tools
        model = llm_provider.get_model_for_agent("architect")
        model_with_tools = model.bind_tools(memory_tools)

        # Build the prompt
        replan_context = ""
        if state.should_replan and state.validation_feedback:
            replan_context = f"""
IMPORTANT: This is a REPLAN. The previous execution was not validated.

Validation Feedback:
{state.validation_feedback}

Previous Plan:
{state.plan}

Please revise the plan to address the feedback.
"""

        task_prompt = f"""
Task Description: {state.description}

Analysis from Analyst:
{state.analysis}

Context: {state.context}

{replan_context}

Please design a solution and create an execution plan.

Your plan should include:
1. Solution Overview
2. Subtasks (as a JSON array with 'description', 'success_criteria', and optional 'assigned_agent' fields)
3. Required Capabilities
4. Validation Strategy
5. Rollback Plan

IMPORTANT: Format your subtasks as a JSON array like this:
```json
[
    {{"description": "Analyze dataset", "success_criteria": "Stats generated", "assigned_agent": "PythonDataAnalyst"}},
    {{"description": "Search for API docs", "success_criteria": "Docs found", "assigned_agent": "WebResearcher"}}
]
```
"""

        # Create messages
        messages = [
            {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
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

        # Extract plan from response
        plan = response.content if hasattr(response, "content") else str(response)

        # Parse subtasks from the plan
        subtasks = _extract_subtasks(plan)

        # Store plan in episodic memory (private)
        await memory_manager.store_episodic(
            MemoryArtifact(
                task_id=state.task_id,
                session_id=state.session_id,
                content=plan,
                content_type="plan",
                memory_type=MemoryType.EPISODIC,
                scope=MemoryScope.PRIVATE,
                created_by="architect",
                metadata={
                    "iteration": state.iteration_count,
                    "is_replan": state.should_replan,
                    "subtask_count": len(subtasks),
                },
            )
        )

        # Log exit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_EXITED,
                agent_name="architect",
                node_name="plan",
                description=f"Created plan with {len(subtasks)} subtasks",
            )
        )

        logger.info(
            "plan_node_complete",
            task_id=str(state.task_id),
            subtask_count=len(subtasks),
        )

        # Return state updates
        return {
            "plan": plan,
            "subtasks": subtasks,
            "current_node": "execute",
            "should_replan": False,  # Reset replan flag
            "messages": state.messages + [AIMessage(content=plan)],
        }

    return plan_node


def _extract_subtasks(plan: str) -> list[SubTask]:
    """
    Extract subtasks from the plan.

    Looks for JSON array in the plan content.
    """
    subtasks: list[SubTask] = []

    # Try to find JSON array in the plan
    try:
        # Look for JSON array between ```json and ```
        import re
        json_match = re.search(r"```json\s*(\[[\s\S]*?\])\s*```", plan)
        if json_match:
            subtasks_data = json.loads(json_match.group(1))
            for item in subtasks_data:
                subtasks.append(
                    SubTask(
                        description=item.get("description", ""),
                        assigned_agent=item.get("assigned_agent"),
                    )
                )
    except (json.JSONDecodeError, AttributeError):
        # If JSON parsing fails, create a single subtask
        logger.warning("failed_to_parse_subtasks", plan_preview=plan[:200])
        subtasks.append(
            SubTask(description="Execute the plan as described")
        )

    # Ensure we have at least one subtask
    if not subtasks:
        subtasks.append(
            SubTask(description="Execute the plan as described")
        )

    return subtasks
