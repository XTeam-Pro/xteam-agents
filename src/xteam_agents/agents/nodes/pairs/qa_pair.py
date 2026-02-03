"""QA Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class QAAgent(BaseAgent):
    """
    QAAgent designs testing strategy.

    Responsibilities:
    - Design test strategy
    - Plan test coverage
    - Define test cases
    - Setup test automation
    - Plan QA process
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.QA)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a QAAgent - responsible for testing strategy and quality assurance.

Your role:
- Design comprehensive test strategy
- Plan test coverage (unit, integration, E2E)
- Define test cases and scenarios
- Setup test automation
- Plan QA process and workflows

Focus on:
- Coverage completeness
- Edge case identification
- Automation strategy
- Test maintainability
- Quality metrics

Output format:
{{
    "test_strategy": {{
        "approach": "TDD|BDD|Exploratory",
        "levels": ["unit", "integration", "e2e"],
        "coverage_target": "80%",
        "tools": ["Jest", "Pytest", "Cypress", etc]
    }},
    "test_cases": [
        {{
            "id": "TC001",
            "type": "unit|integration|e2e",
            "description": "Test case description",
            "preconditions": "Setup needed",
            "steps": ["step 1", "step 2"],
            "expected_result": "What should happen",
            "priority": "high|medium|low"
        }},
        ...
    ],
    "edge_cases": [
        {{
            "scenario": "Edge case scenario",
            "test_approach": "How to test",
            "expected_behavior": "What should happen"
        }},
        ...
    ],
    "automation": {{
        "ci_integration": "GitHub Actions|Jenkins",
        "test_runner": "pytest|jest",
        "coverage_tool": "coverage.py|istanbul",
        "reporting": "Allure|JUnit"
    }},
    "quality_metrics": [
        {{
            "metric": "code_coverage",
            "target": "80%",
            "measurement": "coverage.py"
        }},
        ...
    ]
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute QA strategy design."""
        task_prompt = f"""
Design the testing strategy for this task:

TASK: {state.original_request}

Consider:
1. What test levels are needed?
2. What are the critical test cases?
3. What edge cases must be covered?
4. How to automate testing?
5. What quality metrics to track?

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
                f"Updated test strategy based on feedback" if previous_feedback else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "test_strategy" in content:
            approach = content["test_strategy"].get("approach", "")
            target = content["test_strategy"].get("coverage_target", "")
            return f"QA with {approach} approach, {target} coverage target"
        return str(content)[:200]


class QACritic(BaseCritic):
    """
    QACritic hunts for untested scenarios.

    Strategy: Perfectionist
    Focus:
    - Test coverage gaps
    - Missing edge cases
    - Untested failure paths
    - Test quality issues
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.QA_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a QACritic - you hunt for untested scenarios and coverage gaps.

Your role:
- Find test coverage gaps
- Identify missing edge cases
- Hunt for untested failure paths
- Check test quality
- Find test blind spots

Strategy: Perfectionist (demand comprehensive coverage)

Focus on:
1. Are all critical paths tested?
2. Are edge cases covered?
3. Are failure scenarios tested?
4. Is test coverage sufficient?
5. Are tests maintainable?

Be extremely thorough about coverage - assume bugs hide in untested code."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate QA strategy."""
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
                for word in ["coverage", "edge case", "untested", "gap", "missing"]
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
