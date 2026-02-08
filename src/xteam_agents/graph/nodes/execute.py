"""Worker agent node."""

from __future__ import annotations

from typing import Any, Callable, Optional

import structlog
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph

from xteam_agents.action.executor import ActionExecutor
from xteam_agents.config import Settings
from xteam_agents.graph.prompts import WORKER_SYSTEM_PROMPT, DYNAMIC_PERSONA_TEMPLATE
from xteam_agents.integration.executor import UnifiedExecutor
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.llm.tools import create_action_tools, create_memory_tools
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState, SubTaskStatus

logger = structlog.get_logger()

def _get_tools_for_agent(
    agent_name: str,
    memory_manager: MemoryManager,
    action_executor: ActionExecutor,
    mcp_dummy_object: Any = None # We might need a dummy object if tools require 'mcp'
) -> list[Any]:
    """Get the appropriate toolset for an agent."""
    
    # Base tools available to everyone
    memory_tools = create_memory_tools(memory_manager)
    action_tools = create_action_tools(action_executor)
    
    # Specialized tools
    # Note: We need to adapt the MCP tools to LangChain tools
    # This is complex because our tools are written for FastMCP.
    # For now, we'll stick to the base tools + action executor which can wrap capabilities.
    # BUT, we added direct python/web tools. We should expose them via action executor
    # or wrap them here.
    
    # Ideally, we should refactor the tools to be framework-agnostic, 
    # but for now let's rely on the ActionExecutor to expose them if registered there,
    # OR we can wrap them on the fly if needed.
    
    # For this implementation, we will assume ActionExecutor has been updated to include
    # the new capabilities, OR we add them to the tool list if they are simple functions.
    
    return memory_tools + action_tools


def create_execute_node(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
    action_executor: ActionExecutor,
    adversarial_graph: Optional[StateGraph] = None,
    settings: Optional[Settings] = None,
    magic_core: Any | None = None,
) -> Callable[[AgentState], AgentState]:
    """
    Create the execute node function.

    The Worker agent:
    - Executes the plan created by the Architect
    - Uses action tools to perform work
    - Records results in episodic memory
    - Does NOT write to shared memory

    Integration with Adversarial Team:
    - For complex/critical tasks, uses UnifiedExecutor which routes to Adversarial Team
    - For simple/medium tasks, uses standard execution with dynamic personas

    Supports DYNAMIC PERSONAS:
    - If a subtask has an 'assigned_agent', the worker adopts that persona.
    """

    # Initialize UnifiedExecutor if adversarial_graph is provided
    unified_executor = None
    if adversarial_graph and settings:
        unified_executor = UnifiedExecutor(
            llm_provider,
            memory_manager,
            action_executor,
            adversarial_graph,
            settings,
        )

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

        # Route to UnifiedExecutor for complex/critical tasks
        complexity = state.context.get("complexity", "simple")
        if unified_executor and complexity in ["complex", "critical"]:
            logger.info(
                "routing_to_unified_executor",
                task_id=str(state.task_id),
                complexity=complexity,
            )
            return await unified_executor.execute(state)

        # Standard execution for simple/medium tasks
        logger.info(
            "using_standard_execution",
            task_id=str(state.task_id),
            complexity=complexity,
        )

        # Get pending subtasks
        pending_subtasks = state.get_pending_subtasks()
        
        # We process one subtask at a time to allow for persona switching
        # If there are multiple pending, we take the first one
        if not pending_subtasks:
            return {
                "execution_result": "No pending subtasks.",
                "current_node": "validate",
            }
            
        current_subtask = pending_subtasks[0]
        
        # Determine Persona
        persona_name = current_subtask.assigned_agent or "Worker"
        
        system_prompt = WORKER_SYSTEM_PROMPT
        if current_subtask.assigned_agent:
            # Construct dynamic persona prompt
            # We would typically look up the persona description from memory or config
            # For now, we'll infer a generic expert persona
            system_prompt = DYNAMIC_PERSONA_TEMPLATE.format(
                persona_name=persona_name,
                persona_description=f"You are an expert {persona_name}. You have deep knowledge in your field and use specialized tools to solve problems efficiently.",
                task_context=state.description
            )
            logger.info("using_dynamic_persona", persona=persona_name, subtask=current_subtask.description)

        # Get tools
        # Ideally we would filter tools based on persona, but for now we give full access
        memory_tools = create_memory_tools(memory_manager)
        action_tools = create_action_tools(action_executor)
        
        # TODO: Add the new specialized tools (web, code, fs) to the toolset
        # Currently they are registered to MCP but not directly to LangChain here.
        # We need to bridge them. For this iteration, we'll rely on the existing action executor mechanism
        # or assume the user will use 'execute_action' which might wrap them.
        # TO FIX: We need to explicitly add the tool functions if we want the LLM to call them directly.
        # Since we defined them inside 'register_X_tools' functions which take 'mcp' object,
        # we can't easily import them here without refactoring.
        # For now, we will proceed with the standard toolset.
        
        all_tools = memory_tools + action_tools

        # Get the model with tools
        # We use the persona name to potentially get a specialized model in the future
        model = llm_provider.get_model_for_agent(persona_name)
        model_with_tools = model.bind_tools(all_tools)

        # Build the execution prompt
        task_prompt = f"""
Task: {state.description}

Current Subtask to Execute:
[{current_subtask.status.value}] {current_subtask.description}

Plan Context:
{state.plan}

Please execute ONLY this specific subtask.
1. Verify prerequisites
2. Execute required actions
3. Verify success criteria
4. Report the result

Available capabilities can be listed using the list_capabilities tool.
Use execute_action to perform actions.

Report your execution results clearly.
"""

        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_prompt},
        ]

        # Execution loop - allow multiple tool calls
        max_tool_iterations = 10
        execution_results = []
        updated_subtasks = list(state.subtasks)
        
        # Find index of current subtask
        subtask_index = next((i for i, st in enumerate(updated_subtasks) if st.id == current_subtask.id), -1)

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

        # Mark current subtask as completed
        # In a more advanced implementation, we would parse the LLM's output to see if it actually succeeded
        # For now, we assume if it finished, it's done. The Reviewer will validate it.
        if subtask_index != -1:
             updated_subtasks[subtask_index] = updated_subtasks[subtask_index].mark_completed(execution_result)
        
        # Check if there are more pending subtasks
        more_pending = any(st.status == SubTaskStatus.PENDING for st in updated_subtasks)
        
        # If there are more pending subtasks, we loop back to execute
        # otherwise we go to validate
        next_node = "execute" if more_pending else "validate"
        
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

        # MAGIC: assess confidence if enabled
        state_updates: dict[str, Any] = {
            "execution_result": execution_result,
            "subtasks": updated_subtasks,
            "artifacts": artifacts,
            "current_node": next_node,
            "messages": state.messages + [AIMessage(content=execution_result)],
        }

        if magic_core and state.magic_config and state.magic_config.enabled:
            try:
                confidence = await magic_core.assess_confidence(
                    str(state.task_id),
                    "execute",
                    execution_result,
                    state.description,
                )
                state_updates["confidence_scores"] = {
                    **state.confidence_scores,
                    "execute": confidence.to_dict(),
                }
            except Exception as e:
                logger.warning("magic_confidence_assess_failed", error=str(e))

        return state_updates

    return execute_node
