#!/bin/bash
# Run the integrated execution example inside Docker network

docker run --rm -it \
  --network xteam-agents_xteam-network \
  -v "$(pwd):/app" \
  -w /app \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e LLM_PROVIDER="${LLM_PROVIDER:-openai}" \
  -e LLM_MODEL="${LLM_MODEL:-gpt-4o}" \
  -e REDIS_URL="redis://xteam-redis:6379/0" \
  -e QDRANT_URL="http://xteam-qdrant:6333" \
  -e NEO4J_URL="bolt://xteam-neo4j:7687" \
  -e NEO4J_USER="neo4j" \
  -e NEO4J_PASSWORD="${NEO4J_PASSWORD:-Uhfa1^Uhfa}" \
  -e POSTGRES_URL="postgresql://postgres:${POSTGRES_PASSWORD:-gfhjkmvfhjkm}@xteam-postgres:5432/xteam" \
  python:3.12-slim \
  bash -c "
    pip install -q -e . && \
    python3 examples/integrated_execution.py
  "
