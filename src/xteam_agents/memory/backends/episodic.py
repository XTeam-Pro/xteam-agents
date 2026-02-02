"""Redis-based episodic memory backend."""

import json
from typing import Any
from uuid import UUID

import redis.asyncio as redis
import structlog

from xteam_agents.config import Settings
from xteam_agents.memory.backends.base import MemoryBackend
from xteam_agents.models.memory import (
    MemoryArtifact,
    MemoryQuery,
    MemorySearchResult,
    MemoryType,
)

logger = structlog.get_logger()


class EpisodicBackend(MemoryBackend):
    """
    Redis-based episodic memory.

    Episodic memory stores short-term, private memories.
    No validation is required for writes.

    Key structure:
    - {prefix}artifact:{id} - Individual artifact
    - {prefix}task:{task_id}:artifacts - Set of artifact IDs for a task
    - {prefix}session:{session_id}:artifacts - Set of artifact IDs for a session
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.prefix = settings.redis_key_prefix
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client, raising if not connected."""
        if self._client is None:
            raise RuntimeError("EpisodicBackend not connected. Call connect() first.")
        return self._client

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.from_url(
            self.settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        # Test connection
        await self._client.ping()
        logger.info("episodic_backend_connected", url=self.settings.redis_url)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("episodic_backend_disconnected")

    async def health_check(self) -> dict[str, Any]:
        """Check Redis health."""
        try:
            await self.client.ping()
            info = await self.client.info("server")
            return {
                "status": "healthy",
                "backend": "redis",
                "version": info.get("redis_version", "unknown"),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "redis",
                "error": str(e),
            }

    def _artifact_key(self, artifact_id: UUID) -> str:
        """Get Redis key for an artifact."""
        return f"{self.prefix}artifact:{artifact_id}"

    def _task_artifacts_key(self, task_id: UUID) -> str:
        """Get Redis key for task's artifact set."""
        return f"{self.prefix}task:{task_id}:artifacts"

    def _session_artifacts_key(self, session_id: UUID) -> str:
        """Get Redis key for session's artifact set."""
        return f"{self.prefix}session:{session_id}:artifacts"

    def _serialize_artifact(self, artifact: MemoryArtifact) -> str:
        """Serialize artifact to JSON."""
        data = artifact.model_dump(mode="json")
        # Convert UUID fields to strings
        for field in ["id", "task_id", "session_id", "source_id", "target_id"]:
            if data.get(field):
                data[field] = str(data[field])
        return json.dumps(data)

    def _deserialize_artifact(self, data: str) -> MemoryArtifact:
        """Deserialize artifact from JSON."""
        parsed = json.loads(data)
        return MemoryArtifact.model_validate(parsed)

    async def store(self, artifact: MemoryArtifact) -> None:
        """Store an artifact in Redis."""
        key = self._artifact_key(artifact.id)
        data = self._serialize_artifact(artifact)

        pipe = self.client.pipeline()
        pipe.set(key, data)

        # Add to task index
        pipe.sadd(self._task_artifacts_key(artifact.task_id), str(artifact.id))

        # Add to session index if present
        if artifact.session_id:
            pipe.sadd(self._session_artifacts_key(artifact.session_id), str(artifact.id))

        await pipe.execute()
        logger.debug(
            "episodic_artifact_stored",
            artifact_id=str(artifact.id),
            task_id=str(artifact.task_id),
        )

    async def retrieve(self, artifact_id: UUID) -> MemoryArtifact | None:
        """Retrieve an artifact by ID."""
        key = self._artifact_key(artifact_id)
        data = await self.client.get(key)

        if data is None:
            return None

        return self._deserialize_artifact(data)

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """
        Search episodic memory.

        Note: Redis doesn't support vector search, so we do text matching.
        For semantic search, use the SemanticBackend.
        """
        results: list[MemorySearchResult] = []

        # Get artifacts to search
        if query.task_id:
            artifact_ids = await self.client.smembers(
                self._task_artifacts_key(query.task_id)
            )
        elif query.session_id:
            artifact_ids = await self.client.smembers(
                self._session_artifacts_key(query.session_id)
            )
        else:
            # Without task/session filter, we can't efficiently search Redis
            logger.warning("episodic_search_no_filter", query=query.query_text)
            return results

        # Load and filter artifacts
        count = 0
        for artifact_id_str in artifact_ids:
            if count >= query.limit:
                break

            artifact = await self.retrieve(UUID(artifact_id_str))
            if artifact is None:
                continue

            # Apply scope filter
            if query.scope and artifact.scope != query.scope:
                continue

            # Simple text matching (case-insensitive)
            query_lower = query.query_text.lower()
            if query_lower in artifact.content.lower():
                results.append(
                    MemorySearchResult(
                        artifact=artifact,
                        score=1.0,  # Exact match
                        source=MemoryType.EPISODIC,
                    )
                )
                count += 1

        return results

    async def delete(self, artifact_id: UUID) -> bool:
        """Delete an artifact."""
        key = self._artifact_key(artifact_id)

        # Get artifact first to clean up indexes
        artifact = await self.retrieve(artifact_id)
        if artifact is None:
            return False

        pipe = self.client.pipeline()
        pipe.delete(key)
        pipe.srem(self._task_artifacts_key(artifact.task_id), str(artifact_id))

        if artifact.session_id:
            pipe.srem(self._session_artifacts_key(artifact.session_id), str(artifact_id))

        await pipe.execute()
        logger.debug("episodic_artifact_deleted", artifact_id=str(artifact_id))
        return True

    async def list_by_task(
        self, task_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[MemoryArtifact]:
        """List all artifacts for a task."""
        artifact_ids = await self.client.smembers(self._task_artifacts_key(task_id))

        artifacts: list[MemoryArtifact] = []
        for i, artifact_id_str in enumerate(sorted(artifact_ids)):
            if i < offset:
                continue
            if len(artifacts) >= limit:
                break

            artifact = await self.retrieve(UUID(artifact_id_str))
            if artifact:
                artifacts.append(artifact)

        return artifacts

    async def get_task_state(self, task_id: UUID) -> dict[str, Any] | None:
        """Get task state from Redis (for orchestrator)."""
        key = f"{self.prefix}task_state:{task_id}"
        data = await self.client.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def set_task_state(self, task_id: UUID, state: dict[str, Any]) -> None:
        """Set task state in Redis (for orchestrator)."""
        key = f"{self.prefix}task_state:{task_id}"
        await self.client.set(key, json.dumps(state, default=str))

    async def delete_task_state(self, task_id: UUID) -> None:
        """Delete task state from Redis."""
        key = f"{self.prefix}task_state:{task_id}"
        await self.client.delete(key)
