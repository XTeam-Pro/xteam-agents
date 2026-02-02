"""PostgreSQL-based task storage backend."""

from uuid import UUID

import asyncpg
import structlog

from xteam_agents.config import Settings
from xteam_agents.models.task import Priority, TaskInfo, TaskStatus

logger = structlog.get_logger()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY,
    description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 3,
    current_node VARCHAR(50),
    iteration_count INTEGER DEFAULT 0,
    subtasks_total INTEGER DEFAULT 0,
    subtasks_completed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    error TEXT,
    context JSONB DEFAULT '{}',
    result TEXT,
    artifacts JSONB DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
"""


class TaskBackend:
    """Backend for storing task state in PostgreSQL."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Connect to PostgreSQL and ensure table exists."""
        try:
            self._pool = await asyncpg.create_pool(self.settings.postgres_url)
            async with self._pool.acquire() as conn:
                await conn.execute(CREATE_TABLE_SQL)
            logger.info("task_backend_connected")
        except Exception as e:
            logger.error("task_backend_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self._pool:
            await self._pool.close()

    async def health_check(self) -> str:
        """Check connection health."""
        if not self._pool:
            return "disconnected"
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return "healthy"
        except Exception as e:
            return f"unhealthy: {e}"

    async def save_task(self, task: TaskInfo) -> None:
        """Save or update a task."""
        if not self._pool:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tasks (
                    task_id, description, status, priority, current_node,
                    iteration_count, subtasks_total, subtasks_completed,
                    created_at, started_at, completed_at, updated_at, error
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), $12)
                ON CONFLICT (task_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    current_node = EXCLUDED.current_node,
                    iteration_count = EXCLUDED.iteration_count,
                    subtasks_total = EXCLUDED.subtasks_total,
                    subtasks_completed = EXCLUDED.subtasks_completed,
                    started_at = COALESCE(EXCLUDED.started_at, tasks.started_at),
                    completed_at = EXCLUDED.completed_at,
                    updated_at = NOW(),
                    error = EXCLUDED.error
                """,
                task.id,
                task.description,
                task.status.value,
                task.priority.value,
                task.current_node,
                task.iteration_count,
                task.subtasks_total,
                task.subtasks_completed,
                task.created_at,
                task.started_at,
                task.completed_at,
                task.error,
            )

    async def get_task(self, task_id: UUID) -> TaskInfo | None:
        """Get a task by ID."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tasks WHERE task_id = $1", task_id)
            if not row:
                return None

            return TaskInfo(
                id=row["task_id"],
                description=row["description"],
                status=TaskStatus(row["status"]),
                priority=Priority(row["priority"]),
                current_node=row["current_node"],
                iteration_count=row["iteration_count"],
                subtasks_total=row["subtasks_total"],
                subtasks_completed=row["subtasks_completed"],
                created_at=row["created_at"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                error=row["error"],
            )

    async def list_tasks(self, limit: int = 100) -> list[TaskInfo]:
        """List recent tasks."""
        if not self._pool:
            return []

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT $1", limit
            )

            return [
                TaskInfo(
                    id=row["task_id"],
                    description=row["description"],
                    status=TaskStatus(row["status"]),
                    priority=Priority(row["priority"]),
                    current_node=row["current_node"],
                    iteration_count=row["iteration_count"],
                    subtasks_total=row["subtasks_total"],
                    subtasks_completed=row["subtasks_completed"],
                    created_at=row["created_at"],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    error=row["error"],
                )
                for row in rows
            ]
