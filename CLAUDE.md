# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation

```bash
# Install package with dev dependencies
pip install -e ".[dev]"

# Start all backend services (Redis, Qdrant, Neo4j, PostgreSQL)
docker-compose up -d

# Stop all services
docker-compose down
```

### Running the System

```bash
# Run MCP server in STDIO mode (for Claude Desktop)
python -m xteam_agents

# Run with HTTP server (for development/testing)
python -m xteam_agents --http
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=xteam_agents

# Run specific test file
pytest tests/unit/test_memory.py

# Run specific test
pytest tests/unit/test_memory.py::test_episodic_memory

# Run only integration tests
pytest tests/integration/

# Run only unit tests
pytest tests/unit/
```

### Code Quality

```bash
# Linting with ruff
ruff check src/

# Auto-fix linting issues
ruff check src/ --fix

# Type checking with mypy
mypy src/xteam_agents
```

## Architecture Overview

### The Validated Knowledge Pipeline

This system implements a **cognitive operating system** where the central architectural principle is that **only validated content reaches shared memory**. The flow is:

```
START → analyze → plan → execute → validate → route_after_validation
                   ↑                              │
                   └───── (replan) ──────────────┘
                                                  │
                                        (commit) ↓
                                             commit → END
```

### Critical Architectural Invariant

**Only the `commit_node` can write to shared memory (Semantic/Procedural)**. This is enforced by:

1. No `write_shared_memory` tool is ever exposed to LLM agents
2. The `commit_node` is not an LLM agent - it's a pure system function
3. Memory manager methods enforce write permissions at the function signature level
4. The `commit_node` validates that `is_validated=True` before writing

### Memory Backend Architecture

| Backend | Technology | Memory Type | Scope | Who Can Write |
|---------|-----------|-------------|-------|---------------|
| Redis | Redis | Episodic (short-term) | Private per task | Any node |
| Qdrant | Vector DB | Semantic (validated knowledge) | Shared | **commit_node ONLY** |
| Neo4j | Graph DB | Procedural (relationships) | Shared | **commit_node ONLY** |
| PostgreSQL | SQL | Audit log (append-only) | Shared | Any node |

**Key Files:**
- `src/xteam_agents/memory/manager.py` - MemoryManager enforces write permissions
- `src/xteam_agents/memory/backends/` - Individual backend implementations

### The Five Cognitive Agents

Each agent is a factory function in `src/xteam_agents/graph/nodes/` that returns an async node function:

1. **Analyst** (`analyze.py`) - Understands tasks, gathers context from memory
2. **Architect** (`plan.py`) - Designs solutions, creates structured plans with subtasks
3. **Worker** (`execute.py`) - Executes plans using tools, iterative tool-calling loop (max 10 iterations)
4. **Reviewer** (`validate.py`) - Validates results, returns APPROVED/NEEDS_REPLAN/FAILED
5. **Commit Node** (`commit.py`) - NOT an LLM agent, pure system function that gates shared memory

All agents except commit_node:
- Have read-only access to shared memory
- Can write to episodic (private) memory
- Cannot directly write to semantic/procedural memory

### LangGraph State Flow

The cognitive graph is built using LangGraph's `StateGraph`:

- **State Schema**: `src/xteam_agents/models/state.py` - `AgentState` Pydantic model
- **Graph Builder**: `src/xteam_agents/graph/builder.py` - Constructs the graph
- **Edge Logic**: `src/xteam_agents/graph/edges.py` - Routing conditions including `route_after_validation`

**State contains:**
- Task context, messages, analysis, plan
- Subtasks with execution results
- Validation state and iteration counters
- Custom reducers: `merge_messages`, `merge_artifacts` for list fields

**Replan Loop Protection:**
- Max 3 replan iterations (configurable via `MAX_REPLAN_ITERATIONS`)
- After max iterations, task routes to fail_handler
- Prevents infinite validation → replan → validation loops

### Action Execution System

**Capability Registry Pattern** (`src/xteam_agents/action/registry.py`):
- All actions must be registered before execution
- Security boundary: agents can only invoke registered capabilities
- Default capabilities: `execute_python`, `http_get`, `http_post`, `shell_execute`, `trigger_workflow`

**Action Executor** (`src/xteam_agents/action/executor.py`):
- Handler pattern for action types: CODE, HTTP, SHELL, CI
- Request validation, timeout enforcement
- All executions logged to audit trail

### MCP Server Implementation

**Entry Point**: `src/xteam_agents/server/app.py`

Uses FastMCP to expose three tool categories:
1. **Task Tools** (`server/tools/task_tools.py`) - submit_task, get_task_status, cancel_task, list_tasks
2. **Memory Tools** (`server/tools/memory_tools.py`) - query_memory, search_knowledge, get_knowledge_graph
3. **Admin Tools** (`server/tools/admin_tools.py`) - system_health, register_capability, list_agents

**Transport Modes:**
- STDIO: Default, for Claude Desktop integration
- HTTP: Development mode with `--http` flag

### Task Orchestration

**TaskOrchestrator** (`src/xteam_agents/orchestrator.py`):
- Manages task lifecycle through state machine
- Status flow: PENDING → ANALYZING → PLANNING → EXECUTING → VALIDATING → COMMITTING → COMPLETED/FAILED
- Background async execution
- Task state persisted in Redis during execution
- Final artifacts stored in Qdrant/Neo4j after validation

## Key Implementation Patterns

### Adding a New Agent Node

