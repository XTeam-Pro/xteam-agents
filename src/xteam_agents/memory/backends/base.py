"""Abstract base class for memory backends."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from xteam_agents.models.memory import MemoryArtifact, MemoryQuery, MemorySearchResult


class MemoryBackend(ABC):
    """
    Abstract base class for memory backends.

    Each backend implementation handles a specific type of memory:
    - Episodic (Redis): Short-term, private memory
    - Semantic (Qdrant): Vector-searchable knowledge
    - Procedural (Neo4j): Graph-based relationships
    - Audit (PostgreSQL): Append-only audit log
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the backend."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check backend health and return status."""
        pass

    @abstractmethod
    async def store(self, artifact: MemoryArtifact) -> None:
        """
        Store a memory artifact.

        Args:
            artifact: The memory artifact to store
        """
        pass

    @abstractmethod
    async def retrieve(self, artifact_id: UUID) -> MemoryArtifact | None:
        """
        Retrieve a specific artifact by ID.

        Args:
            artifact_id: The ID of the artifact to retrieve

        Returns:
            The artifact if found, None otherwise
        """
        pass

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """
        Search for artifacts matching the query.

        Args:
            query: The search query parameters

        Returns:
            List of matching artifacts with scores
        """
        pass

    @abstractmethod
    async def delete(self, artifact_id: UUID) -> bool:
        """
        Delete an artifact.

        Args:
            artifact_id: The ID of the artifact to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_by_task(
        self, task_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[MemoryArtifact]:
        """
        List all artifacts for a specific task.

        Args:
            task_id: The task ID to filter by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of artifacts for the task
        """
        pass

    async def clear_task(self, task_id: UUID) -> int:
        """
        Clear all artifacts for a task.

        Args:
            task_id: The task ID to clear

        Returns:
            Number of artifacts deleted
        """
        artifacts = await self.list_by_task(task_id)
        count = 0
        for artifact in artifacts:
            if await self.delete(artifact.id):
                count += 1
        return count
