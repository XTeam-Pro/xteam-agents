"""Unit tests for the memory manager."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from xteam_agents.config import Settings
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return Settings(
        openai_api_key="test-key",
        redis_url="redis://localhost:6379/0",
        qdrant_url="http://localhost:6333",
        neo4j_url="bolt://localhost:7687",
        neo4j_password="password",
        postgres_url="postgresql://postgres:password@localhost:5432/xteam",
    )


class TestMemoryManagerInvariants:
    """Tests for memory manager invariants."""

    def test_commit_to_shared_requires_commit_node(self, mock_settings, task_id, session_id):
        """Test that only commit_node can write to shared memory."""
        manager = MemoryManager(mock_settings)

        artifact = MemoryArtifact(
            task_id=task_id,
            session_id=session_id,
            content="Test content",
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.SHARED,
            created_by="test_agent",
            is_validated=True,
            validated_by="reviewer",
        )

        # Should raise when caller is not commit_node
        with pytest.raises(ValueError, match="Only commit_node can write"):
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                manager.commit_to_shared(artifact, caller="some_agent")
            )

    def test_commit_to_shared_requires_validated(self, mock_settings, task_id, session_id):
        """Test that artifacts must be validated before commit."""
        manager = MemoryManager(mock_settings)

        # Unvalidated artifact
        artifact = MemoryArtifact(
            task_id=task_id,
            session_id=session_id,
            content="Test content",
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.SHARED,
            created_by="test_agent",
            is_validated=False,  # Not validated
        )

        # Should raise even when caller is commit_node
        with pytest.raises(ValueError, match="Cannot commit unvalidated"):
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                manager.commit_to_shared(artifact, caller="commit_node")
            )


class TestMemoryArtifactValidation:
    """Tests for memory artifact validation rules."""

    def test_private_scope_always_writable(self, task_id, session_id):
        """Test that private scope artifacts can always write."""
        artifact = MemoryArtifact(
            task_id=task_id,
            session_id=session_id,
            content="Private content",
            memory_type=MemoryType.EPISODIC,
            scope=MemoryScope.PRIVATE,
            created_by="agent",
            is_validated=False,  # Doesn't matter for private
        )

        assert artifact.can_write_to_shared() is True

    def test_shared_scope_requires_validation(self, task_id, session_id):
        """Test that shared scope requires validation."""
        artifact = MemoryArtifact(
            task_id=task_id,
            session_id=session_id,
            content="Shared content",
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.SHARED,
            created_by="agent",
            is_validated=False,
        )

        assert artifact.can_write_to_shared() is False

        # After validation
        validated = artifact.validate_artifact("reviewer")
        assert validated.can_write_to_shared() is True

    def test_validate_artifact_sets_fields(self, task_id, session_id):
        """Test that validate_artifact sets all required fields."""
        artifact = MemoryArtifact(
            task_id=task_id,
            session_id=session_id,
            content="Content",
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.SHARED,
            created_by="agent",
        )

        validated = artifact.validate_artifact("reviewer_agent")

        assert validated.is_validated is True
        assert validated.validated_by == "reviewer_agent"
        assert validated.validated_at is not None
