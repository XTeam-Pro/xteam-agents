"""Qdrant-based semantic memory backend."""

from typing import Any
from uuid import UUID

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from xteam_agents.config import Settings
from xteam_agents.memory.backends.base import MemoryBackend
from xteam_agents.models.memory import (
    MemoryArtifact,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryType,
)

logger = structlog.get_logger()


class SemanticBackend(MemoryBackend):
    """
    Qdrant-based semantic memory.

    Semantic memory stores vector embeddings for similarity search.
    Only validated, shared artifacts can be written here.

    Collection structure:
    - Vectors: Embeddings from content
    - Payload: Full artifact data
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.collection_name = settings.qdrant_collection
        self.vector_size = settings.embedding_dimensions
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        """Get Qdrant client, raising if not connected."""
        if self._client is None:
            raise RuntimeError("SemanticBackend not connected. Call connect() first.")
        return self._client

    async def connect(self) -> None:
        """Connect to Qdrant and ensure collection exists."""
        api_key = None
        if self.settings.qdrant_api_key:
            api_key = self.settings.qdrant_api_key.get_secret_value()

        self._client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            api_key=api_key,
        )

        # Ensure collection exists
        await self._ensure_collection()
        logger.info(
            "semantic_backend_connected",
            url=self.settings.qdrant_url,
            collection=self.collection_name,
        )

    async def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        try:
            await self.client.get_collection(self.collection_name)
        except UnexpectedResponse:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("semantic_collection_created", collection=self.collection_name)

    async def disconnect(self) -> None:
        """Disconnect from Qdrant."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("semantic_backend_disconnected")

    async def health_check(self) -> dict[str, Any]:
        """Check Qdrant health."""
        try:
            collections = await self.client.get_collections()
            collection_info = await self.client.get_collection(self.collection_name)
            return {
                "status": "healthy",
                "backend": "qdrant",
                "collections": len(collections.collections),
                "points_count": collection_info.points_count,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "qdrant",
                "error": str(e),
            }

    def _artifact_to_payload(self, artifact: MemoryArtifact) -> dict[str, Any]:
        """Convert artifact to Qdrant payload."""
        data = artifact.model_dump(mode="json")
        # Convert UUID fields to strings for Qdrant
        for field in ["id", "task_id", "session_id", "source_id", "target_id"]:
            if data.get(field):
                data[field] = str(data[field])
        return data

    def _payload_to_artifact(self, payload: dict[str, Any]) -> MemoryArtifact:
        """Convert Qdrant payload to artifact."""
        return MemoryArtifact.model_validate(payload)

    async def store(self, artifact: MemoryArtifact) -> None:
        """
        Store an artifact in Qdrant.

        INVARIANT: Only validated, shared artifacts can be stored.
        """
        # Enforce invariant: only validated shared artifacts
        if artifact.scope == MemoryScope.SHARED and not artifact.is_validated:
            raise ValueError(
                "Cannot store unvalidated artifact in semantic memory. "
                "Artifact must be validated before writing to shared memory."
            )

        if artifact.embedding is None:
            raise ValueError("Artifact must have embedding for semantic storage")

        point = PointStruct(
            id=str(artifact.id),
            vector=artifact.embedding,
            payload=self._artifact_to_payload(artifact),
        )

        await self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

        logger.debug(
            "semantic_artifact_stored",
            artifact_id=str(artifact.id),
            task_id=str(artifact.task_id),
        )

    async def retrieve(self, artifact_id: UUID) -> MemoryArtifact | None:
        """Retrieve an artifact by ID."""
        results = await self.client.retrieve(
            collection_name=self.collection_name,
            ids=[str(artifact_id)],
            with_payload=True,
        )

        if not results:
            return None

        return self._payload_to_artifact(results[0].payload)

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """
        Search semantic memory using vector similarity.

        Requires embedding in the query (done by MemoryManager).
        """
        results: list[MemorySearchResult] = []

        # Build filter conditions
        filter_conditions = []

        if query.task_id:
            filter_conditions.append(
                FieldCondition(
                    key="task_id",
                    match=MatchValue(value=str(query.task_id)),
                )
            )

        if query.scope:
            filter_conditions.append(
                FieldCondition(
                    key="scope",
                    match=MatchValue(value=query.scope.value),
                )
            )

        if query.content_type:
            filter_conditions.append(
                FieldCondition(
                    key="content_type",
                    match=MatchValue(value=query.content_type),
                )
            )

        # Build filter
        search_filter = None
        if filter_conditions:
            search_filter = Filter(must=filter_conditions)

        # Note: The actual search needs a query vector
        # This will be provided by the MemoryManager via embedding
        # For now, return empty - the manager handles embedding
        logger.debug(
            "semantic_search_prepared",
            query=query.query_text,
            filter_count=len(filter_conditions),
        )

        return results

    async def search_with_vector(
        self, vector: list[float], query: MemoryQuery
    ) -> list[MemorySearchResult]:
        """
        Search using a pre-computed query vector.

        Called by MemoryManager after embedding the query.
        """
        results: list[MemorySearchResult] = []

        # Build filter conditions
        filter_conditions = []

        if query.task_id:
            filter_conditions.append(
                FieldCondition(
                    key="task_id",
                    match=MatchValue(value=str(query.task_id)),
                )
            )

        if query.scope:
            filter_conditions.append(
                FieldCondition(
                    key="scope",
                    match=MatchValue(value=query.scope.value),
                )
            )

        # Build filter
        search_filter = None
        if filter_conditions:
            search_filter = Filter(must=filter_conditions)

        # Perform search
        search_results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=search_filter,
            limit=query.limit,
            score_threshold=query.similarity_threshold,
        )

        for hit in search_results:
            artifact = self._payload_to_artifact(hit.payload)
            results.append(
                MemorySearchResult(
                    artifact=artifact,
                    score=hit.score,
                    source=MemoryType.SEMANTIC,
                )
            )

        return results

    async def delete(self, artifact_id: UUID) -> bool:
        """Delete an artifact."""
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=[str(artifact_id)],
            )
            logger.debug("semantic_artifact_deleted", artifact_id=str(artifact_id))
            return True
        except Exception as e:
            logger.error(
                "semantic_delete_failed",
                artifact_id=str(artifact_id),
                error=str(e),
            )
            return False

    async def list_by_task(
        self, task_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[MemoryArtifact]:
        """List all artifacts for a task."""
        scroll_filter = Filter(
            must=[
                FieldCondition(
                    key="task_id",
                    match=MatchValue(value=str(task_id)),
                )
            ]
        )

        results, _ = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
        )

        return [self._payload_to_artifact(point.payload) for point in results]
