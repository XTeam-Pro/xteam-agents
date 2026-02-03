"""Unified executor that routes between standard and adversarial execution."""

from typing import Any

import structlog
from langgraph.graph import StateGraph

from xteam_agents.action.executor import ActionExecutor
from xteam_agents.config import Settings
from xteam_agents.integration.state_adapter import StateAdapter
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


class UnifiedExecutor:
    """
    Unified executor that routes to standard or adversarial mode.

    Routing logic:
    - simple/medium complexity → Standard execution (single LLM call)
    - complex/critical complexity → Adversarial execution (Agent Team)
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        memory_manager: MemoryManager,
        action_executor: ActionExecutor,
        adversarial_graph: StateGraph | None,
        settings: Settings,
    ):
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
        self.action_executor = action_executor
        self.adversarial_graph = adversarial_graph
        self.settings = settings
        self.logger = logger.bind(component="UnifiedExecutor")

    async def execute(self, state: AgentState) -> dict[str, Any]:
        """
        Execute task using appropriate mode based on complexity.

        Args:
            state: Current agent state

        Returns:
            State updates dictionary
        """
        complexity = state.context.get("complexity", "simple")

        self.logger.info(
            "unified_executor_routing",
            task_id=str(state.task_id),
            complexity=complexity,
        )

        # Log routing decision
        await self.memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_ENTERED,
                agent_name="executor",
                node_name="execute",
                description=f"Routing to {'adversarial' if complexity in ['complex', 'critical'] else 'standard'} execution",
                data={"complexity": complexity},
            )
        )

        # Route based on complexity
        if complexity in ["complex", "critical"]:
            return await self.execute_adversarial(state)
        else:
            return await self.execute_standard(state)

    async def execute_standard(self, state: AgentState) -> dict[str, Any]:
        """
        Standard execution using single LLM call.

        This is the lightweight path for simple and medium tasks.

        Args:
            state: Current agent state

        Returns:
            State updates dictionary
        """
        self.logger.info(
            "standard_execution_start",
            task_id=str(state.task_id),
        )

        # Get the executor model
        model = self.llm_provider.get_model_for_agent("executor")

        # Build execution prompt
        execution_prompt = self._build_standard_execution_prompt(state)

        # Invoke LLM
        try:
            response = await model.ainvoke([
                {"role": "system", "content": self._get_standard_system_prompt()},
                {"role": "user", "content": execution_prompt},
            ])

            execution_result = response.content if hasattr(response, "content") else str(response)

            self.logger.info(
                "standard_execution_complete",
                task_id=str(state.task_id),
                result_length=len(execution_result),
            )

            # Log completion
            await self.memory_manager.log_audit(
                AuditEntry(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    event_type=AuditEventType.NODE_EXITED,
                    agent_name="executor",
                    node_name="execute",
                    description="Standard execution completed",
                )
            )

            return {
                "execution_result": execution_result,
                "current_node": "validate",
            }

        except Exception as e:
            self.logger.error("standard_execution_failed", error=str(e))
            return {
                "error": f"Standard execution failed: {str(e)}",
                "is_failed": True,
            }

    async def execute_adversarial(self, state: AgentState) -> dict[str, Any]:
        """
        Adversarial execution using Agent Team.

        This is the high-quality path for complex and critical tasks.

        Args:
            state: Current agent state

        Returns:
            State updates dictionary
        """
        self.logger.info(
            "adversarial_execution_start",
            task_id=str(state.task_id),
        )

        if not self.adversarial_graph:
            self.logger.error("adversarial_graph_not_initialized")
            return {
                "error": "Adversarial graph not initialized",
                "is_failed": True,
            }

        try:
            # Convert AgentState to AdversarialAgentState
            adversarial_state = StateAdapter.to_adversarial(state)

            self.logger.debug(
                "adversarial_state_converted",
                task_id=str(state.task_id),
            )

            # Execute adversarial graph
            result = await self.adversarial_graph.ainvoke(adversarial_state)

            self.logger.info(
                "adversarial_execution_complete",
                task_id=str(state.task_id),
                approved=result.orchestrator_final_decision.approved if result.orchestrator_final_decision else False,
            )

            # Convert result back to AgentState updates
            updates = StateAdapter.from_adversarial(result, state)

            # Log completion
            await self.memory_manager.log_audit(
                AuditEntry(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    event_type=AuditEventType.NODE_EXITED,
                    agent_name="executor",
                    node_name="execute",
                    description="Adversarial execution completed",
                    data={
                        "approved": updates.get("is_validated", False),
                        "quality_score": state.context.get("adversarial_execution", {}).get("quality_score"),
                    },
                )
            )

            # Add current_node if not failed
            if not updates.get("is_failed"):
                updates["current_node"] = "validate"

            return updates

        except Exception as e:
            self.logger.error("adversarial_execution_failed", error=str(e))
            return {
                "error": f"Adversarial execution failed: {str(e)}",
                "is_failed": True,
            }

    def _build_standard_execution_prompt(self, state: AgentState) -> str:
        """Build execution prompt for standard mode."""
        prompt = f"""
TASK: {state.description}

CONTEXT: {state.context}

ANALYSIS:
{state.analysis or 'No analysis available'}

PLAN:
{state.plan or 'No plan available'}

SUBTASKS:
"""
        for subtask in state.subtasks:
            prompt += f"- {subtask.description} ({subtask.status.value})\n"

        prompt += """

Execute the task according to the plan. Provide:
1. Implementation details
2. Code/configuration if applicable
3. Steps taken
4. Results

Be thorough and precise.
"""
        return prompt

    def _get_standard_system_prompt(self) -> str:
        """Get system prompt for standard execution."""
        return """You are an Executor agent responsible for implementing tasks.

Your role:
- Follow the plan provided
- Execute tasks methodically
- Produce high-quality results
- Document your work clearly

Focus on correctness, completeness, and clarity."""
