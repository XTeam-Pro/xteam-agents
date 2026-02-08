"""MetacognitionEngine - Confidence scoring and uncertainty detection."""

import json

import structlog

from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.magic import ConfidenceScore

logger = structlog.get_logger()

CONFIDENCE_ASSESSMENT_PROMPT = """You are a metacognitive assessment system. Evaluate the following output
from an AI agent pipeline stage and provide confidence scores.

TASK DESCRIPTION:
{task_description}

PIPELINE STAGE: {node_name}

STAGE OUTPUT:
{node_output}

ADDITIONAL CONTEXT:
{context}

Rate each dimension from 0.0 to 1.0:
1. factual_accuracy: How factually correct is the output?
2. completeness: Does it cover all aspects of the task?
3. relevance: How relevant is it to the original task?
4. coherence: Is it logically consistent and well-structured?
5. novelty_risk: How much risk from novel/untested approaches? (0=safe, 1=risky)

Also identify:
- uncertainty_factors: List of specific uncertainties
- knowledge_gaps: List of missing knowledge areas

Respond ONLY with valid JSON:
{{
    "factual_accuracy": 0.0,
    "completeness": 0.0,
    "relevance": 0.0,
    "coherence": 0.0,
    "novelty_risk": 0.0,
    "uncertainty_factors": [],
    "knowledge_gaps": []
}}"""


class MetacognitionEngine:
    """Assesses confidence in pipeline outputs using LLM-based metacognition."""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        self._llm_provider = llm_provider
        self._memory_manager = memory_manager

    async def assess_confidence(
        self,
        task_id: str,
        node_name: str,
        node_output: str,
        task_description: str,
        context: str = "",
    ) -> ConfidenceScore:
        """Assess confidence in a pipeline stage output."""
        try:
            model = self._llm_provider.get_model_for_agent("analyst")

            prompt = CONFIDENCE_ASSESSMENT_PROMPT.format(
                task_description=task_description,
                node_name=node_name,
                node_output=node_output[:2000],  # Truncate for token efficiency
                context=context[:500],
            )

            response = await model.ainvoke([{"role": "user", "content": prompt}])
            content = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response
            # Try to extract JSON from the response
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            # Compute overall score (weighted average, novelty_risk inverted)
            weights = {
                "factual_accuracy": 0.3,
                "completeness": 0.25,
                "relevance": 0.2,
                "coherence": 0.15,
                "novelty_risk": 0.1,
            }
            overall = (
                data.get("factual_accuracy", 0.5) * weights["factual_accuracy"]
                + data.get("completeness", 0.5) * weights["completeness"]
                + data.get("relevance", 0.5) * weights["relevance"]
                + data.get("coherence", 0.5) * weights["coherence"]
                + (1.0 - data.get("novelty_risk", 0.5)) * weights["novelty_risk"]
            )

            return ConfidenceScore(
                overall=round(overall, 3),
                factual_accuracy=data.get("factual_accuracy", 0.5),
                completeness=data.get("completeness", 0.5),
                relevance=data.get("relevance", 0.5),
                coherence=data.get("coherence", 0.5),
                novelty_risk=data.get("novelty_risk", 0.5),
                uncertainty_factors=data.get("uncertainty_factors", []),
                knowledge_gaps=data.get("knowledge_gaps", []),
                node_name=node_name,
            )

        except Exception as e:
            logger.warning(
                "confidence_assessment_failed",
                node_name=node_name,
                error=str(e),
            )
            return ConfidenceScore.from_score(0.5, node_name=node_name)

    async def assess_with_history(
        self,
        task_id: str,
        node_name: str,
        node_output: str,
        task_description: str,
        context: str = "",
    ) -> ConfidenceScore:
        """Assess confidence with historical context from semantic memory."""
        # Search for similar past tasks to boost confidence
        extra_context = context
        try:
            similar = await self._memory_manager.search_knowledge(
                task_description, limit=3
            )
            if similar:
                history_text = "\n".join(
                    f"- Past task: {s.content[:200]}" for s in similar
                )
                extra_context = f"{context}\n\nSimilar past tasks:\n{history_text}"
        except Exception as e:
            logger.debug("history_search_failed", error=str(e))

        score = await self.assess_confidence(
            task_id, node_name, node_output, task_description, extra_context
        )

        # Boost confidence slightly if we found similar successful tasks
        if similar:
            boost = min(0.1, len(similar) * 0.03)
            score = score.model_copy(
                update={"overall": min(1.0, score.overall + boost)}
            )

        return score
