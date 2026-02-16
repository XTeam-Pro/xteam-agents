"""Adapters bridging xteam-agents concrete classes to MAGIC SDK Protocols.

These adapters allow MAGICCore from the SDK to work with xteam-agents'
LLMProvider and MemoryManager without the SDK importing them directly.
"""

from uuid import UUID

import structlog

from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager

logger = structlog.get_logger()


class LLMBackendAdapter:
    """Adapts xteam-agents LLMProvider to SDK LLMBackend Protocol."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def invoke(self, messages: list[dict[str, str]]) -> str:
        """Send messages to LLM via LangChain model and return text."""
        model = self._provider.get_model_for_agent("analyst")
        response = await model.ainvoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        return content


class MemoryBackendAdapter:
    """Adapts xteam-agents MemoryManager to SDK MemoryBackend Protocol."""

    def __init__(self, manager: MemoryManager) -> None:
        self._manager = manager

    async def store_episodic(self, artifact: object) -> None:
        """Store artifact in episodic memory.

        Accepts SDK MemoryArtifact and converts to xteam_agents MemoryArtifact.
        """
        from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType

        # If it's already an xteam_agents MemoryArtifact, use directly
        if isinstance(artifact, MemoryArtifact):
            await self._manager.store_episodic(artifact)
            return

        # Convert from SDK artifact
        xa = MemoryArtifact(
            task_id=artifact.task_id,  # type: ignore[union-attr]
            content=artifact.content,  # type: ignore[union-attr]
            content_type=getattr(artifact, "content_type", "text"),
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.PRIVATE,
            created_by=getattr(artifact, "created_by", "magic_sdk"),
            metadata=getattr(artifact, "metadata", {}),
        )
        await self._manager.store_episodic(xa)

    async def search_semantic(
        self, query: str, limit: int = 10, task_id: UUID | None = None
    ) -> list[object]:
        """Search semantic memory. Returns results with .content attribute."""
        results = await self._manager.search_semantic(query, limit=limit, task_id=task_id)
        return [r.artifact for r in results]


def create_magic_core(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
) -> "MAGICCore":
    """Factory function to create SDK MAGICCore with xteam-agents backends.

    Usage:
        from xteam_agents.integration.magic_sdk_adapter import create_magic_core

        core = create_magic_core(llm_provider, memory_manager)
        score = await core.assess_confidence(...)
    """
    from studyninja_magic import MAGICCore

    llm_adapter = LLMBackendAdapter(llm_provider)
    memory_adapter = MemoryBackendAdapter(memory_manager)

    return MAGICCore(
        llm=llm_adapter,
        memory=memory_adapter,
    )
