"""Architect Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class ArchitectAgent(BaseAgent):
    """
    ArchitectAgent designs system architecture.

    Responsibilities:
    - Define system components
    - Establish boundaries
    - Plan integration points
    - Identify failure modes
    - Design for scalability
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.ARCHITECT)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are an ArchitectAgent - responsible for system architecture design.

Your role:
- Design system components and their boundaries
- Define integration points between components
- Plan for scalability and failure modes
- Establish architectural patterns
- Create clear component diagrams

Focus on:
- Clear separation of concerns
- Scalability considerations
- Failure resilience
- Clean interfaces
- Evolution path

Output format:
{{
    "components": [
        {{
            "name": "ComponentName",
            "responsibility": "What it does",
            "dependencies": ["dep1", "dep2"],
            "interfaces": ["interface1", "interface2"]
        }},
        ...
    ],
    "boundaries": [
        {{
            "between": ["component1", "component2"],
            "type": "api|event|data",
            "protocol": "REST|gRPC|queue|etc"
        }},
        ...
    ],
    "integration_points": ["integration 1", ...],
    "failure_modes": [
        {{
            "scenario": "What can fail",
            "impact": "What happens",
            "mitigation": "How to handle"
        }},
        ...
    ],
    "scalability_strategy": "How the system scales"
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute architecture design."""
        task_prompt = f"""
Design the system architecture for this task:

TASK: {state.original_request}

Consider:
1. What are the main components?
2. How do they interact?
3. What are the integration points?
4. What can fail and how to handle it?
5. How does it scale?

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
                f"Addressed feedback: {previous_feedback[:200]}"
                if previous_feedback
                else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "scalability_strategy" in content:
            return content["scalability_strategy"]
        return str(content)[:200]


class ArchitectCritic(BaseCritic):
    """
    ArchitectCritic stress-tests architecture.

    Strategy: Constructive
    Focus:
    - Architectural patterns
    - Scalability issues
    - Failure scenarios
    - Component coupling
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.ARCHITECT_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are an ArchitectCritic - you stress-test system architectures.

Your role:
- Question architectural decisions
- Find scalability bottlenecks
- Identify single points of failure
- Check for tight coupling
- Validate architectural patterns

Strategy: Constructive (find issues and suggest improvements)

Focus on:
1. Can this scale to 10x load?
2. What happens if a component fails?
3. Are components too tightly coupled?
4. Are boundaries clear?
5. Is the architecture flexible for change?

Be thorough but practical."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate architecture design."""
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
                for word in ["scalability", "failure", "bottleneck", "spof", "coupling"]
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
