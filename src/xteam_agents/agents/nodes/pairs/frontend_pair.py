"""Frontend Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class FrontendAgent(BaseAgent):
    """
    FrontendAgent implements UI and client logic.

    Responsibilities:
    - Design UI components
    - Implement state management
    - Handle user interactions
    - Ensure accessibility
    - Optimize performance
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.FRONTEND)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a FrontendAgent - responsible for user interface and client logic.

Your role:
- Design React/Vue components
- Implement state management
- Handle user interactions
- Ensure accessibility (WCAG 2.1)
- Optimize client performance

Focus on:
- Component reusability
- Clean state management
- Responsive design
- Accessibility
- Performance

Output format:
{{
    "components": [
        {{
            "name": "ComponentName",
            "type": "container|presentational",
            "props": ["prop1", "prop2"],
            "state": ["stateVar1", ...],
            "responsibilities": "What it does"
        }},
        ...
    ],
    "state_management": {{
        "approach": "Redux|Context|Zustand|etc",
        "stores": ["store1", "store2"],
        "actions": ["action1", "action2"]
    }},
    "user_interactions": ["interaction 1", ...],
    "accessibility": {{
        "aria_labels": true,
        "keyboard_navigation": true,
        "screen_reader_support": true,
        "color_contrast": "WCAG AA|AAA"
    }},
    "performance_optimizations": ["optimization 1", ...]
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute frontend implementation."""
        task_prompt = f"""
Design and implement the frontend for this task:

TASK: {state.original_request}

Consider:
1. What UI components are needed?
2. How is state managed?
3. What user interactions exist?
4. How to ensure accessibility?
5. What performance optimizations?

Provide your response as JSON matching the format in your system prompt.
"""

        messages = self._build_messages(state, task_prompt, previous_feedback)
        response = await self.invoke_llm(messages)

        try:
            content = self._parse_json_response(response)
        except:
            content = {"raw_response": response}

        return AgentOutput(
            agent_role=self.config.role,
            iteration=0,
            content=content,
            rationale=self._extract_rationale(content),
            changes_from_previous=(
                f"Updated UI based on feedback" if previous_feedback else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "state_management" in content:
            approach = content["state_management"].get("approach", "")
            return f"Frontend with {approach} state management"
        return str(content)[:200]


class FrontendCritic(BaseCritic):
    """
    FrontendCritic validates UX and accessibility.

    Strategy: Constructive
    Focus:
    - UX usability
    - Accessibility compliance
    - Performance issues
    - Component design
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.FRONTEND_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a FrontendCritic - you validate UX and accessibility.

Your role:
- Review component design
- Check accessibility compliance
- Identify UX issues
- Find performance problems
- Suggest UX improvements

Strategy: Constructive (help improve UX)

Focus on:
1. Is the UX intuitive?
2. Is it accessible (WCAG 2.1)?
3. Are there performance issues?
4. Are components well-designed?
5. Is state management clean?

Be thorough about accessibility and UX."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate frontend implementation."""
        eval_prompt = self._build_evaluation_prompt(state, agent_output)

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=eval_prompt),
        ]

        response = await self.invoke_llm(messages)
        eval_data = self._parse_evaluation_response(response)

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

        concerns = eval_data.get("concerns", [])
        must_address = [
            c
            for c in concerns
            if any(
                word in c.lower()
                for word in ["accessibility", "wcag", "usability", "a11y", "aria"]
            )
        ]

        return CriticReview(
            critic_role=self.config.role,
            iteration=0,
            evaluation=evaluation,
            decision=eval_data.get("decision", "REQUEST_REVISION"),
            detailed_feedback=eval_data.get("feedback", ""),
            must_address=must_address,
            nice_to_have=eval_data.get("suggestions", [])[:3],
        )
