# Multi-stage Dockerfile for XTeam Agents MCP Server

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install uv

# Copy studyninja-magic-sdk (local dependency)
COPY studyninja-magic-sdk /tmp/studyninja-magic-sdk
RUN cd /tmp/studyninja-magic-sdk && uv pip install --system -e .

# Copy project files
COPY xteam-agents/pyproject.toml .
COPY xteam-agents/README.md .
COPY xteam-agents/src/ src/

# Install dependencies
RUN uv pip install --system -e ".[dev]"

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY xteam-agents/src/ src/
COPY xteam-agents/pyproject.toml .

# Create non-root user
RUN useradd -m -u 1000 xteam && \
    chown -R xteam:xteam /app

USER xteam

# Expose port for HTTP transport
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - stdio transport
CMD ["python", "-m", "xteam_agents"]

# For HTTP transport, use:
# CMD ["python", "-m", "xteam_agents", "--http"]
