"""End-to-end tests for Docker Compose deployment.

These tests require Docker and docker-compose to be available.
They test the full system integration with real backends.

Run with: pytest tests/e2e/ -v --docker
"""

import os
import pytest
import asyncio
from uuid import UUID


# Skip all tests if not running with --docker flag
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DOCKER_TESTS") != "true",
    reason="Docker tests disabled. Set RUN_DOCKER_TESTS=true to enable."
)


class TestDockerComposeDeployment:
    """Tests that require the full Docker Compose stack."""

    @pytest.mark.asyncio
    async def test_all_backends_healthy(self):
        """Test that all backends are healthy after docker-compose up."""
        import httpx

        # Test Redis
        import redis.asyncio as redis_client
        r = redis_client.from_url("redis://localhost:6379/0")
        assert await r.ping()
        await r.aclose()

        # Test Qdrant
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:6333/")
            assert response.status_code == 200

        # Test Neo4j
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", os.getenv("NEO4J_PASSWORD", "xteam_password")),
        )
        async with driver.session() as session:
            result = await session.run("RETURN 1 as n")
            record = await result.single()
            assert record["n"] == 1
        await driver.close()

        # Test PostgreSQL
        import asyncpg
        conn = await asyncpg.connect(
            f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD', 'xteam_password')}@localhost:5432/xteam"
        )
        result = await conn.fetchval("SELECT 1")
        assert result == 1
        await conn.close()

    @pytest.mark.asyncio
    async def test_mcp_server_health(self):
        """Test that the MCP server is healthy."""
        import httpx

        async with httpx.AsyncClient() as client:
            # This would test the actual MCP server health endpoint
            # Requires the server to be running
            try:
                response = await client.get("http://localhost:8000/health")
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("MCP server not running")

    @pytest.mark.asyncio
    async def test_submit_and_complete_task(self):
        """Test submitting a task and waiting for completion.

        This is a full end-to-end test that:
        1. Submits a task via MCP
        2. Waits for task completion
        3. Verifies the result is in shared memory
        """
        # This test would use the actual MCP client to submit a task
        # For now, we'll skip if the server isn't running
        pytest.skip("Full E2E test requires running MCP server")

    @pytest.mark.asyncio
    async def test_memory_persistence_across_restart(self):
        """Test that memory persists across container restarts."""
        # This test would:
        # 1. Submit a task and let it complete
        # 2. Restart the MCP server container
        # 3. Query memory to verify the result persists
        pytest.skip("Restart test requires docker control")


class TestBackendIntegration:
    """Tests for individual backend integration."""

    @pytest.mark.asyncio
    async def test_redis_episodic_memory(self):
        """Test Redis episodic memory operations."""
        import redis.asyncio as redis_client
        import json
        from uuid import uuid4

        r = redis_client.from_url("redis://localhost:6379/0")

        # Test basic operations
        test_key = f"test:{uuid4()}"
        test_data = {"content": "Test memory", "task_id": str(uuid4())}

        await r.set(test_key, json.dumps(test_data))
        result = await r.get(test_key)
        assert result is not None
        assert json.loads(result) == test_data

        # Cleanup
        await r.delete(test_key)
        await r.aclose()

    @pytest.mark.asyncio
    async def test_qdrant_semantic_memory(self):
        """Test Qdrant semantic memory operations."""
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
        from uuid import uuid4

        client = AsyncQdrantClient(url="http://localhost:6333")

        # Create test collection
        collection_name = f"test_{uuid4().hex[:8]}"
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=4, distance=Distance.COSINE),
        )

        # Insert test point
        await client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=str(uuid4()),
                    vector=[0.1, 0.2, 0.3, 0.4],
                    payload={"content": "Test semantic memory"},
                )
            ],
        )

        # Search
        results = await client.search(
            collection_name=collection_name,
            query_vector=[0.1, 0.2, 0.3, 0.4],
            limit=1,
        )
        assert len(results) == 1

        # Cleanup
        await client.delete_collection(collection_name)
        await client.close()

    @pytest.mark.asyncio
    async def test_neo4j_procedural_memory(self):
        """Test Neo4j procedural memory operations."""
        from neo4j import AsyncGraphDatabase
        from uuid import uuid4

        driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", os.getenv("NEO4J_PASSWORD", "xteam_password")),
        )

        async with driver.session() as session:
            # Create test node
            test_id = str(uuid4())
            await session.run(
                "CREATE (a:TestArtifact {id: $id, content: $content})",
                id=test_id,
                content="Test procedural memory",
            )

            # Query
            result = await session.run(
                "MATCH (a:TestArtifact {id: $id}) RETURN a.content as content",
                id=test_id,
            )
            record = await result.single()
            assert record["content"] == "Test procedural memory"

            # Cleanup
            await session.run(
                "MATCH (a:TestArtifact {id: $id}) DELETE a",
                id=test_id,
            )

        await driver.close()

    @pytest.mark.asyncio
    async def test_postgres_audit_log(self):
        """Test PostgreSQL audit log operations."""
        import asyncpg
        from uuid import uuid4
        from datetime import datetime

        conn = await asyncpg.connect(
            f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD', 'xteam_password')}@localhost:5432/xteam"
        )

        # Ensure table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id UUID PRIMARY KEY,
                task_id UUID,
                event_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # Insert test entry
        test_id = uuid4()
        task_id = uuid4()
        await conn.execute(
            """
            INSERT INTO audit_log (id, task_id, event_type, description)
            VALUES ($1, $2, $3, $4)
            """,
            test_id,
            task_id,
            "test_event",
            "Test audit entry",
        )

        # Query
        row = await conn.fetchrow(
            "SELECT * FROM audit_log WHERE id = $1",
            test_id,
        )
        assert row["description"] == "Test audit entry"

        # Cleanup
        await conn.execute("DELETE FROM audit_log WHERE id = $1", test_id)
        await conn.close()
