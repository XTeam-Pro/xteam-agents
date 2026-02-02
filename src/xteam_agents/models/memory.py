"""Memory-related models."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory backends."""

    EPISODIC = "episodic"  # Redis - private, no validation
    SEMANTIC = "semantic"  # Qdrant - shared, requires validation
    PROCEDURAL = "procedural"  # Neo4j - shared, requires validation
    AUDIT = "audit"  # PostgreSQL - append-only


class MemoryScope(str, Enum):
    """Scope of memory visibility."""

    PRIVATE = "private"  # Only visible to creating agent
    SHARED = "shared"  # Visible to all agents (requires validation)


class MemoryArtifact(BaseModel):
    """
    A piece of information stored in memory.

    Memory artifacts flow through the system and are persisted
    to the appropriate backend based on their type and scope.
    """

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    session_id: UUID | None = None

    # Content
    content: str
    content_type: str = "text"  # text, json, code, etc.
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Classification
    memory_type: MemoryType
    scope: MemoryScope

    # Validation state (only relevant for shared scope)
    is_validated: bool = False
    validated_by: str | None = None
    validated_at: datetime | None = None

    # Embedding (populated by embedding provider)
    embedding: list[float] | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # Agent name that created this

    # For procedural memory (Neo4j relationships)
    source_id: UUID | None = None
    target_id: UUID | None = None
    relationship_type: str | None = None

    def validate_artifact(self, validator: str) -> "MemoryArtifact":
        """Mark artifact as validated."""
        return self.model_copy(
            update={
                "is_validated": True,
                "validated_by": validator,
                "validated_at": datetime.utcnow(),
            }
        )

    def can_write_to_shared(self) -> bool:
        """Check if artifact can be written to shared memory."""
        if self.scope == MemoryScope.PRIVATE:
            return True  # Private always allowed
        # Shared requires validation
        return self.is_validated


class MemoryQuery(BaseModel):
    """Query parameters for memory retrieval."""

    query_text: str
    memory_types: list[MemoryType] = Field(default_factory=lambda: list(MemoryType))
    scope: MemoryScope | None = None  # None means both
    task_id: UUID | None = None
    session_id: UUID | None = None

    # Vector search parameters
    use_semantic_search: bool = True
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    # Pagination
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    # Filters
    created_after: datetime | None = None
    created_before: datetime | None = None
    content_type: str | None = None
    metadata_filters: dict[str, Any] = Field(default_factory=dict)


class MemorySearchResult(BaseModel):
    """Result from a memory search."""

    artifact: MemoryArtifact
    score: float = Field(ge=0.0, le=1.0)
    source: MemoryType
