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

### Production Deployment

For production deployment with Traefik reverse proxy and SSL certificates:

```bash
# Run automated setup script
sudo ./scripts/setup-traefik.sh

# Or manually
cp .env.example .env
# Edit .env with production values
docker-compose up -d
```

**Production URLs** (when deployed):
- `https://<domain>` - MCP Server
- `https://traefik.<domain>` - Traefik Dashboard
- `https://qdrant.<domain>` - Qdrant UI
- `https://neo4j.<domain>` - Neo4j Browser
- `https://n8n.<domain>` - n8n Workflows

See [DEPLOYMENT.md](DEPLOYMENT.md) and [TRAEFIK.md](TRAEFIK.md) for details.

### Running the System

```bash
# Run MCP server in STDIO mode (for Claude Desktop)
python -m xteam_agents

# Run with HTTP/SSE transport (for development/testing)
python -m xteam_agents --http

# Run via CLI entry point (STDIO only)
xteam-agents
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=xteam_agents

# Run specific test file
pytest tests/unit/test_memory_manager.py

# Run specific test
pytest tests/unit/test_models.py::test_something

# Run only integration tests
pytest tests/integration/

# Run only unit tests
pytest tests/unit/
```

**Pytest configuration** (from `pyproject.toml`):
- `asyncio_mode = "auto"` — async tests run automatically
- `testpaths = ["tests"]`
- `addopts = "-v --tb=short"`

### Code Quality

```bash
# Linting with ruff
ruff check src/

# Auto-fix linting issues
ruff check src/ --fix

# Type checking with mypy
mypy src/xteam_agents
```

**Ruff configuration**: line-length=100, target Python 3.11, rules: E, F, I, W, UP, B, C4, SIM (E501 ignored).

**Mypy configuration**: strict mode enabled, warns on `return_any` and `unused_ignores`.

## Architecture Overview

### The Validated Knowledge Pipeline

This system implements a **cognitive operating system** where the central architectural principle is that **only validated content reaches shared memory**. The full flow including the self-evolution reflect node:

```
START → analyze → plan → execute → validate → route
                    ↑                           │
                    └──── (replan) ─────────────┘
                                                │
                                     (commit)   ↓
                                          commit → reflect → END
                                                │
                                     (fail,     ↓
                                   max_iter) reflect → END
```

### Critical Architectural Invariant

**Only the `commit_node` (and `reflect_node` for guidelines) can write to shared memory (Semantic/Procedural)**. This is enforced by:

1. No `write_shared_memory` tool is ever exposed to LLM agents
2. The `commit_node` is not an LLM agent — it's a pure system function
3. Memory manager methods enforce write permissions at the function signature level
4. The `commit_node` validates that `is_validated=True` before writing
5. The `reflect_node` generates system guidelines and writes them as validated knowledge

### Memory Backend Architecture

| Backend    | Technology | Memory Type                 | Scope           | Who Can Write           |
|------------|------------|-----------------------------|-----------------|-------------------------|
| Redis      | Redis 7    | Episodic (short-term)       | Private per task| Any node                |
| Qdrant     | Vector DB  | Semantic (validated knowledge)| Shared        | **commit_node + reflect_node ONLY** |
| Neo4j      | Graph DB   | Procedural (relationships)  | Shared          | **commit_node ONLY**    |
| PostgreSQL | SQL        | Audit log (append-only)     | Shared          | Any node                |

**Key Files:**
- `src/xteam_agents/memory/manager.py` — MemoryManager enforces write permissions
- `src/xteam_agents/memory/backends/` — Individual backend implementations
- `src/xteam_agents/memory/embeddings.py` — Embedding generation (OpenAI `text-embedding-3-small`)

### The Six Cognitive Nodes

Each node is a factory function in `src/xteam_agents/graph/nodes/` that returns an async node function:

1. **Analyst** (`analyze.py`) — Understands tasks, gathers context from memory, classifies task complexity
2. **Architect** (`plan.py`) — Designs solutions, creates structured plans with subtasks
3. **Worker** (`execute.py`) — Executes plans using tools, iterative tool-calling loop; routes complex tasks to the adversarial team via `UnifiedExecutor`
4. **Reviewer** (`validate.py`) — Validates results, returns APPROVED/NEEDS_REPLAN/FAILED
5. **Commit Node** (`commit.py`) — NOT an LLM agent; pure system function that gates shared memory writes
6. **Reflect Node** (`reflect.py`) — Self-evolution via automated retrospectives; analyzes execution trace and generates reusable guidelines stored in shared semantic memory

