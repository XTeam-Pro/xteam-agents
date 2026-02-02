#!/usr/bin/env python3
"""Health check script for all XTeam Agents backends."""

import asyncio
import os
import sys

import asyncpg
import httpx
import redis.asyncio as redis
from neo4j import AsyncGraphDatabase


async def check_redis():
    """Check Redis connectivity."""
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.from_url(url)
        await client.ping()
        await client.aclose()
        return True, "Redis: OK"
    except Exception as e:
        return False, f"Redis: FAILED - {e}"


async def check_qdrant():
    """Check Qdrant connectivity."""
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/")
            if response.status_code == 200:
                return True, "Qdrant: OK"
            return False, f"Qdrant: FAILED - HTTP {response.status_code}"
    except Exception as e:
        return False, f"Qdrant: FAILED - {e}"


async def check_neo4j():
    """Check Neo4j connectivity."""
    url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    try:
        driver = AsyncGraphDatabase.driver(url, auth=(user, password))
        async with driver.session() as session:
            await session.run("RETURN 1")
        await driver.close()
        return True, "Neo4j: OK"
    except Exception as e:
        return False, f"Neo4j: FAILED - {e}"


async def check_postgres():
    """Check PostgreSQL connectivity."""
    url = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:password@localhost:5432/xteam"
    )
    try:
        conn = await asyncpg.connect(url)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True, "PostgreSQL: OK"
    except Exception as e:
        return False, f"PostgreSQL: FAILED - {e}"


async def main():
    """Run all health checks."""
    print("XTeam Agents Health Check")
    print("=" * 40)

    checks = [
        check_redis(),
        check_qdrant(),
        check_neo4j(),
        check_postgres(),
    ]

    results = await asyncio.gather(*checks, return_exceptions=True)

    all_healthy = True
    for result in results:
        if isinstance(result, Exception):
            print(f"ERROR: {result}")
            all_healthy = False
        else:
            healthy, message = result
            print(message)
            if not healthy:
                all_healthy = False

    print("=" * 40)
    if all_healthy:
        print("All backends healthy!")
        sys.exit(0)
    else:
        print("Some backends are unhealthy!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
