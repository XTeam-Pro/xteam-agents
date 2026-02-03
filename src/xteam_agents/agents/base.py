"""Base classes for Agent and Critic in adversarial system."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config import Settings
from .adversarial_config import AgentConfig, AgentRole, CriticEvaluation
from .adversarial_state import AdversarialAgentState, AgentOutput, CriticReview

if TYPE_CHECKING:
    from ..memory.manager import MemoryManager

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all action agents."""

    def __init__(
        self,
        config: AgentConfig,
        settings: Settings,
        memory_manager: Optional["MemoryManager"] = None,
        llm: Optional[Any] = None,
    ):
        self.config = config
        self.settings = settings
        self.memory_manager = memory_manager
        self.logger = logger.bind(agent=config.role.value)

        # Initialize LLM (use provided or create new)
        self.llm = llm if llm is not None else self._create_llm()

    def _create_llm(self):
        """Create LLM instance based on configuration."""
        if self.settings.llm_provider == "anthropic":
            return ChatAnthropic(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                anthropic_api_key=self.settings.anthropic_api_key,
            )
        else:
            return ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                openai_api_key=self.settings.openai_api_key,
            )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    @abstractmethod
    def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute agent's task and return output."""
        pass

    def _build_messages(
        self,
        state: AdversarialAgentState,
        user_message: str,
        previous_feedback: Optional[str] = None,
    ) -> list[BaseMessage]:
        """Build message list for LLM."""
        messages = [SystemMessage(content=self.get_system_prompt())]

        # Add task context
        context_msg = f"""
Task ID: {state.task_id}
Original Request: {state.original_request}

Current Phase: {state.current_phase}
"""
        if state.orchestrator_decision:
            context_msg += f"""
Orchestrator Decision:
- Scope: {state.orchestrator_decision.task_summary}
- Constraints: {', '.join(state.orchestrator_decision.constraints)}
- Success Criteria: {', '.join(state.orchestrator_decision.success_criteria)}
"""

        messages.append(HumanMessage(content=context_msg))

        # Add previous feedback if available
        if previous_feedback:
            messages.append(
                HumanMessage(
                    content=f"Previous Feedback from Critic:\n{previous_feedback}"
                )
            )

        # Add current task
        messages.append(HumanMessage(content=user_message))

        return messages

    async def invoke_llm(self, messages: list[BaseMessage]) -> str:
        """Invoke LLM with messages."""
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            self.logger.error("LLM invocation failed", error=str(e))
            raise


class BaseCritic(ABC):
    """Base class for all critic agents."""

    def __init__(
        self,
        config: AgentConfig,
        settings: Settings,
        memory_manager: Optional["MemoryManager"] = None,
        llm: Optional[Any] = None,
    ):
        self.config = config
        self.settings = settings
        self.memory_manager = memory_manager
        self.logger = logger.bind(critic=config.role.value)

        # Initialize LLM (use provided or create new)
        self.llm = llm if llm is not None else self._create_llm()

    def _create_llm(self):
        """Create LLM instance based on configuration."""
        if self.settings.llm_provider == "anthropic":
            return ChatAnthropic(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                anthropic_api_key=self.settings.anthropic_api_key,
            )
        else:
            return ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                openai_api_key=self.settings.openai_api_key,
            )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this critic."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate agent's output and return review."""
        pass

    def _build_evaluation_prompt(
        self, state: AdversarialAgentState, agent_output: AgentOutput
    ) -> str:
        """Build evaluation prompt for critic."""
        prompt = f"""
You are evaluating the following output from {agent_output.agent_role.value}.

TASK CONTEXT:
{state.original_request}

AGENT'S OUTPUT:
{self._format_agent_output(agent_output)}

ITERATION: {agent_output.iteration}

EVALUATE on 5 dimensions (0-10 scale):
1. Correctness - Is it technically correct?
2. Completeness - Are all requirements addressed?
3. Quality - Is the code/design quality acceptable?
4. Performance - Are performance considerations addressed?
5. Security - Are security considerations met?

Provide:
- Score for each dimension (0-10)
- Detailed feedback
- Specific concerns (if any)
- Suggestions for improvement

Format your response as JSON:
{{
    "correctness": <0-10>,
    "completeness": <0-10>,
    "quality": <0-10>,
    "performance": <0-10>,
    "security": <0-10>,
    "feedback": "detailed feedback here",
    "concerns": ["concern 1", "concern 2"],
    "suggestions": ["suggestion 1", "suggestion 2"],
    "decision": "APPROVED" or "REJECTED" or "REQUEST_REVISION"
}}
"""
        return prompt

    def _format_agent_output(self, agent_output: AgentOutput) -> str:
        """Format agent output for evaluation."""
        output_str = f"Rationale: {agent_output.rationale}\n\n"

        if agent_output.changes_from_previous:
            output_str += f"Changes from previous iteration:\n{agent_output.changes_from_previous}\n\n"

        output_str += "Content:\n"
        for key, value in agent_output.content.items():
            output_str += f"- {key}: {value}\n"

        return output_str

    async def invoke_llm(self, messages: list[BaseMessage]) -> str:
        """Invoke LLM with messages."""
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            self.logger.error("LLM invocation failed", error=str(e))
            raise

    def _parse_evaluation_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response into evaluation dict."""
        import json

        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback: create default evaluation
                return self._create_default_evaluation(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse evaluation JSON", response=response)
            return self._create_default_evaluation(response)

    def _create_default_evaluation(self, response: str) -> dict[str, Any]:
        """Create default evaluation when parsing fails."""
        return {
            "correctness": 5.0,
            "completeness": 5.0,
            "quality": 5.0,
            "performance": 5.0,
            "security": 5.0,
            "feedback": response,
            "concerns": ["Could not parse evaluation properly"],
            "suggestions": ["Please review manually"],
            "decision": "REQUEST_REVISION",
        }
