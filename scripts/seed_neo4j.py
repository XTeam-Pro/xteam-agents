#!/usr/bin/env python3
"""Seed Neo4j with initial schema and sample data."""

import asyncio
import os

from neo4j import AsyncGraphDatabase


async def main():
    """Create Neo4j schema and sample data."""
    url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    print(f"Connecting to Neo4j at {url}...")
    driver = AsyncGraphDatabase.driver(url, auth=(user, password))

    async with driver.session() as session:
        # Create indexes
        print("Creating indexes...")
        await session.run(
            "CREATE INDEX artifact_id IF NOT EXISTS FOR (a:Artifact) ON (a.id)"
        )
        await session.run(
            "CREATE INDEX task_id IF NOT EXISTS FOR (t:Task) ON (t.id)"
        )
        await session.run(
            "CREATE INDEX artifact_task_id IF NOT EXISTS FOR (a:Artifact) ON (a.task_id)"
        )

        # Create constraints
        print("Creating constraints...")
        await session.run(
            "CREATE CONSTRAINT artifact_unique_id IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE"
        )
        await session.run(
            "CREATE CONSTRAINT task_unique_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE"
        )

        print("Schema created successfully!")

    await driver.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
