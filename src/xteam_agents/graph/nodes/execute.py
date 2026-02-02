"""Worker agent node."""

from typing import Any, Callable

import structlog
from langchain_core.messages import AIMessage

from xteam_agents.action.executor import ActionExecutor
from xteam_agents.graph.prompts import WORKER_SYSTEM_PROMPT
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.llm.tools import create_action_tools, create_memory_tools
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState, SubTaskStatus

logger = structlog.get_logger()


def create_execute_node(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
    action_executor: ActionExecutor,
) -> Callable[[AgentState], AgentState]:
    """
    Create the execute node function.

    The Worker agent:
    - Executes the plan created by the Architect
    - Uses action tools to perform work
    - Records results in episodic memory
    - Does NOT write to shared memory
    """

    async def execute_node(state: AgentState) -> dict[str, Any]:
        """Execute the execute node."""
        logger.info(
            "execute_node_enter",
            task_id=str(state.task_id),
            iteration=state.iteration_count,
            subtask_count=len(state.subtasks),
        )

        # Log entry to audit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_ENTERED,
                agent_name="worker",
                node_name="execute",
                description=f"Entered execute node with {len(state.subtasks)} subtasks",
            )
        )

        # Get tools
        memory_tools = create_memory_tools(memory_manager)
        action_tools = create_action_tools(action_executor)
        all_tools = memory_tools + action_tools

        # Get the model with tools
        model = llm_provider.get_model_for_agent("worker")
        model_with_tools = model.bind_tools(all_tools)

        # Get pending subtasks
        pending_subtasks = state.get_pending_subtasks()

        # Build the execution prompt
        subtask_list = "\n".join(
            f"- [{st.status.value}] {st.description}"
            for st in state.subtasks
        )

        task_prompt = f"""
Task: {state.description}

Plan:
{state.plan}

Subtasks:
{subtask_list}

Please execute the pending subtasks. For each subtask:
1. Verify prerequisites
2. Execute required actions using the available tools
3. Verify success criteria
4. Report the result

Available capabilities can be listed using the list_capabilities tool.
Use execute_action to perform actions.

Report your execution results clearly.
"""

        # Create messages
        messages = [
            {"role": "system", "content": WORKER_SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt},
        ]

        # Execution loop - allow multiple tool calls
        max_tool_iterations = 10
        execution_results = []
        updated_subtasks = list(state.subtasks)
        artifacts = list(state.artifacts)

        for iteration in range(max_tool_iterations):
            response = await model_with_tools.ainvoke(messages)

            if not hasattr(response, "tool_calls") or not response.tool_calls:
                # No more tool calls, done executing
                break

            # Execute tool calls
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Log action request
                if tool_name == "execute_action":
                    await memory_manager.log_audit(
                        AuditEntry(
                            task_id=state.task_id,
                            session_id=state.session_id,
                            event_type=AuditEventType.ACTION_REQUESTED,
                            agent_name="worker",
                            node_name="execute",
                            description=f"Requested action: {tool_args.get('capability_name', 'unknown')}",
                            data=tool_args,
                        )
                    )

                # Find and execute the tool
                result = None
                for tool in all_tools:
                    if tool.name == tool_name:
                        try:
                            # Add task_id to args if needed
                            if "task_id" in tool_args and tool_args["task_id"] is None:
                                tool_args["task_id"] = str(state.task_id)
                            elif tool_name == "execute_action" and "task_id" not in tool_args:
                                tool_args["task_id"] = str(state.task_id)

                            result = await tool.ainvoke(tool_args)
                            tool_results.append(f"{tool_name}: {result}")

                            # Log action completion
                            if tool_name == "execute_action":
                                success = result.get("success", False) if isinstance(result, dict) else True
                                await memory_manager.log_audit(
                                    AuditEntry(
                                        task_id=state.task_id,
                                        session_id=state.session_id,
                                        event_type=(
                                            AuditEventType.ACTION_COMPLETED
                                            if success
                                            else AuditEventType.ACTION_FAILED
                                        ),
                                        agent_name="worker",
                                        node_name="execute",
                                        description=f"Action completed: {tool_args.get('capability_name', 'unknown')}",
                                        data={"result": str(result)[:500]},
                                    )
                                )

                            execution_results.append({
                                "tool": tool_name,
                                "args": tool_args,
                                "result": result,
                            })

                        except Exception as e:
                            result = f"Error: {str(e)}"
                            tool_results.append(f"{tool_name}: {result}")
                            logger.error(
                                "tool_execution_error",
                                tool=tool_name,
                                error=str(e),
                            )
                        break

            # Add to messages for next iteration
            messages.append({"role": "assistant", "content": str(response.content)})
            messages.append({
                "role": "user",
                "content": f"Tool results:\n" + "\n".join(tool_results),
            })

        # Get final response summarizing execution
        final_response = await model.ainvoke(messages)
        execution_result = (
            final_response.content
            if hasattr(final_response, "content")
            else str(final_response)
        )

        # Mark subtasks as completed (simplified - in reality would check success)
        for i, subtask in enumerate(updated_subtasks):
            if subtask.status == SubTaskStatus.PENDING:
                updated_subtasks[i] = subtask.mark_completed("Executed")

        # Store execution result in episodic memory
        await memory_manager.store_episodic(
            MemoryArtifact(
                task_id=state.task_id,
                session_id=state.session_id,
                content=execution_result,
                content_type="execution_result",
                memory_type=MemoryType.EPISODIC,
                scope=MemoryScope.PRIVATE,
                created_by="worker",
                metadata={
                    "iteration": state.iteration_count,
                    "action_count": len(execution_results),
                },
            )
        )

        # Log exit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_EXITED,
                agent_name="worker",
                node_name="execute",
                description=f"Completed execution with {len(execution_results)} actions",
            )
        )

        logger.info(
            "execute_node_complete",
            task_id=str(state.task_id),
            action_count=len(execution_results),
        )

        # Return state updates
        return {
            "execution_result": execution_result,
            "subtasks": updated_subtasks,
            "artifacts": artifacts,
            "current_node": "validate",
            "messages": state.messages + [AIMessage(content=execution_result)],
        }

    return execute_node
