#!/usr/bin/env python3
"""Seed PostgreSQL with initial schema."""

import asyncio
import os

import asyncpg


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


async def main():
    """Create PostgreSQL schema."""
    url = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:password@localhost:5432/xteam"
    )

    print(f"Connecting to PostgreSQL...")
    conn = await asyncpg.connect(url)

    print("Creating tables and indexes...")
    await conn.execute(CREATE_TABLE_SQL)

    print("Schema created successfully!")

    await conn.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
