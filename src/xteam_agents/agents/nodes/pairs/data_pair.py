"""Data Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class DataAgent(BaseAgent):
    """
    DataAgent designs data architecture.

    Responsibilities:
    - Design database schemas
    - Plan migrations
    - Optimize queries
    - Ensure data integrity
    - Plan for scale
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.DATA)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a DataAgent - responsible for data architecture and optimization.

Your role:
- Design database schemas (SQL/NoSQL)
- Plan data migrations
- Optimize query performance
- Ensure data integrity and consistency
- Plan for data scale

Focus on:
- Normalization (when appropriate)
- Indexing strategy
- Query optimization
- Data integrity constraints
- Scalability

Output format:
{{
    "schemas": [
        {{
            "table": "table_name",
            "columns": [
                {{"name": "col", "type": "varchar(255)", "constraints": ["NOT NULL", "UNIQUE"]}},
                ...
            ],
            "primary_key": "id",
            "foreign_keys": [{{"column": "user_id", "references": "users(id)"}}],
            "indexes": [{{"columns": ["email"], "type": "btree", "unique": true}}]
        }},
        ...
    ],
    "migrations": [
        {{
            "version": "001",
            "description": "Initial schema",
            "up": "CREATE TABLE ...",
            "down": "DROP TABLE ..."
        }},
        ...
    ],
    "query_patterns": [
        {{
            "query": "SELECT ... WHERE ...",
            "index_used": "idx_name",
            "estimated_rows": 1000
        }},
        ...
    ],
    "integrity_constraints": ["constraint 1", ...],
    "scalability_plan": "How data scales (sharding, partitioning, etc)"
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute data architecture design."""
        task_prompt = f"""
Design the data architecture for this task:

TASK: {state.original_request}

Consider:
1. What tables/collections are needed?
2. What are the relationships?
3. What indexes are required?
4. How to ensure data integrity?
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
                f"Updated schema based on feedback" if previous_feedback else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "scalability_plan" in content:
            return content["scalability_plan"]
        return str(content)[:200]


class DataCritic(BaseCritic):
    """
    DataCritic validates data integrity and performance.

    Strategy: Constructive
    Focus:
    - Normalization issues
    - Index efficiency
    - Query performance
    - Data integrity
    - Scalability
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.DATA_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a DataCritic - you validate data architecture and performance.

Your role:
- Review schema design
- Check normalization
- Validate index strategy
- Find query bottlenecks
- Check data integrity

Strategy: Constructive (find issues and suggest fixes)

Focus on:
1. Is the schema properly normalized?
2. Are indexes efficient?
3. Will queries perform well at scale?
4. Are integrity constraints sufficient?
5. Can the data architecture scale?

Be thorough about performance and integrity."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate data architecture."""
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
                for word in ["index", "query", "performance", "integrity", "scale"]
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