1. Create node function in `src/xteam_agents/graph/nodes/your_node.py`
2. Define node logic: takes `AgentState`, returns dict updates
3. Add to graph in `src/xteam_agents/graph/builder.py`
4. Update edges if needed in `src/xteam_agents/graph/edges.py`

### Adding a New Memory Backend

1. Implement backend in `src/xteam_agents/memory/backends/your_backend.py`
2. Follow interface: `read()`, `write()`, `search()`, `connect()`, `disconnect()`
3. Update `MemoryManager` in `src/xteam_agents/memory/manager.py`
4. Add configuration to `src/xteam_agents/config.py`

### Adding a New Action Capability

1. Create handler in `src/xteam_agents/action/handlers/your_handler.py`
2. Implement `Handler` protocol: `async def execute(request: ActionRequest) -> ActionResult`
3. Register in `CapabilityRegistry` during initialization
4. Action types defined in `src/xteam_agents/models/action.py`

### Adding a New MCP Tool

1. Create tool function in appropriate `server/tools/` file
2. Decorate with `@mcp.tool()`
3. Register in `server/app.py` during server initialization
4. Tool automatically exposed via MCP protocol

## Configuration

All configuration via environment variables in `.env` file (see `.env.example`):

**LLM Configuration:**
- `LLM_PROVIDER`: `openai` or `anthropic`
- `LLM_MODEL`: Model name (e.g., `gpt-4o`, `claude-3-5-sonnet-20241022`)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`: Required API keys

**Memory Backends:**
- `REDIS_URL`: Redis connection URL for episodic memory
- `QDRANT_URL`: Qdrant URL for semantic memory
- `NEO4J_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j for procedural memory
- `POSTGRES_URL`: PostgreSQL for audit log

**Task Configuration:**
- `TASK_TIMEOUT_SECONDS`: Timeout for individual tasks (default: 300)
- `MAX_RETRIES`: Max retry attempts (default: 3)
- `MAX_REPLAN_ITERATIONS`: Max replan cycles before failing (default: 3)

Configuration loaded via Pydantic Settings in `src/xteam_agents/config.py`.

## Important Files for Understanding

**Core Architecture:**
- `src/xteam_agents/graph/builder.py` - Graph structure and flow
- `src/xteam_agents/memory/manager.py` - Memory invariants and enforcement
- `src/xteam_agents/orchestrator.py` - Task lifecycle management
- `src/xteam_agents/models/state.py` - State schema with reducers

**Agent Nodes:**
- `src/xteam_agents/graph/nodes/commit.py` - The gatekeeper to shared memory
- `src/xteam_agents/graph/nodes/validate.py` - Validation decision logic
- `src/xteam_agents/graph/edges.py` - Routing logic including replan conditions

**Tool System:**
- `src/xteam_agents/llm/tools.py` - Tool creation and restrictions
- `src/xteam_agents/action/executor.py` - Action execution with handlers

**Server:**
- `src/xteam_agents/server/app.py` - MCP server entry point
- `src/xteam_agents/__main__.py` - CLI entry point

## Common Development Workflows

### Running Tests Against Local Backends

```bash
# Start backends
docker-compose up -d

# Run integration tests
pytest tests/integration/

# Stop backends
docker-compose down
```

### Testing with Claude Desktop

1. Build and install locally: `pip install -e ".[dev]"`
2. Configure in `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "xteam-agents": {
      "command": "python",
      "args": ["-m", "xteam_agents"],
      "env": {
        "OPENAI_API_KEY": "...",
        "REDIS_URL": "redis://localhost:6379/0",
        ...
      }
    }
  }
}
```
3. Restart Claude Desktop
4. Use MCP tools: `submit_task`, `get_task_status`, etc.

### Debugging Graph Execution

The graph execution is async and stateful. To debug:

1. Add logging in node functions: `logger.info(f"State: {state}")`
2. Check Redis for task state: `redis-cli GET xteam:task_state:{task_id}`
3. Query audit log in PostgreSQL for execution history
4. Enable DEBUG logging: `LOG_LEVEL=DEBUG` in `.env`

### Understanding Memory Flows

**When worker executes and validation succeeds:**
```
Worker → stores artifact in episodic (Redis)
Reviewer → sets is_validated=True
route_after_validation → routes to commit
commit_node → generates embedding → writes to Qdrant + Neo4j → logs to audit
```

**When validation fails and replan is needed:**
```
Worker → stores artifact in episodic (Redis)
Reviewer → sets should_replan=True, validation_feedback="..."
route_after_validation → routes back to plan (iteration++)
Architect → reads feedback, creates new plan
Cycle repeats (max 3 times)
```

## Testing Strategy

**Unit Tests** (`tests/unit/`):
- Test individual components in isolation
- Mock external dependencies (memory backends, LLM calls)
- Fast, no external services required

**Integration Tests** (`tests/integration/`):
- Test components together with real backends
- Use testcontainers for isolated backend instances
- Slower but verify real interactions

**E2E Tests** (`tests/e2e/`):
- Full system tests with docker-compose
- Test complete task flows through MCP interface
- Most realistic but slowest

## Security Considerations

1. **Memory Isolation**: Architecture prevents agents from directly writing to shared memory
2. **Capability Registry**: Only registered actions can be executed by agents
3. **Audit Trail**: All significant events logged to append-only PostgreSQL audit table
4. **Validation Gate**: Reviewer must approve before commit_node writes to shared memory
5. **Timeout Enforcement**: All actions have configurable timeouts to prevent runaway execution
