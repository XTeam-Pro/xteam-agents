"""Memory manager facade with invariant enforcement."""

from typing import Any
from uuid import UUID

import structlog

from xteam_agents.config import Settings
from xteam_agents.memory.backends.audit import AuditBackend
from xteam_agents.memory.backends.episodic import EpisodicBackend
from xteam_agents.memory.backends.procedural import ProceduralBackend
from xteam_agents.memory.backends.semantic import SemanticBackend
from xteam_agents.memory.embeddings import EmbeddingProvider
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import (
    MemoryArtifact,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryType,
)

logger = structlog.get_logger()


class MemoryManager:
    """
    Facade for all memory operations with invariant enforcement.

    Memory Invariants:
    | Backend    | Who writes?    | Scope     | Validation |
    |------------|----------------|-----------|------------|
    | Episodic   | Any node       | private   | No         |
    | Semantic   | commit_node    | shared    | Required   |
    | Procedural | commit_node    | shared    | Required   |
    | Audit      | Any node       | shared    | N/A        |

    Agents have NO direct DB access - all operations go through this manager.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.episodic = EpisodicBackend(settings)
        self.semantic = SemanticBackend(settings)
        self.procedural = ProceduralBackend(settings)
        self.audit = AuditBackend(settings)
        self.embeddings = EmbeddingProvider(settings)
        self._connected = False

    async def connect(self) -> None:
        """Connect to all backends."""
        await self.episodic.connect()
        await self.semantic.connect()
        await self.procedural.connect()
        await self.audit.connect()
        self._connected = True
        logger.info("memory_manager_connected")

    async def disconnect(self) -> None:
        """Disconnect from all backends."""
        await self.episodic.disconnect()
        await self.semantic.disconnect()
        await self.procedural.disconnect()
        await self.audit.disconnect()
        self._connected = False
        logger.info("memory_manager_disconnected")

    async def health_check(self) -> dict[str, Any]:
        """Check health of all backends."""
        return {
            "episodic": await self.episodic.health_check(),
            "semantic": await self.semantic.health_check(),
            "procedural": await self.procedural.health_check(),
            "audit": await self.audit.health_check(),
        }

    # ==================== EPISODIC MEMORY (Any node can write) ====================

    async def store_episodic(self, artifact: MemoryArtifact) -> None:
        """
        Store an artifact in episodic memory.

        This can be called by any node for private, short-term storage.
        No validation required.
        """
        if artifact.memory_type != MemoryType.EPISODIC:
            artifact = artifact.model_copy(update={"memory_type": MemoryType.EPISODIC})

        # Episodic memory should be private
        if artifact.scope != MemoryScope.PRIVATE:
            logger.warning(
                "episodic_scope_override",
                artifact_id=str(artifact.id),
                original_scope=artifact.scope.value,
            )
            artifact = artifact.model_copy(update={"scope": MemoryScope.PRIVATE})

        await self.episodic.store(artifact)

        # Audit the write
        await self.audit.append(
            AuditEntry(
                task_id=artifact.task_id,
                session_id=artifact.session_id,
                event_type=AuditEventType.MEMORY_WRITE,
                agent_name=artifact.created_by,
                description=f"Stored episodic artifact: {artifact.id}",
                data={"artifact_id": str(artifact.id), "content_type": artifact.content_type},
            )
        )

    async def read_episodic(self, artifact_id: UUID) -> MemoryArtifact | None:
        """Read an artifact from episodic memory."""
        return await self.episodic.retrieve(artifact_id)

    # ==================== SHARED MEMORY (commit_node only) ====================

    async def commit_to_shared(
        self,
        artifact: MemoryArtifact,
        caller: str = "commit_node",
    ) -> None:
        """
        Commit a validated artifact to shared memory.

        INVARIANT: This should ONLY be called by commit_node.
        INVARIANT: Artifact MUST be validated.

        Args:
            artifact: The artifact to commit (must be validated)
            caller: Name of the calling node (for audit)

        Raises:
            ValueError: If artifact is not validated or caller is not commit_node
        """
        # Enforce caller invariant
        if caller != "commit_node":
            logger.error(
                "shared_memory_violation",
                caller=caller,
                artifact_id=str(artifact.id),
            )
            raise ValueError(
                f"Only commit_node can write to shared memory. Caller: {caller}"
            )

        # Enforce validation invariant
        if not artifact.is_validated:
            raise ValueError(
                "Cannot commit unvalidated artifact to shared memory. "
                "Artifact must be validated by reviewer first."
            )

        # Ensure shared scope
        if artifact.scope != MemoryScope.SHARED:
            artifact = artifact.model_copy(update={"scope": MemoryScope.SHARED})

        # Generate embedding if needed
        if artifact.embedding is None:
            artifact = artifact.model_copy(
                update={"embedding": await self.embeddings.embed_text(artifact.content)}
            )

        # Store in semantic memory (Qdrant)
        if artifact.memory_type in [MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            await self.semantic.store(artifact)

        # Store in procedural memory (Neo4j) if it has relationship info
        if artifact.memory_type == MemoryType.PROCEDURAL or artifact.relationship_type:
            await self.procedural.store(artifact)

        # Audit the commit
        await self.audit.append(
            AuditEntry(
                task_id=artifact.task_id,
                session_id=artifact.session_id,
                event_type=AuditEventType.MEMORY_VALIDATED,
                agent_name=caller,
                description=f"Committed validated artifact to shared memory: {artifact.id}",
                data={
                    "artifact_id": str(artifact.id),
                    "memory_type": artifact.memory_type.value,
                    "validated_by": artifact.validated_by,
                },
            )
        )

        logger.info(
            "artifact_committed_to_shared",
            artifact_id=str(artifact.id),
            memory_type=artifact.memory_type.value,
        )

    # ==================== READING (Any node can read) ====================

    async def query(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """
        Query memory across backends.

        All nodes can read from any memory type.
        """
        results: list[MemorySearchResult] = []

        # Generate query embedding for semantic search
        query_embedding = None
        if query.use_semantic_search and MemoryType.SEMANTIC in query.memory_types:
            query_embedding = await self.embeddings.embed_text(query.query_text)

        # Search each requested backend
        for memory_type in query.memory_types:
            if memory_type == MemoryType.EPISODIC:
                episodic_results = await self.episodic.search(query)
                results.extend(episodic_results)

            elif memory_type == MemoryType.SEMANTIC and query_embedding:
                semantic_results = await self.semantic.search_with_vector(
                    query_embedding, query
                )
                results.extend(semantic_results)

            elif memory_type == MemoryType.PROCEDURAL:
                procedural_results = await self.procedural.search(query)
                results.extend(procedural_results)

        # Sort by score and apply limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: query.limit]

    async def search_semantic(
        self, query_text: str, limit: int = 10, task_id: UUID | None = None
    ) -> list[MemorySearchResult]:
        """Convenience method for semantic search."""
        query = MemoryQuery(
            query_text=query_text,
            memory_types=[MemoryType.SEMANTIC],
            limit=limit,
            task_id=task_id,
        )
        return await self.query(query)

    async def get_knowledge_graph(
        self, task_id: UUID, depth: int = 2
    ) -> dict[str, Any]:
        """Get knowledge graph from procedural memory."""
        return await self.procedural.get_knowledge_graph(task_id, depth)

    # ==================== AUDIT (Any node can write) ====================

    async def log_audit(self, entry: AuditEntry) -> None:
        """
        Append an audit entry.

        Any node can write to the audit log.
        """
        await self.audit.append(entry)

    async def get_audit_log(
        self, task_id: UUID, limit: int = 100
    ) -> list[AuditEntry]:
        """Get audit log for a task."""
        return await self.audit.get_by_task(task_id, limit)

    # ==================== TASK STATE (Redis) ====================

    async def get_task_state(self, task_id: UUID) -> dict[str, Any] | None:
        """Get task state from episodic backend."""
        return await self.episodic.get_task_state(task_id)

    async def set_task_state(self, task_id: UUID, state: dict[str, Any]) -> None:
        """Set task state in episodic backend."""
        await self.episodic.set_task_state(task_id, state)

    async def delete_task_state(self, task_id: UUID) -> None:
        """Delete task state from episodic backend."""
        await self.episodic.delete_task_state(task_id)

    # ==================== CLEANUP ====================

    async def clear_task_data(self, task_id: UUID) -> dict[str, int]:
        """
        Clear all data for a task from all backends.

        Returns count of deleted items per backend.
        """
        counts = {
            "episodic": await self.episodic.clear_task(task_id),
            "semantic": await self.semantic.clear_task(task_id),
            "procedural": await self.procedural.clear_task(task_id),
        }

        logger.info("task_data_cleared", task_id=str(task_id), counts=counts)
        return counts
