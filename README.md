# XTeam Agents

Cognitive Operating System with configurable LLM (OpenAI/Anthropic), 4 memory backends (Redis, Qdrant, Neo4j, PostgreSQL), LangGraph orchestration, and full MCP control surface via FastMCP.

## Architecture

### Cognitive Graph Flow

```
START → [analyze] → [plan] → [execute] → [validate] → route_after_validation
                       ↑                                    │
                       └──────── (replan) ─────────────────┘
                                                            │
                                                   (commit) ↓
                                                        [commit] → END
```

### Agents

| Agent | Role | Memory Access |
|-------|------|---------------|
| Analyst | Understand tasks, gather context | Read all, Write episodic |
| Architect | Design solutions, create plans | Read all, Write episodic |
| Worker | Execute plans, perform actions | Read all, Write episodic |
| Reviewer | Validate results | Read all, Write episodic |
| Commit Node | Store validated knowledge | **Write shared (semantic, procedural)** |

### Memory Backends

| Backend | Type | Purpose | Who Writes |
|---------|------|---------|------------|
| Redis | Episodic | Short-term, private memory | Any node |
| Qdrant | Semantic | Vector-searchable knowledge | commit_node only |
| Neo4j | Procedural | Graph-based relationships | commit_node only |
| PostgreSQL | Audit | Append-only event log | Any node |

### Key Invariants

1. **Only validated content reaches shared memory** - The commit_node is the single write point
2. **Agents cannot write to shared memory directly** - No `write_shared_memory` tool
3. **All actions require registered capabilities** - Security boundary via CapabilityRegistry
4. **Audit log is append-only** - No UPDATE or DELETE operations

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI or Anthropic API key

### Installation

```bash
# Clone the repository
git clone https://github.com/xteam/xteam-agents.git
cd xteam-agents

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Or run locally for development
pip install -e ".[dev]"
python -m xteam_agents --http
```

### Using with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "xteam-agents": {
      "command": "python",
      "args": ["-m", "xteam_agents"],
      "env": {
        "OPENAI_API_KEY": "your-key",
        "REDIS_URL": "redis://localhost:6379/0",
        "QDRANT_URL": "http://localhost:6333",
        "NEO4J_URL": "bolt://localhost:7687",
        "NEO4J_PASSWORD": "password",
        "POSTGRES_URL": "postgresql://postgres:password@localhost:5432/xteam"
      }
    }
  }
}
```

## MCP Tools

### Task Management

- `submit_task` - Submit a new task for execution
- `get_task_status` - Check task progress
- `get_task_result` - Get completed task results
- `cancel_task` - Cancel a running task
- `list_tasks` - List all tasks

### Memory & Knowledge

- `query_memory` - Search across all memory types
- `search_knowledge` - Semantic search in validated knowledge
- `get_knowledge_graph` - Get task knowledge relationships
- `get_task_audit_log` - Get task execution history

### Administration

- `list_agents` - See all cognitive agents
- `get_audit_log` - System-wide audit log
- `register_capability` - Add new action capabilities
- `list_capabilities` - See available actions
- `system_health` - Check system status

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `openai` or `anthropic` | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `LLM_MODEL` | Model name | `gpt-4o` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `QDRANT_URL` | Qdrant connection URL | `http://localhost:6333` |
| `NEO4J_URL` | Neo4j connection URL | `bolt://localhost:7687` |
| `POSTGRES_URL` | PostgreSQL connection URL | - |

See `.env.example` for all options.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=xteam_agents

# Type checking
mypy src/xteam_agents

# Linting
ruff check src/
```

## License

MIT