All LLM agent nodes (1–4):
- Have read-only access to shared memory
- Can write to episodic (private) memory
- Cannot directly write to semantic/procedural memory

### Perception Engine

The perception system (`src/xteam_agents/perception/`) provides environmental awareness to agents:

**PerceptionEngine** (`engine.py`) aggregates observations from three sensor categories:

| Category    | Sensors                          | Purpose                                |
|-------------|----------------------------------|----------------------------------------|
| System      | TaskStateSensor, ErrorSensor, BudgetSensor | Monitor internal system state  |
| Environment | APISensor, CISensor, GitSensor, FeedbackSensor | Monitor external integrations |
| Temporal    | DeadlineSensor, TimeoutSensor, CronSensor | Track time-based constraints    |

Observations are sorted by severity: CRITICAL → ERROR → WARNING → INFO. Blocking observations can halt task execution.

**Key Files:**
- `src/xteam_agents/perception/engine.py` — PerceptionEngine coordinator
- `src/xteam_agents/perception/sensors/base.py` — Sensor protocol
- `src/xteam_agents/perception/sensors/system.py` — System state sensors
- `src/xteam_agents/perception/sensors/environment.py` — External integration sensors
- `src/xteam_agents/perception/sensors/temporal.py` — Time-based sensors

### Integrated System: Cognitive OS + Adversarial Agent Team

The system integrates the Adversarial Agent Team for complex tasks:

```
User Request
    ↓
Cognitive OS (analyze → plan → execute → validate → commit → reflect)
                              ↓
                    UnifiedExecutor (routing)
                    ├─ simple/medium → Standard LLM
                    └─ complex/critical → Adversarial Team
                                              ↓
                                    21 AI Agents (1 Orchestrator + 10 pairs)
                                              ↓
                                    Agent-Critic iterative refinement
                                              ↓
                                    5D Quality Scoring
                                              ↓
                                    Results back to Cognitive OS
```

**Execution Modes:**

| Complexity | Execution Mode | Use Case               | Agents Involved              |
|------------|----------------|------------------------|------------------------------|
| simple     | Standard       | Typo fixes, logging    | Single LLM call              |
| medium     | Standard       | API endpoints, tests   | Single LLM call              |
| complex    | Adversarial    | Architecture, refactoring | 21-agent team             |
| critical   | Adversarial    | Security, migrations   | 21-agent team + extended validation |

**Adversarial Agent Team** (21 agents total):
- **1 Orchestrator**: Supreme coordinator, classifies tasks, resolves conflicts
- **10 Agent-Critic Pairs** (in `src/xteam_agents/agents/nodes/pairs/`):
  - TechLead ↔ TechLeadCritic
  - Architect ↔ ArchitectCritic
  - Backend ↔ BackendCritic
  - Frontend ↔ FrontendCritic
  - Data ↔ DataCritic
  - DevOps ↔ DevOpsCritic
  - QA ↔ QACritic (Perfectionist strategy)
  - AIArchitect ↔ AIArchitectCritic
  - Security (Blue Team) ↔ SecurityCritic (Red Team — Adversarial)
  - Performance ↔ PerformanceCritic (Adversarial)

**5D Quality Scoring** (dimensions): Correctness, Completeness, Efficiency, Maintainability, Security

**Integration Points:**
- `src/xteam_agents/integration/state_adapter.py` — State conversion (AgentState ↔ AdversarialAgentState)
- `src/xteam_agents/integration/executor.py` — UnifiedExecutor routes by complexity
- `src/xteam_agents/graph/nodes/analyze.py` — Classifies task complexity
- `src/xteam_agents/graph/nodes/execute.py` — Integrated execution with routing
- `src/xteam_agents/graph/builder.py` — Creates both graphs, shares resources

**Shared Resources:**
- **MemoryManager**: All agents (cognitive + adversarial) use same instance
- **LLM Provider**: Connection pooling across all agents
- **Memory Invariants**: Enforced for both systems

