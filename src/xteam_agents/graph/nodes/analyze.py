"""Analyst agent node."""

from typing import Any, Callable

import structlog
from langchain_core.messages import AIMessage, HumanMessage

from xteam_agents.graph.prompts import ANALYST_SYSTEM_PROMPT
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.llm.tools import create_memory_tools
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


def create_analyze_node(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
) -> Callable[[AgentState], AgentState]:
    """
    Create the analyze node function.

    The Analyst agent:
    - Reads memory to understand context
    - Analyzes the task requirements
    - Produces an analysis for the Architect
    - Does NOT write to shared memory (only episodic)
    """

    async def analyze_node(state: AgentState) -> dict[str, Any]:
        """Execute the analyze node."""
        logger.info(
            "analyze_node_enter",
            task_id=str(state.task_id),
            iteration=state.iteration_count,
        )

        # Log entry to audit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_ENTERED,
                agent_name="analyst",
                node_name="analyze",
                description="Entered analyze node",
                data={"iteration": state.iteration_count},
            )
        )

        # Get memory tools (read-only)
        memory_tools = create_memory_tools(memory_manager)

        # Get the model with tools
        model = llm_provider.get_model_for_agent("analyst")
        model_with_tools = model.bind_tools(memory_tools)

        # Build the prompt
        task_prompt = f"""
Task Description: {state.description}

Context: {state.context}

Priority: {state.priority}

Please analyze this task thoroughly. Use the available tools to search for
relevant knowledge and context from past tasks.

Provide a comprehensive analysis covering:
1. Task Understanding
2. Requirements (explicit and implicit)
3. Constraints
4. Dependencies
5. Risks and potential challenges
6. Relevant knowledge from memory
"""

        # Create messages
        messages = [
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt},
        ]

        # Add any existing messages from state for context
        for msg in state.messages[-5:]:  # Last 5 messages for context
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})

        # Invoke the model (may have tool calls)
        response = await model_with_tools.ainvoke(messages)

        # Handle tool calls if any
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Execute tool calls
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Find and execute the tool
                for tool in memory_tools:
                    if tool.name == tool_name:
                        result = await tool.ainvoke(tool_args)
                        tool_results.append(f"{tool_name}: {result}")
                        break

            # Add tool results to messages and get final response
            messages.append({"role": "assistant", "content": str(response.content)})
            messages.append({
                "role": "user",
                "content": f"Tool results:\n" + "\n".join(tool_results),
            })

            response = await model.ainvoke(messages)

        # Extract analysis from response
        analysis = response.content if hasattr(response, "content") else str(response)

        # Store analysis in episodic memory (private, no validation needed)
        await memory_manager.store_episodic(
            MemoryArtifact(
                task_id=state.task_id,
                session_id=state.session_id,
                content=analysis,
                content_type="analysis",
                memory_type=MemoryType.EPISODIC,
                scope=MemoryScope.PRIVATE,
                created_by="analyst",
                metadata={"iteration": state.iteration_count},
            )
        )

        # Log exit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_EXITED,
                agent_name="analyst",
                node_name="analyze",
                description="Completed analysis",
            )
        )

        logger.info(
            "analyze_node_complete",
            task_id=str(state.task_id),
            analysis_length=len(analysis),
        )

        # Return state updates
        return {
            "analysis": analysis,
            "current_node": "plan",
            "messages": state.messages + [AIMessage(content=analysis)],
        }

    return analyze_node
