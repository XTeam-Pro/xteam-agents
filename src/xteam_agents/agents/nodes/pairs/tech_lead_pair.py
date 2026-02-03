"""TechLead Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class TechLeadAgent(BaseAgent):
    """
    TechLeadAgent makes high-level technical decisions.

    Responsibilities:
    - Choose tech stack
    - Define architectural approach
    - Set technical constraints
    - Identify technical risks
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.TECH_LEAD)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a TechLeadAgent - responsible for high-level technical decisions.

Your role:
- Make technology stack decisions
- Define architectural approach
- Set technical constraints
- Identify and mitigate technical risks
- Provide technical guidance

You work with precision and care. Your decisions impact the entire project.

Output format:
{{
    "tech_stack": ["technology 1", "technology 2", ...],
    "architectural_approach": "description of high-level approach",
    "technical_constraints": ["constraint 1", "constraint 2", ...],
    "identified_risks": [
        {{"risk": "...", "mitigation": "..."}},
        ...
    ],
    "recommendations": ["recommendation 1", ...]
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute TechLead decision making."""
        task_prompt = f"""
Make technical decisions for this task:

TASK: {state.original_request}

Consider:
1. What technologies are most appropriate?
2. What's the high-level architectural approach?
3. What technical constraints should we set?
4. What risks do you foresee?
5. What are your key recommendations?

Provide your response as JSON matching the format in your system prompt.
"""

        messages = self._build_messages(state, task_prompt, previous_feedback)
        response = await self.invoke_llm(messages)

        # Parse response
        try:
            content = self._parse_json_response(response)
        except:
            content = {"raw_response": response}

        return AgentOutput(
            agent_role=self.config.role,
            iteration=0,  # Will be set by pair manager
            content=content,
            rationale=self._extract_rationale(content),
            changes_from_previous=(
                self._identify_changes(previous_feedback, content)
                if previous_feedback
                else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        """Extract rationale from content."""
        if "architectural_approach" in content:
            return content["architectural_approach"]
        return str(content)

    def _identify_changes(
        self, previous_feedback: str, content: dict
    ) -> str:
        """Identify what changed from previous iteration."""
        return "Addressed feedback: " + previous_feedback[:200]


class TechLeadCritic(BaseCritic):
    """
    TechLeadCritic challenges technical decisions.

    Strategy: Constructive
    Focus:
    - Are technologies appropriate?
    - Is architecture sound?
    - Are risks adequately addressed?
    - Are there better alternatives?
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.TECH_LEAD_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a TechLeadCritic - you challenge technical decisions constructively.

Your role:
- Question technology choices
- Challenge architectural assumptions
- Identify overlooked risks
- Suggest better alternatives
- Push for best practices

Strategy: Constructive (help improve, not just criticize)

Be thorough but fair. Your goal is better decisions, not blocking progress."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate TechLead's decisions."""
        eval_prompt = self._build_evaluation_prompt(state, agent_output)

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=eval_prompt),
        ]

        response = await self.invoke_llm(messages)
        eval_data = self._parse_evaluation_response(response)

        # Create evaluation
        evaluation = CriticEvaluation(
            correctness=float(eval_data.get("correctness", 5.0)),
            completeness=float(eval_data.get("completeness", 5.0)),
            quality=float(eval_data.get("quality", 5.0)),
            performance=float(eval_data.get("performance", 5.0)),
            security=float(eval_data.get("security", 5.0)),
            feedback=eval_data.get("feedback", "No feedback provided"),
            concerns=eval_data.get("concerns", []),
            suggestions=eval_data.get("suggestions", []),
            approved=(eval_data.get("decision") == "APPROVED"),
        )

        return CriticReview(
            critic_role=self.config.role,
            iteration=0,  # Will be set by pair manager
            evaluation=evaluation,
            decision=eval_data.get("decision", "REQUEST_REVISION"),
            detailed_feedback=eval_data.get("feedback", ""),
            must_address=[
                c for c in eval_data.get("concerns", []) if "critical" in c.lower()
            ],
            nice_to_have=eval_data.get("suggestions", [])[:3],
        )
