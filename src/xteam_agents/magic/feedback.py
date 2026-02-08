"""FeedbackCollector - Captures human feedback and converts to guidelines.

Critical invariant: Does NOT write to shared memory. Queues MemoryArtifacts
that commit_node picks up and writes.
"""

from datetime import datetime
from uuid import UUID

import structlog

from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.magic import (
    FeedbackType,
    HumanFeedback,
    HumanPreferenceProfile,
    HumanResponse,
    HumanResponseType,
)
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType

logger = structlog.get_logger()


class FeedbackCollector:
    """Collects human feedback and converts it to guidelines for shared memory."""

    def __init__(self, memory_manager: MemoryManager):
        self._memory_manager = memory_manager
        self._feedback_log: list[HumanFeedback] = []
        self._pending_guidelines: list[MemoryArtifact] = []
        self._profiles: dict[str, HumanPreferenceProfile] = {}

    async def record_feedback(self, feedback: HumanFeedback) -> None:
        """Record human feedback. Optionally queue as a guideline."""
        self._feedback_log.append(feedback)

        # Store in episodic memory (private)
        await self._memory_manager.store_episodic(
            MemoryArtifact(
                task_id=feedback.task_id,
                content=f"Human feedback ({feedback.feedback_type.value}): {feedback.content}",
                content_type="feedback",
                memory_type=MemoryType.EPISODIC,
                scope=MemoryScope.PRIVATE,
                created_by=f"human:{feedback.human_id}",
                metadata={
                    "feedback_type": feedback.feedback_type.value,
                    "target_node": feedback.target_node,
                    "rating": feedback.rating,
                    "human_id": feedback.human_id,
                },
            )
        )

        # If feedback should persist, convert to a guideline artifact
        if feedback.should_persist:
            guideline = self._feedback_to_guideline(feedback)
            self._pending_guidelines.append(guideline)
            logger.info(
                "guideline_queued",
                feedback_id=str(feedback.id),
                content=feedback.content[:100],
            )

        # Update human preference profile
        self._update_profile(feedback)

    def convert_response_to_feedback(
        self, response: HumanResponse, task_id: UUID
    ) -> HumanFeedback:
        """Convert an escalation response to feedback for learning."""
        feedback_type_map = {
            HumanResponseType.APPROVAL: FeedbackType.RATING,
            HumanResponseType.REJECTION: FeedbackType.CORRECTION,
            HumanResponseType.MODIFICATION: FeedbackType.CORRECTION,
            HumanResponseType.GUIDANCE: FeedbackType.GUIDELINE,
            HumanResponseType.OVERRIDE: FeedbackType.CORRECTION,
            HumanResponseType.DEFERRAL: FeedbackType.COMMENT,
        }

        rating = None
        if response.response_type == HumanResponseType.APPROVAL:
            rating = 1.0
        elif response.response_type == HumanResponseType.REJECTION:
            rating = 0.0

        should_persist = response.response_type in (
            HumanResponseType.GUIDANCE,
            HumanResponseType.MODIFICATION,
        )

        return HumanFeedback(
            task_id=task_id,
            feedback_type=feedback_type_map.get(
                response.response_type, FeedbackType.COMMENT
            ),
            content=response.content or f"Response: {response.response_type.value}",
            rating=rating,
            should_persist=should_persist,
            human_id=response.human_id,
        )

    def get_pending_guidelines(self) -> list[MemoryArtifact]:
        """Get guidelines queued for commit_node to write to shared memory."""
        guidelines = list(self._pending_guidelines)
        self._pending_guidelines.clear()
        return guidelines

    def get_profile(self, human_id: str) -> HumanPreferenceProfile | None:
        """Get a human's preference profile."""
        return self._profiles.get(human_id)

    def _feedback_to_guideline(self, feedback: HumanFeedback) -> MemoryArtifact:
        """Convert feedback to a MemoryArtifact for shared memory.

        The artifact has is_validated=True and type=guideline metadata.
        commit_node will pick this up and write it to shared memory.
        """
        content = f"Rule: {feedback.content}"
        if feedback.applies_to:
            content += f"\nContext: Applies to {feedback.applies_to}"
        if feedback.target_node:
            content += f"\nStage: {feedback.target_node}"

        return MemoryArtifact(
            task_id=feedback.task_id,
            content=content,
            content_type="text",
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.SHARED,
            is_validated=True,
            validated_by=f"human:{feedback.human_id}",
            validated_at=datetime.utcnow(),
            created_by="magic_feedback",
            metadata={
                "type": "guideline",
                "source": "human_feedback",
                "feedback_type": feedback.feedback_type.value,
                "human_id": feedback.human_id,
            },
        )

    def _update_profile(self, feedback: HumanFeedback) -> None:
        """Update the human's preference profile."""
        human_id = feedback.human_id
        profile = self._profiles.get(human_id)

        if not profile:
            profile = HumanPreferenceProfile(human_id=human_id)
            self._profiles[human_id] = profile

        profile.total_interactions += 1
        profile.feedback_count += 1

        if feedback.rating is not None:
            # Update rolling approval rate
            total = profile.total_interactions
            profile.approval_rate = (
                profile.approval_rate * (total - 1) + feedback.rating
            ) / total

        profile.updated_at = datetime.utcnow()
