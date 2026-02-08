"""Analyst agent node."""

from __future__ import annotations

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
    magic_core: Any | None = None,
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

        # Retrieve Guidelines from Memory
        # We search for "guideline" artifacts
        guidelines_text = "No specific guidelines found."
        try:
            # We use semantic search for "guideline" or generic query, but filter by metadata in a real scenario
            # Here we just do a semantic search for "guideline error failure rule" to find relevant ones
            # Or better, we search for context related to current task AND include "guideline" in query
            guideline_results = await memory_manager.search_knowledge(
                f"guideline rule for {state.description}", 
                limit=5
            )
            if guideline_results:
                # Filter strictly for guidelines if possible, or just use top results
                guidelines_list = [
                    f"- {g.content}" 
                    for g in guideline_results 
                    if g.metadata.get("type") == "guideline" or "Rule:" in g.content
                ]
                if guidelines_list:
                    guidelines_text = "\n".join(guidelines_list)
        except Exception as e:
            logger.warning("guideline_retrieval_failed", error=str(e))

        # Build the prompt
        task_prompt = f"""
Task Description: {state.description}

Context: {state.context}

Priority: {state.priority}

SYSTEM GUIDELINES (Learned from past experience):
{guidelines_text}

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

        # Classify task complexity for execution routing
        complexity = await _classify_task_complexity(
            llm_provider,
            state.description,
            analysis,
        )
        logger.info("task_complexity_classified", complexity=complexity)

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

        # MAGIC: assess confidence if enabled
        state_updates: dict[str, Any] = {
            "analysis": analysis,
            "current_node": "plan",
            "messages": state.messages + [AIMessage(content=analysis)],
            "context": {
                **state.context,
                "complexity": complexity,
            },
        }

        if magic_core and state.magic_config and state.magic_config.enabled:
            try:
                confidence = await magic_core.assess_confidence(
                    str(state.task_id), "analyze", analysis, state.description
                )
                state_updates["confidence_scores"] = {
                    **state.confidence_scores,
                    "analyze": confidence.to_dict(),
                }
            except Exception as e:
                logger.warning("magic_confidence_assess_failed", error=str(e))

        return state_updates

    return analyze_node


async def _classify_task_complexity(
    llm_provider: LLMProvider,
    task_description: str,
    analysis: str,
) -> str:
    """
    Classify task complexity for execution routing.

    Returns: "simple", "medium", "complex", or "critical"
    """
    model = llm_provider.get_model_for_agent("analyst")

    classification_prompt = f"""
Classify the complexity of this task based on the description and analysis.

TASK DESCRIPTION:
{task_description}

ANALYSIS:
{analysis}

COMPLEXITY LEVELS:
- **simple**: Single straightforward operation, minimal decision-making
  Examples: Fix typo, add logging, update config value

- **medium**: Multiple operations, some decision-making, standard patterns
  Examples: Add simple API endpoint, write unit tests, refactor single file

- **complex**: Architectural decisions, multiple components, requires expert review
  Examples: Design new feature, refactor module, implement security measure

- **critical**: High-risk, system-wide impact, requires multiple expert reviews
  Examples: Change authentication system, database migration, security audit

Based on the above, classify this task. Consider:
1. Number of components affected
2. Architectural decisions needed
3. Risk level
4. Need for expert review

Respond with ONLY ONE WORD: simple, medium, complex, or critical
"""

    try:
        response = await model.ainvoke([{"role": "user", "content": classification_prompt}])
        complexity = response.content.strip().lower()

        # Validate response
        if complexity not in ["simple", "medium", "complex", "critical"]:
            logger.warning(
                "invalid_complexity_classification",
                raw_response=complexity,
                defaulting_to="medium",
            )
            return "medium"

        return complexity
    except Exception as e:
        logger.error("complexity_classification_failed", error=str(e))
        # Default to medium complexity on error
        return "medium"
