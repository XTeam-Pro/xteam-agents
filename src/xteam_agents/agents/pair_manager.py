"""Manages Agent-Critic pair interactions."""

import json
from datetime import datetime

import structlog

from ..config import Settings
from .adversarial_config import (
    AgentPairConfig,
    CriticEvaluation,
    PairStatus,
    is_approval_met,
)
from .adversarial_state import (
    AdversarialAgentState,
    AgentOutput,
    CriticReview,
    PairResult,
)
from .base import BaseAgent, BaseCritic

logger = structlog.get_logger()


class PairInteractionManager:
    """Manages iterative interaction between an agent and their critic."""

    def __init__(
        self,
        agent: BaseAgent,
        critic: BaseCritic,
        pair_config: AgentPairConfig,
        settings: Settings,
    ):
        self.agent = agent
        self.critic = critic
        self.pair_config = pair_config
        self.settings = settings
        self.logger = logger.bind(
            pair=pair_config.pair_type.value,
            agent=agent.config.role.value,
            critic=critic.config.role.value,
        )

    async def execute_pair(self, state: AdversarialAgentState) -> PairResult:
        """
        Execute the agent-critic pair with iterative refinement.

        Process:
        1. Agent proposes solution
        2. Critic evaluates
        3. If approved → done
        4. If rejected → agent revises (up to max_iterations)
        5. If still rejected → escalate
        """
        self.logger.info("Starting pair execution", task_id=state.task_id)

        # Initialize pair result
        pair_result = state.get_pair_result(self.pair_config.pair_type)
        if not pair_result:
            state.init_pair_result(self.pair_config.pair_type, self.pair_config)
            pair_result = state.get_pair_result(self.pair_config.pair_type)

        pair_result.started_at = datetime.utcnow()
        pair_result.status = PairStatus.IN_PROGRESS

        previous_feedback = None

        for iteration in range(1, self.pair_config.max_iterations + 1):
            self.logger.info(
                "Pair iteration",
                iteration=iteration,
                max=self.pair_config.max_iterations,
            )

            # Agent proposes/revises solution
            try:
                agent_output = await self.agent.execute(state, previous_feedback)
                agent_output.iteration = iteration
            except Exception as e:
                self.logger.error("Agent execution failed", error=str(e))
                pair_result.status = PairStatus.REJECTED
                return pair_result

            # Critic evaluates
            try:
                critic_review = await self.critic.evaluate(state, agent_output)
                critic_review.iteration = iteration
            except Exception as e:
                self.logger.error("Critic evaluation failed", error=str(e))
                # If critic fails, default to request revision
                critic_review = self._create_fallback_review(iteration, str(e))

            # Store iteration
            pair_result.add_iteration(agent_output, critic_review)

            # Check if approved
            if is_approval_met(critic_review.evaluation, self.pair_config):
                self.logger.info(
                    "Pair approved",
                    iteration=iteration,
                    score=critic_review.evaluation.average_score(),
                )
                pair_result.status = PairStatus.APPROVED
                pair_result.final_output = agent_output
                pair_result.final_evaluation = critic_review.evaluation
                pair_result.completed_at = datetime.utcnow()
                return pair_result

            # Not approved - prepare feedback for next iteration
            previous_feedback = self._format_feedback(critic_review)

            if iteration >= self.pair_config.max_iterations:
                # Max iterations reached - escalate
                self.logger.warning(
                    "Max iterations reached, escalating",
                    iterations=iteration,
                )
                pair_result.status = PairStatus.ESCALATED

                # Create conflict for orchestrator
                state.add_conflict(
                    pair_type=self.pair_config.pair_type,
                    agent_position=agent_output.rationale,
                    critic_position=critic_review.detailed_feedback,
                    iterations=iteration,
                    context={
                        "agent_output": agent_output.content,
                        "critic_scores": {
                            "correctness": critic_review.evaluation.correctness,
                            "completeness": critic_review.evaluation.completeness,
                            "quality": critic_review.evaluation.quality,
                            "performance": critic_review.evaluation.performance,
                            "security": critic_review.evaluation.security,
                        },
                        "average_score": critic_review.evaluation.average_score(),
                    },
                )

                pair_result.completed_at = datetime.utcnow()
                return pair_result

        # Should not reach here, but handle it
        pair_result.status = PairStatus.REJECTED
        pair_result.completed_at = datetime.utcnow()
        return pair_result

    def _format_feedback(self, critic_review: CriticReview) -> str:
        """Format critic's feedback for agent's next iteration."""
        feedback = f"""
CRITIC'S EVALUATION:
Decision: {critic_review.decision}

Scores (0-10):
- Correctness: {critic_review.evaluation.correctness}
- Completeness: {critic_review.evaluation.completeness}
- Quality: {critic_review.evaluation.quality}
- Performance: {critic_review.evaluation.performance}
- Security: {critic_review.evaluation.security}
Average: {critic_review.evaluation.average_score():.1f}

Feedback:
{critic_review.detailed_feedback}

Must Address:
{chr(10).join(f"- {item}" for item in critic_review.must_address)}

Nice to Have:
{chr(10).join(f"- {item}" for item in critic_review.nice_to_have)}
"""
        return feedback

    def _create_fallback_review(
        self, iteration: int, error: str
    ) -> CriticReview:
        """Create a fallback review when critic fails."""
        return CriticReview(
            critic_role=self.critic.config.role,
            iteration=iteration,
            evaluation=CriticEvaluation(
                correctness=5.0,
                completeness=5.0,
                quality=5.0,
                performance=5.0,
                security=5.0,
                feedback=f"Critic evaluation failed: {error}",
                concerns=["Critic evaluation error"],
                suggestions=["Manual review recommended"],
                approved=False,
            ),
            decision="REQUEST_REVISION",
            detailed_feedback=f"Critic encountered an error: {error}. Please revise and try again.",
            must_address=["Fix the error that caused critic to fail"],
            nice_to_have=[],
        )


class PairRegistry:
    """Registry of agent-critic pairs."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.pairs: dict[str, PairInteractionManager] = {}
        self.logger = logger.bind(component="PairRegistry")

    def register_pair(
        self,
        pair_config: AgentPairConfig,
        agent: BaseAgent,
        critic: BaseCritic,
    ):
        """Register an agent-critic pair."""
        manager = PairInteractionManager(
            agent=agent,
            critic=critic,
            pair_config=pair_config,
            settings=self.settings,
        )
        self.pairs[pair_config.pair_type.value] = manager
        self.logger.info(
            "Pair registered",
            pair_type=pair_config.pair_type.value,
            agent=agent.config.role.value,
            critic=critic.config.role.value,
        )

    def get_pair(self, pair_type: str) -> PairInteractionManager:
        """Get a pair manager by type."""
        return self.pairs.get(pair_type)

    async def execute_pair(
        self, pair_type: str, state: AdversarialAgentState
    ) -> PairResult:
        """Execute a specific pair."""
        manager = self.get_pair(pair_type)
        if not manager:
            raise ValueError(f"Pair {pair_type} not registered")

        return await manager.execute_pair(state)
