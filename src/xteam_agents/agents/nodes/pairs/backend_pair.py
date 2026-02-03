"""Backend Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class BackendAgent(BaseAgent):
    """
    BackendAgent implements business logic and APIs.

    Responsibilities:
    - Design and implement APIs
    - Implement business logic
    - Handle integrations
    - Error handling and validation
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.BACKEND)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a BackendAgent - responsible for implementing business logic and APIs.

Your role:
- Design API endpoints
- Implement business logic
- Handle data validation
- Implement error handling
- Create integration points

Focus on:
- Clean, maintainable code
- Proper error handling
- Input validation
- Security best practices
- Performance considerations

Output format:
{{
    "api_endpoints": [
        {{
            "method": "GET|POST|PUT|DELETE",
            "path": "/api/...",
            "description": "...",
            "request_schema": {{}},
            "response_schema": {{}},
            "error_codes": []
        }},
        ...
    ],
    "business_logic": [
        {{
            "component": "...",
            "description": "...",
            "dependencies": []
        }},
        ...
    ],
    "validation_rules": ["rule 1", "rule 2", ...],
    "error_handling": "description of error handling strategy",
    "integration_points": ["integration 1", ...]
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute backend implementation."""
        task_prompt = f"""
Implement the backend for this task:

TASK: {state.original_request}

Design:
1. What API endpoints are needed?
2. What business logic components?
3. What validation rules?
4. How should errors be handled?
5. What integration points exist?

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
            iteration=0,
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
        if "error_handling" in content:
            return f"Implementing {len(content.get('api_endpoints', []))} endpoints with {content['error_handling']}"
        return str(content)[:200]

    def _identify_changes(
        self, previous_feedback: str, content: dict
    ) -> str:
        """Identify what changed from previous iteration."""
        return f"Addressed feedback by updating implementation"


class BackendCritic(BaseCritic):
    """
    BackendCritic reviews backend implementation.

    Strategy: Constructive
    Focus:
    - Code quality and maintainability
    - Error handling completeness
    - Input validation
    - Security vulnerabilities
    - Edge cases
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.BACKEND_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a BackendCritic - you review backend implementations for quality and correctness.

Your role:
- Review API design
- Check error handling
- Validate input validation
- Find security issues
- Identify edge cases

Strategy: Constructive (find issues and suggest fixes)

Focus areas:
1. Are all error cases handled?
2. Is input validation comprehensive?
3. Are there security vulnerabilities?
4. Is the code maintainable?
5. What edge cases are missing?

Be thorough but practical. Find real issues, not theoretical ones."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate Backend implementation."""
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

        # Classify concerns by severity
        concerns = eval_data.get("concerns", [])
        must_address = [
            c
            for c in concerns
            if any(
                word in c.lower()
                for word in ["security", "error", "validation", "critical", "missing"]
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