**Key Files:**
- `src/xteam_agents/agents/adversarial_graph.py` — Adversarial team LangGraph
- `src/xteam_agents/agents/adversarial_state.py` — State schema for adversarial agents
- `src/xteam_agents/agents/adversarial_config.py` — Adversarial system configuration
- `src/xteam_agents/agents/orchestrator.py` — Orchestrator agent
- `src/xteam_agents/agents/base.py` — BaseAgent and BaseCritic classes
- `src/xteam_agents/agents/pair_manager.py` — Manager for agent-critic pairs
- `src/xteam_agents/agents/routing.py` — Complexity routing logic
- `examples/integrated_execution.py` — Working example of both modes

### LangGraph State Flow

The cognitive graph is built using LangGraph's `StateGraph`:

- **State Schema**: `src/xteam_agents/models/state.py` — `AgentState` Pydantic model
- **Graph Builder**: `src/xteam_agents/graph/builder.py` — Constructs the graph
- **Edge Logic**: `src/xteam_agents/graph/edges.py` — Routing conditions including `route_after_validation`

**State contains:**
- Task context, messages, analysis, plan
- Subtasks with execution results
- Validation state and iteration counters
- Custom reducers: `merge_messages`, `merge_artifacts` for list fields

**Replan Loop Protection:**
- Max 5 replan iterations (hardcoded in `builder.py:validate_router`)
- After max iterations, task routes to `reflect` node (failure path)
- Prevents infinite validation → replan → validation loops
- Configurable `MAX_REPLAN_ITERATIONS` in settings defaults to 3 (used elsewhere)

### Action Execution System

**Capability Registry Pattern** (`src/xteam_agents/action/registry.py`):
- All actions must be registered before execution
- Security boundary: agents can only invoke registered capabilities
- Default capabilities: `execute_python`, `http_get`, `http_post`, `shell_execute`, `trigger_workflow`

**Action Executor** (`src/xteam_agents/action/executor.py`):
- Handler pattern for action types: CODE, HTTP, SHELL, CI
- Request validation, timeout enforcement
- All executions logged to audit trail

**Action Handlers** (`src/xteam_agents/action/handlers/`):
- `base.py` — Handler protocol/base class
- `code.py` — Python code execution
- `http.py` — HTTP request execution
- `shell.py` — Shell command execution
- `ci.py` — CI/CD pipeline triggers (GitHub Actions, etc.)

### MCP Server Implementation

**Entry Point**: `src/xteam_agents/server/app.py`

Uses FastMCP to expose six tool categories:

1. **Task Tools** (`server/tools/task_tools.py`) — submit_task, get_task_status, get_task_result, cancel_task, list_tasks
2. **Memory Tools** (`server/tools/memory_tools.py`) — query_memory, search_knowledge, get_knowledge_graph, get_task_audit_log
3. **Admin Tools** (`server/tools/admin_tools.py`) — system_health, register_capability, list_capabilities, list_agents, get_audit_log, get_system_config
4. **Code Tools** (`server/tools/code_tools.py`) — execute_python (sandboxed Docker), index_repository (Qdrant indexing)
5. **Web Tools** (`server/tools/web_tools.py`) — search_web (DuckDuckGo), scrape_url (HTML → text)
6. **Filesystem Tools** (`server/tools/filesystem_tools.py`) — list_directory, read_file, write_file (sandboxed to `/app/workspace`)

**Transport Modes:**
- STDIO: Default, for Claude Desktop integration
- HTTP/SSE: Development mode with `--http` flag

**REST API Endpoints** (for dashboard integration, defined in `app.py`):
- `POST /api/tasks` — Submit a task
- `GET /api/tasks` — List tasks
- `GET /api/tasks/{task_id}` — Get task details with audit log
- `POST /api/tasks/{task_id}/cancel` — Cancel a task
- `GET /api/files/list?path=` — List directory
- `GET /api/files/read?path=` — Read file
- `GET /api/memory/search?query=` — Search knowledge
- `POST /api/chat` — RAG-powered chat endpoint
- `GET /api/agents/status` — Agent status (cognitive + adversarial)
- `GET /api/metrics/quality` — 5D quality scoring metrics
- `GET /health` — Health check

### Dashboard

A Streamlit-based web dashboard (`dashboard/`) provides monitoring and control:

- **App**: `dashboard/app.py`
- **Dockerfile**: `dashboard/Dockerfile`
- **Dependencies**: `dashboard/requirements.txt`

Features: task submission/monitoring, agent status visualization, quality metrics, memory search, file browser.

