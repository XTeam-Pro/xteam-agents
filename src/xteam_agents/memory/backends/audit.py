"""PostgreSQL-based audit log backend."""

from typing import Any
from uuid import UUID

import asyncpg
import structlog

from xteam_agents.config import Settings
from xteam_agents.models.audit import AuditEntry, AuditEventType

logger = structlog.get_logger()


# SQL for creating the audit table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY,
    task_id UUID,
    session_id UUID,
    event_type VARCHAR(50) NOT NULL,
    agent_name VARCHAR(100),
    node_name VARCHAR(100),
    description TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id UUID,
    duration_ms INTEGER,
    token_count INTEGER
);

CREATE INDEX IF NOT EXISTS idx_audit_task_id ON audit_log(task_id);
CREATE INDEX IF NOT EXISTS idx_audit_session_id ON audit_log(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_correlation_id ON audit_log(correlation_id);
"""


class AuditBackend:
    """
    PostgreSQL-based append-only audit log.

    INVARIANT: Audit entries can only be inserted, never updated or deleted.

    This backend intentionally does NOT inherit from MemoryBackend
    because audit logs have different semantics (append-only, no search by content).
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        """Get connection pool, raising if not connected."""
        if self._pool is None:
            raise RuntimeError("AuditBackend not connected. Call connect() first.")
        return self._pool

    async def connect(self) -> None:
        """Connect to PostgreSQL and ensure table exists."""
        self._pool = await asyncpg.create_pool(self.settings.postgres_url)

        # Create table and indexes
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_TABLE_SQL)

        logger.info("audit_backend_connected", url=self.settings.postgres_url.split("@")[-1])

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("audit_backend_disconnected")

    async def health_check(self) -> dict[str, Any]:
        """Check PostgreSQL health."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT version()")
                count = await conn.fetchval("SELECT COUNT(*) FROM audit_log")
                return {
                    "status": "healthy",
                    "backend": "postgresql",
                    "version": result,
                    "entry_count": count,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "postgresql",
                "error": str(e),
            }

    async def append(self, entry: AuditEntry) -> None:
        """
        Append an audit entry.

        This is the ONLY write operation allowed on the audit log.
        """
        import json

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (
                    id, task_id, session_id, event_type, agent_name, node_name,
                    description, data, context, timestamp, correlation_id,
                    duration_ms, token_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                entry.id,
                entry.task_id,
                entry.session_id,
                entry.event_type.value,
                entry.agent_name,
                entry.node_name,
                entry.description,
                json.dumps(entry.data),
                json.dumps(entry.context),
                entry.timestamp,
                entry.correlation_id,
                entry.duration_ms,
                entry.token_count,
            )

        logger.debug(
            "audit_entry_appended",
            entry_id=str(entry.id),
            event_type=entry.event_type.value,
        )

    async def get_by_task(
        self, task_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[AuditEntry]:
        """Get audit entries for a specific task."""
        import json

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_log
                WHERE task_id = $1
                ORDER BY timestamp ASC
                LIMIT $2 OFFSET $3
                """,
                task_id,
                limit,
                offset,
            )

        entries = []
        for row in rows:
            entries.append(
                AuditEntry(
                    id=row["id"],
                    task_id=row["task_id"],
                    session_id=row["session_id"],
                    event_type=AuditEventType(row["event_type"]),
                    agent_name=row["agent_name"],
                    node_name=row["node_name"],
                    description=row["description"],
                    data=json.loads(row["data"]) if row["data"] else {},
                    context=json.loads(row["context"]) if row["context"] else {},
                    timestamp=row["timestamp"],
                    correlation_id=row["correlation_id"],
                    duration_ms=row["duration_ms"],
                    token_count=row["token_count"],
                )
            )

        return entries

    async def get_by_session(
        self, session_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[AuditEntry]:
        """Get audit entries for a specific session."""
        import json

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_log
                WHERE session_id = $1
                ORDER BY timestamp ASC
                LIMIT $2 OFFSET $3
                """,
                session_id,
                limit,
                offset,
            )

        entries = []
        for row in rows:
            entries.append(
                AuditEntry(
                    id=row["id"],
                    task_id=row["task_id"],
                    session_id=row["session_id"],
                    event_type=AuditEventType(row["event_type"]),
                    agent_name=row["agent_name"],
                    node_name=row["node_name"],
                    description=row["description"],
                    data=json.loads(row["data"]) if row["data"] else {},
                    context=json.loads(row["context"]) if row["context"] else {},
                    timestamp=row["timestamp"],
                    correlation_id=row["correlation_id"],
                    duration_ms=row["duration_ms"],
                    token_count=row["token_count"],
                )
            )

        return entries

    async def get_by_event_type(
        self,
        event_type: AuditEventType,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Get audit entries by event type."""
        import json

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_log
                WHERE event_type = $1
                ORDER BY timestamp DESC
                LIMIT $2 OFFSET $3
                """,
                event_type.value,
                limit,
                offset,
            )

        entries = []
        for row in rows:
            entries.append(
                AuditEntry(
                    id=row["id"],
                    task_id=row["task_id"],
                    session_id=row["session_id"],
                    event_type=AuditEventType(row["event_type"]),
                    agent_name=row["agent_name"],
                    node_name=row["node_name"],
                    description=row["description"],
                    data=json.loads(row["data"]) if row["data"] else {},
                    context=json.loads(row["context"]) if row["context"] else {},
                    timestamp=row["timestamp"],
                    correlation_id=row["correlation_id"],
                    duration_ms=row["duration_ms"],
                    token_count=row["token_count"],
                )
            )

        return entries

    async def get_recent(self, limit: int = 100) -> list[AuditEntry]:
        """Get most recent audit entries."""
        import json

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_log
                ORDER BY timestamp DESC
                LIMIT $1
                """,
                limit,
            )

        entries = []
        for row in rows:
            entries.append(
                AuditEntry(
                    id=row["id"],
                    task_id=row["task_id"],
                    session_id=row["session_id"],
                    event_type=AuditEventType(row["event_type"]),
                    agent_name=row["agent_name"],
                    node_name=row["node_name"],
                    description=row["description"],
                    data=json.loads(row["data"]) if row["data"] else {},
                    context=json.loads(row["context"]) if row["context"] else {},
                    timestamp=row["timestamp"],
                    correlation_id=row["correlation_id"],
                    duration_ms=row["duration_ms"],
                    token_count=row["token_count"],
                )
            )

        return entries

    async def count_by_task(self, task_id: UUID) -> int:
        """Count audit entries for a task."""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE task_id = $1",
                task_id,
            )
        return count or 0
