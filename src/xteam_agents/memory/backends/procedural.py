"""Neo4j-based procedural memory backend."""

from typing import Any
from uuid import UUID

import structlog
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

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


class ProceduralBackend(MemoryBackend):
    """
    Neo4j-based procedural memory.

    Procedural memory stores knowledge as a graph of relationships.
    Only validated, shared artifacts can be written (via commit_node only).

    Graph structure:
    - (:Artifact {id, content, ...}) - Artifact nodes
    - (:Task {id, description}) - Task nodes
    - (a)-[:BELONGS_TO]->(t) - Artifact belongs to task
    - (a1)-[:RELATES_TO {type}]->(a2) - Relationships between artifacts
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._driver = None

    @property
    def driver(self):
        """Get Neo4j driver, raising if not connected."""
        if self._driver is None:
            raise RuntimeError("ProceduralBackend not connected. Call connect() first.")
        return self._driver

    async def connect(self) -> None:
        """Connect to Neo4j."""
        password = self.settings.neo4j_password.get_secret_value()
        self._driver = AsyncGraphDatabase.driver(
            self.settings.neo4j_url,
            auth=(self.settings.neo4j_user, password),
        )

        # Verify connectivity
        async with self._driver.session(database=self.settings.neo4j_database) as session:
            await session.run("RETURN 1")

        # Create indexes
        await self._ensure_indexes()
        logger.info(
            "procedural_backend_connected",
            url=self.settings.neo4j_url,
            database=self.settings.neo4j_database,
        )

    async def _ensure_indexes(self) -> None:
        """Create necessary indexes."""
        async with self.driver.session(database=self.settings.neo4j_database) as session:
            # Index on Artifact.id
            await session.run(
                "CREATE INDEX artifact_id IF NOT EXISTS FOR (a:Artifact) ON (a.id)"
            )
            # Index on Task.id
            await session.run(
                "CREATE INDEX task_id IF NOT EXISTS FOR (t:Task) ON (t.id)"
            )
            # Index on Artifact.task_id for filtering
            await session.run(
                "CREATE INDEX artifact_task_id IF NOT EXISTS FOR (a:Artifact) ON (a.task_id)"
            )

    async def disconnect(self) -> None:
        """Disconnect from Neo4j."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("procedural_backend_disconnected")

    async def health_check(self) -> dict[str, Any]:
        """Check Neo4j health."""
        try:
            async with self.driver.session(database=self.settings.neo4j_database) as session:
                result = await session.run("CALL dbms.components() YIELD name, versions")
                record = await result.single()
                return {
                    "status": "healthy",
                    "backend": "neo4j",
                    "name": record["name"] if record else "unknown",
                    "version": record["versions"][0] if record else "unknown",
                }
        except ServiceUnavailable as e:
            return {
                "status": "unhealthy",
                "backend": "neo4j",
                "error": str(e),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "neo4j",
                "error": str(e),
            }

    def _artifact_to_props(self, artifact: MemoryArtifact) -> dict[str, Any]:
        """Convert artifact to Neo4j node properties."""
        return {
            "id": str(artifact.id),
            "task_id": str(artifact.task_id),
            "session_id": str(artifact.session_id) if artifact.session_id else None,
            "content": artifact.content,
            "content_type": artifact.content_type,
            "memory_type": artifact.memory_type.value,
            "scope": artifact.scope.value,
            "is_validated": artifact.is_validated,
            "validated_by": artifact.validated_by,
            "created_by": artifact.created_by,
            "created_at": artifact.created_at.isoformat(),
            "metadata": str(artifact.metadata),  # Store as string for simplicity
        }

    def _props_to_artifact(self, props: dict[str, Any]) -> MemoryArtifact:
        """Convert Neo4j properties to artifact."""
        import ast
        from datetime import datetime

        return MemoryArtifact(
            id=UUID(props["id"]),
            task_id=UUID(props["task_id"]),
            session_id=UUID(props["session_id"]) if props.get("session_id") else None,
            content=props["content"],
            content_type=props.get("content_type", "text"),
            memory_type=MemoryType(props["memory_type"]),
            scope=MemoryScope(props["scope"]),
            is_validated=props.get("is_validated", False),
            validated_by=props.get("validated_by"),
            created_by=props["created_by"],
            created_at=datetime.fromisoformat(props["created_at"]),
            metadata=ast.literal_eval(props.get("metadata", "{}")),
        )

    async def store(self, artifact: MemoryArtifact) -> None:
        """
        Store an artifact in Neo4j.

        INVARIANT: Only validated, shared artifacts can be stored.
        This should only be called by commit_node.
        """
        # Enforce invariant: only validated shared artifacts
        if artifact.scope == MemoryScope.SHARED and not artifact.is_validated:
            raise ValueError(
                "Cannot store unvalidated artifact in procedural memory. "
                "Artifact must be validated before writing to shared memory."
            )

        async with self.driver.session(database=self.settings.neo4j_database) as session:
            props = self._artifact_to_props(artifact)

            # Create artifact node and link to task
            await session.run(
                """
                MERGE (t:Task {id: $task_id})
                ON CREATE SET t.created_at = datetime()
                CREATE (a:Artifact $props)
                CREATE (a)-[:BELONGS_TO]->(t)
                """,
                task_id=str(artifact.task_id),
                props=props,
            )

            # Create relationship if source_id is specified
            if artifact.source_id and artifact.relationship_type:
                await session.run(
                    """
                    MATCH (source:Artifact {id: $source_id})
                    MATCH (target:Artifact {id: $target_id})
                    CREATE (source)-[:RELATES_TO {type: $rel_type}]->(target)
                    """,
                    source_id=str(artifact.source_id),
                    target_id=str(artifact.id),
                    rel_type=artifact.relationship_type,
                )

        logger.debug(
            "procedural_artifact_stored",
            artifact_id=str(artifact.id),
            task_id=str(artifact.task_id),
        )

    async def retrieve(self, artifact_id: UUID) -> MemoryArtifact | None:
        """Retrieve an artifact by ID."""
        async with self.driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                "MATCH (a:Artifact {id: $id}) RETURN a",
                id=str(artifact_id),
            )
            record = await result.single()

            if record is None:
                return None

            return self._props_to_artifact(dict(record["a"]))

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """
        Search procedural memory using text matching.

        Neo4j full-text search could be enabled for better results.
        """
        results: list[MemorySearchResult] = []

        async with self.driver.session(database=self.settings.neo4j_database) as session:
            # Build query with filters
            cypher = "MATCH (a:Artifact)"
            params: dict[str, Any] = {"limit": query.limit}
            where_clauses = []

            if query.task_id:
                where_clauses.append("a.task_id = $task_id")
                params["task_id"] = str(query.task_id)

            if query.scope:
                where_clauses.append("a.scope = $scope")
                params["scope"] = query.scope.value

            # Text search (simple contains)
            where_clauses.append("toLower(a.content) CONTAINS toLower($query_text)")
            params["query_text"] = query.query_text

            if where_clauses:
                cypher += " WHERE " + " AND ".join(where_clauses)

            cypher += " RETURN a LIMIT $limit"

            result = await session.run(cypher, **params)
            records = await result.values()

            for record in records:
                artifact = self._props_to_artifact(dict(record[0]))
                results.append(
                    MemorySearchResult(
                        artifact=artifact,
                        score=1.0,
                        source=MemoryType.PROCEDURAL,
                    )
                )

        return results

    async def delete(self, artifact_id: UUID) -> bool:
        """Delete an artifact and its relationships."""
        async with self.driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                """
                MATCH (a:Artifact {id: $id})
                DETACH DELETE a
                RETURN count(a) as deleted
                """,
                id=str(artifact_id),
            )
            record = await result.single()
            deleted = record["deleted"] > 0 if record else False

        if deleted:
            logger.debug("procedural_artifact_deleted", artifact_id=str(artifact_id))
        return deleted

    async def list_by_task(
        self, task_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[MemoryArtifact]:
        """List all artifacts for a task."""
        async with self.driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                """
                MATCH (a:Artifact {task_id: $task_id})
                RETURN a
                ORDER BY a.created_at
                SKIP $offset
                LIMIT $limit
                """,
                task_id=str(task_id),
                offset=offset,
                limit=limit,
            )
            records = await result.values()
            return [self._props_to_artifact(dict(record[0])) for record in records]

    async def get_knowledge_graph(
        self, task_id: UUID, depth: int = 2
    ) -> dict[str, Any]:
        """
        Get the knowledge graph for a task.

        Returns nodes and relationships up to specified depth.
        """
        async with self.driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                """
                MATCH (t:Task {id: $task_id})
                MATCH (a:Artifact)-[:BELONGS_TO]->(t)
                OPTIONAL MATCH path = (a)-[:RELATES_TO*1..$depth]-(related:Artifact)
                WITH a, collect(DISTINCT related) as related_artifacts,
                     collect(DISTINCT relationships(path)) as rels
                RETURN a, related_artifacts, rels
                """,
                task_id=str(task_id),
                depth=depth,
            )

            nodes = []
            relationships = []
            seen_nodes = set()
            seen_rels = set()

            records = await result.values()
            for record in records:
                # Add main artifact
                artifact_props = dict(record[0])
                if artifact_props["id"] not in seen_nodes:
                    nodes.append({
                        "id": artifact_props["id"],
                        "content": artifact_props["content"][:100],
                        "type": artifact_props.get("content_type", "text"),
                    })
                    seen_nodes.add(artifact_props["id"])

                # Add related artifacts
                for related in record[1] or []:
                    if related:
                        related_props = dict(related)
                        if related_props["id"] not in seen_nodes:
                            nodes.append({
                                "id": related_props["id"],
                                "content": related_props["content"][:100],
                                "type": related_props.get("content_type", "text"),
                            })
                            seen_nodes.add(related_props["id"])

                # Add relationships
                for rel_list in record[2] or []:
                    for rel in rel_list or []:
                        if rel:
                            rel_key = f"{rel.start_node['id']}->{rel.end_node['id']}"
                            if rel_key not in seen_rels:
                                relationships.append({
                                    "source": rel.start_node["id"],
                                    "target": rel.end_node["id"],
                                    "type": rel.get("type", "RELATES_TO"),
                                })
                                seen_rels.add(rel_key)

            return {
                "nodes": nodes,
                "relationships": relationships,
                "task_id": str(task_id),
            }