### Task Orchestration

**TaskOrchestrator** (`src/xteam_agents/orchestrator.py`):
- Manages task lifecycle through state machine
- Status flow: PENDING → ANALYZING → PLANNING → EXECUTING → VALIDATING → COMMITTING → COMPLETED/FAILED
- Background async execution
- Task state persisted in Redis during execution
- Final artifacts stored in Qdrant/Neo4j after validation

## Source Code Structure

```
src/xteam_agents/
├── __init__.py              # Package init (exports Settings, TaskOrchestrator, create_mcp_server)
├── __main__.py              # CLI entry point (STDIO and HTTP modes)
├── config.py                # Pydantic Settings configuration
├── orchestrator.py          # Task lifecycle management
│
├── action/                  # Action execution system
│   ├── executor.py          # ActionExecutor
│   ├── registry.py          # CapabilityRegistry
│   └── handlers/            # CODE, HTTP, SHELL, CI handlers
│       ├── base.py
│       ├── code.py
│       ├── http.py
│       ├── shell.py
│       └── ci.py
│
├── agents/                  # Adversarial agent team (21 agents)
│   ├── base.py              # BaseAgent, BaseCritic
│   ├── config.py            # Agent configuration
│   ├── orchestrator.py      # Orchestrator agent
│   ├── pair_manager.py      # Agent-critic pair manager
│   ├── routing.py           # Complexity routing
│   ├── adversarial_config.py
│   ├── adversarial_graph.py # LangGraph for 21-agent team
│   ├── adversarial_init.py
│   ├── adversarial_state.py
│   └── nodes/pairs/         # 10 agent-critic pair implementations
│       ├── tech_lead_pair.py
│       ├── architect_pair.py
│       ├── backend_pair.py
│       ├── frontend_pair.py
│       ├── data_pair.py
│       ├── devops_pair.py
│       ├── qa_pair.py
│       ├── ai_architect_pair.py
│       ├── security_pair.py
│       └── performance_pair.py
│
├── graph/                   # Cognitive graph orchestration
│   ├── builder.py           # LangGraph builder (creates both graphs)
│   ├── edges.py             # Edge routing logic
│   ├── prompts.py           # System prompts for agents
│   └── nodes/               # 6 cognitive nodes
│       ├── analyze.py       # Analyst — understand task
│       ├── plan.py          # Architect — design solution
│       ├── execute.py       # Worker — perform actions
│       ├── validate.py      # Reviewer — validate results
│       ├── commit.py        # Commit — write to shared memory
│       └── reflect.py       # Reflect — self-evolution retrospectives
│
├── integration/             # Cognitive OS + Adversarial bridge
│   ├── executor.py          # UnifiedExecutor (routes by complexity)
│   └── state_adapter.py     # AgentState ↔ AdversarialAgentState
│
├── llm/                     # LLM provider abstraction
│   ├── provider.py          # LLMProvider (OpenAI & Anthropic)
│   └── tools.py             # Tool creation and restrictions
│
├── memory/                  # Multi-backend memory system
│   ├── manager.py           # MemoryManager (write permission enforcement)
│   ├── embeddings.py        # Embedding generation
│   └── backends/
│       ├── base.py          # Backend interface/protocol
│       ├── episodic.py      # Redis — short-term private memory
│       ├── semantic.py      # Qdrant — validated knowledge (vectors)
│       ├── procedural.py    # Neo4j — relationships (graph)
│       ├── audit.py         # PostgreSQL — append-only audit log
│       └── task.py          # Task-specific memory helpers
│
├── models/                  # Data models and schemas
│   ├── state.py             # AgentState (LangGraph state schema)
│   ├── action.py            # ActionRequest, ActionResult, Capability
│   ├── task.py              # TaskRequest, TaskStatus, Priority
│   ├── memory.py            # MemoryArtifact, MemoryType, MemoryScope
│   ├── audit.py             # AuditEntry, AuditEventType
│   └── observation.py       # Observation model for perception
│
├── perception/              # Perception/sensing system
│   ├── engine.py            # PerceptionEngine coordinator
│   └── sensors/
│       ├── base.py          # Sensor protocol
│       ├── system.py        # TaskStateSensor, ErrorSensor, BudgetSensor
│       ├── environment.py   # APISensor, CISensor, GitSensor, FeedbackSensor
│       └── temporal.py      # DeadlineSensor, TimeoutSensor, CronSensor
│
└── server/                  # MCP server and tools
    ├── app.py               # FastMCP server + REST API endpoints
    └── tools/
        ├── task_tools.py    # Task management tools
        ├── memory_tools.py  # Memory query tools
        ├── admin_tools.py   # Administration tools
        ├── code_tools.py    # Code execution (Docker sandbox)
        ├── web_tools.py     # Web search/scraping
        └── filesystem_tools.py  # File operations (sandboxed)
```

