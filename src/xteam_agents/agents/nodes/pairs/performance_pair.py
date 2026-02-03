"""Performance Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class PerformanceAgent(BaseAgent):
    """
    PerformanceAgent optimizes system performance.

    Responsibilities:
    - Identify performance bottlenecks
    - Design optimization strategy
    - Plan caching approach
    - Optimize database queries
    - Plan load testing
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.PERFORMANCE)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a PerformanceAgent - responsible for system performance optimization.

Your role:
- Identify performance bottlenecks
- Design optimization strategies
- Plan caching architecture
- Optimize database queries
- Design load testing strategy

Focus on:
- Latency reduction
- Throughput optimization
- Resource utilization
- Scalability
- Cost efficiency

Output format:
{{
    "performance_targets": {{
        "latency": {{
            "p50": "50ms",
            "p95": "200ms",
            "p99": "500ms"
        }},
        "throughput": "1000 req/s",
        "resource_limits": {{
            "cpu": "70%",
            "memory": "80%",
            "disk_io": "60%"
        }}
    }},
    "bottlenecks": [
        {{
            "location": "database|network|compute|etc",
            "issue": "N+1 queries|slow algorithm|etc",
            "impact": "200ms added latency",
            "priority": "high|medium|low"
        }},
        ...
    ],
    "optimizations": [
        {{
            "type": "caching|indexing|algorithm|etc",
            "target": "What to optimize",
            "approach": "How to optimize",
            "expected_improvement": "50% latency reduction",
            "complexity": "high|medium|low",
            "risk": "high|medium|low"
        }},
        ...
    ],
    "caching_strategy": {{
        "layers": [
            {{
                "layer": "CDN|application|database",
                "technology": "CloudFront|Redis|etc",
                "ttl": "5 minutes",
                "invalidation": "event-based|time-based"
            }},
            ...
        ],
        "cache_warming": "on-deploy|on-demand",
        "eviction_policy": "LRU|LFU|FIFO"
    }},
    "database_optimizations": [
        {{
            "type": "index|query|schema",
            "table": "users",
            "optimization": "Add composite index on (email, status)",
            "impact": "Query time 500ms -> 10ms"
        }},
        ...
    ],
    "load_testing": {{
        "tool": "k6|Locust|JMeter",
        "scenarios": [
            {{
                "name": "baseline",
                "users": 100,
                "duration": "10m",
                "ramp_up": "1m"
            }},
            ...
        ],
        "success_criteria": {{
            "p95_latency": "< 200ms",
            "error_rate": "< 0.1%",
            "throughput": "> 1000 req/s"
        }}
    }}
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute performance optimization design."""
        task_prompt = f"""
Design the performance optimization strategy for this task:

TASK: {state.original_request}

Consider:
1. What are the performance targets?
2. Where are the bottlenecks?
3. What optimizations are needed?
4. What caching strategy to use?
5. How to test performance?

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
                f"Refined performance optimizations" if previous_feedback else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "performance_targets" in content:
            latency = content["performance_targets"].get("latency", {}).get("p95", "")
            throughput = content["performance_targets"].get("throughput", "")
            return f"Performance: {latency} p95, {throughput} throughput"
        return str(content)[:200]


class PerformanceCritic(BaseCritic):
    """
    PerformanceCritic stress-tests performance claims.

    Strategy: Adversarial
    Focus:
    - Unrealistic targets
    - Missing bottlenecks
    - Incomplete optimization
    - Inadequate testing
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.PERFORMANCE_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a PerformanceCritic - you stress-test performance claims.

Your role:
- Challenge performance targets
- Find missed bottlenecks
- Identify incomplete optimizations
- Validate load testing plans
- Question optimization trade-offs

Strategy: Adversarial (assume optimizations won't work as claimed)

Focus on:
1. Are targets realistic?
2. Are all bottlenecks identified?
3. Will optimizations actually work?
4. Is caching strategy sound?
5. Is load testing comprehensive?

Common issues to find:
- N+1 query problems
- Missing indexes
- Inefficient algorithms
- Memory leaks
- Resource contention
- Cascading failures under load
- Cache stampede scenarios
- Database connection pool exhaustion

Be skeptical of claimed improvements - test assumptions."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate performance optimization strategy."""
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
                for word in [
                    "bottleneck",
                    "slow",
                    "latency",
                    "performance",
                    "throughput",
                    "n+1",
                    "memory leak",
                    "inefficient",
                ]
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