## Key Implementation Patterns

### Adding a New Agent Node

1. Create node function in `src/xteam_agents/graph/nodes/your_node.py`
2. Define node logic: factory function takes dependencies, returns `async def node(state: AgentState) -> dict[str, Any]`
3. Add to graph in `src/xteam_agents/graph/builder.py` (both `add_node` and edges)
4. Update edges/routing if needed in `builder.py` or `edges.py`

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

1. Create tool function in appropriate `server/tools/` file (or create a new file)
2. Decorate with `@mcp.tool()` inside a `register_*_tools(mcp, orchestrator)` function
3. Register in `server/app.py` during server initialization (call your register function)
4. Tool automatically exposed via MCP protocol

### Adding a New Sensor

1. Create sensor in `src/xteam_agents/perception/sensors/`
2. Implement the `Sensor` protocol from `base.py`: `name`, `enabled`, `observe()`, `setup()`, `teardown()`
3. Register in `PerceptionEngine._setup_default_sensors()` in `engine.py`

### Adding a New Agent-Critic Pair

1. Create pair file in `src/xteam_agents/agents/nodes/pairs/your_pair.py`
2. Define agent and critic classes extending `BaseAgent` and `BaseCritic`
3. Register in the adversarial graph via `pair_manager.py`
4. Update `adversarial_graph.py` to include the new pair

## Docker Services

| Service      | Technology    | Internal Port | Purpose                     |
|--------------|---------------|---------------|-----------------------------|
| `traefik`    | Traefik v2.11 | 80, 443       | Reverse proxy with auto-SSL |
| `mcp-server` | Python 3.11   | 8000          | XTeam Agents MCP Server     |
| `dashboard`  | Streamlit     | 8501          | Web monitoring dashboard    |
| `redis`      | Redis 7       | 6379          | Episodic memory             |
| `qdrant`     | Qdrant        | 6333, 6334    | Semantic memory (vectors)   |
| `neo4j`      | Neo4j 5       | 7474, 7687    | Procedural memory (graph)   |
| `postgres`   | PostgreSQL 16 | 5432          | Audit log                   |
| `n8n`        | n8n           | 5678          | Workflow automation (optional) |

All services use `expose` instead of `ports` (Traefik handles external access). HTTP automatically redirects to HTTPS.

## Configuration

All configuration via environment variables in `.env` file (see `.env.example`):

**LLM Configuration:**
- `LLM_PROVIDER`: `openai` or `anthropic`
- `LLM_MODEL`: Model name (e.g., `gpt-4o`, `claude-3-5-sonnet-20241022`)
- `LLM_TEMPERATURE`: 0.0–2.0 (default: 0.7)
- `LLM_MAX_TOKENS`: Max response tokens (default: 4096)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`: Required API keys

**Memory Backends:**
- `REDIS_URL`: Redis connection URL for episodic memory
- `QDRANT_URL`: Qdrant URL for semantic memory
- `QDRANT_COLLECTION`: Collection name (default: `xteam_semantic`)
- `NEO4J_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`: Neo4j for procedural memory
- `POSTGRES_URL`: PostgreSQL for audit log

**Embedding Configuration:**
- `EMBEDDING_MODEL`: Embedding model (default: `text-embedding-3-small`)
- `EMBEDDING_DIMENSIONS`: Vector dimensions (default: 1536)

**Server Configuration:**
- `SERVER_HOST`: Bind address (default: `0.0.0.0`)
- `SERVER_PORT`: Port (default: 8000)

**Task Configuration:**
- `TASK_TIMEOUT_SECONDS`: Timeout for individual tasks (default: 300)
- `MAX_RETRIES`: Max retry attempts (default: 3)
- `MAX_REPLAN_ITERATIONS`: Max replan cycles before failing (default: 3)

**Logging:**
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `LOG_JSON`: JSON-formatted logs (default: true)

**Integrations:**
- `N8N_URL`: n8n webhook URL (optional)
- `N8N_API_KEY`: n8n API key (optional)

Configuration loaded via Pydantic Settings in `src/xteam_agents/config.py`.

## Dependencies

**Core** (from `pyproject.toml`):
- `fastmcp >=2.14` — MCP server framework
- `langgraph >=0.3` — Graph-based agent orchestration
- `langchain >=0.3`, `langchain-core`, `langchain-openai`, `langchain-anthropic` — LLM integration
- `pydantic >=2.0`, `pydantic-settings >=2.0` — Data validation and settings
- `redis >=5.0` — Episodic memory backend
- `qdrant-client >=1.12` — Semantic memory backend
- `neo4j >=5.20` — Procedural memory backend
- `asyncpg >=0.30` — PostgreSQL async driver
- `httpx >=0.27` — Async HTTP client
- `structlog >=24.0` — Structured logging
- `uvicorn >=0.30` — ASGI server
- `docker >=7.0` — Docker SDK for sandboxed code execution
- `duckduckgo-search >=5.0` — Web search
- `beautifulsoup4 >=4.12` — HTML parsing

**Dev:**
- `pytest >=8.0`, `pytest-asyncio >=0.23`, `pytest-cov >=4.0`
- `testcontainers >=4.0` — Docker-based test isolation
- `ruff >=0.4` — Linting
- `mypy >=1.10` — Type checking

Build system: `hatchling`.

## Testing Strategy

**Unit Tests** (`tests/unit/`):
- `test_graph_nodes.py` — Test individual graph nodes
- `test_memory_manager.py` — Test memory manager and backends
- `test_models.py` — Test data models
- Mocked external dependencies (memory backends, LLM calls)
- Fast, no external services required

**Integration Tests** (`tests/integration/`):
- `test_graph_full_cycle.py` — Full graph execution cycle
- `test_integrated_execution.py` — Standard + adversarial execution
- `test_mcp_tools.py` — MCP tool functionality
- Use testcontainers for isolated backend instances

**E2E Tests** (`tests/e2e/`):
- `test_docker_compose.py` — Full system with Docker Compose
- Test complete task flows through MCP interface

**Test Fixtures**: Common fixtures in `tests/conftest.py`.

## Common Development Workflows

### Running Tests Against Local Backends

```bash
# Start backends
docker-compose up -d redis qdrant neo4j postgres

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
        "REDIS_URL": "redis://localhost:6379/0"
      }
    }
  }
}
```
3. Restart Claude Desktop
4. Use MCP tools: `submit_task`, `get_task_status`, etc.

### Debugging Graph Execution

1. Add logging in node functions: `logger.info(f"State: {state}")`
2. Check Redis for task state: `redis-cli GET xteam:task_state:{task_id}`
3. Query audit log in PostgreSQL for execution history
4. Enable DEBUG logging: `LOG_LEVEL=DEBUG` in `.env`

### Understanding Memory Flows

**When worker executes and validation succeeds:**
```
Worker → stores artifact in episodic (Redis)
Reviewer → sets is_validated=True
validate_router → routes to commit
commit_node → generates embedding → writes to Qdrant + Neo4j → logs to audit
reflect_node → analyzes execution → optionally creates guideline → END
```

**When validation fails and replan is needed:**
```
Worker → stores artifact in episodic (Redis)
Reviewer → sets should_replan=True, validation_feedback="..."
validate_router → routes back to plan (iteration++)
Architect → reads feedback, creates new plan
Cycle repeats (max 5 times before routing to reflect as failure)
```

## Security Considerations

1. **Memory Isolation**: Architecture prevents agents from directly writing to shared memory
2. **Capability Registry**: Only registered actions can be executed by agents
3. **Audit Trail**: All significant events logged to append-only PostgreSQL audit table
4. **Validation Gate**: Reviewer must approve before commit_node writes to shared memory
5. **Timeout Enforcement**: All actions have configurable timeouts to prevent runaway execution
6. **Sandboxed Code Execution**: Python code runs in Docker containers with network disabled, 512MB memory limit
7. **Filesystem Sandboxing**: Filesystem tools restrict access to `/app/workspace` directory
8. **Path Traversal Protection**: `_validate_path()` resolves and checks all paths against workspace root
