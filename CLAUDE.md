# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What's New

This version includes two major new systems:

1. **MAGIC System** (Metacognitive Awareness, Adaptive Learning, Generative Collaboration, Intelligent Escalation, Continuous Evolution)
   - Optional human-AI collaboration at every pipeline stage
   - Intelligent escalation based on confidence and autonomy levels
   - Feedback capture and guideline learning
   - Progressive autonomy adjustments
   - 100% backward compatible - zero overhead when disabled

2. **QA Automation System**
   - Multi-agent powered QA orchestration
   - User story generation and analysis
   - Automated testing across 6 domains (E2E, API, Visual, Performance, Security, A11y)
   - Progress tracking with coverage matrix
   - Integration with Streamlit dashboard
   - CI/CD ready with GitHub Actions support

Both systems integrate seamlessly with the existing Cognitive OS and Adversarial Team architecture.

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

**Production URLs** (when deployed on example.com):
- https://example.com - MCP Server
- https://traefik.example.com - Traefik Dashboard
- https://qdrant.example.com - Qdrant UI
- https://neo4j.example.com - Neo4j Browser
- https://n8n.example.com - n8n Workflows

See [DEPLOYMENT.md](/root/xteam-agents/DEPLOYMENT.md) and [TRAEFIK.md](/root/xteam-agents/TRAEFIK.md) for details.

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

# Run MAGIC system tests (includes backward compatibility)
pytest tests/unit/test_magic.py -v

# Run with MAGIC enabled
MAGIC_ENABLED=true pytest tests/unit/test_magic.py -v
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

### Integrated System: Cognitive OS + Adversarial Agent Team

**NEW**: The system now integrates the Adversarial Agent Team for complex tasks:

```
User Request
    ↓
Cognitive OS (analyze → plan → execute → validate → commit)
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

| Complexity | Execution Mode | Use Case | Agents Involved |
|------------|----------------|----------|-----------------|
| simple | Standard | Typo fixes, logging | Single LLM call |
| medium | Standard | API endpoints, tests | Single LLM call |
| complex | Adversarial | Architecture, refactoring | 21-agent team |
| critical | Adversarial | Security, migrations | 21-agent team + extended validation |

**Adversarial Agent Team** (21 agents total):
- **1 Orchestrator**: Supreme coordinator, classifies tasks, resolves conflicts
- **10 Agent-Critic Pairs**:
  - TechLead ↔ TechLeadCritic
  - Architect ↔ ArchitectCritic
  - Backend ↔ BackendCritic
  - Frontend ↔ FrontendCritic
  - Data ↔ DataCritic
  - DevOps ↔ DevOpsCritic
  - QA ↔ QACritic (Perfectionist strategy)
  - AIArchitect ↔ AIArchitectCritic
  - Security (Blue Team) ↔ SecurityCritic (Red Team - Adversarial)
  - Performance ↔ PerformanceCritic (Adversarial)

**Integration Points:**
- `src/xteam_agents/integration/state_adapter.py` - State conversion (AgentState ↔ AdversarialAgentState)
- `src/xteam_agents/integration/executor.py` - UnifiedExecutor routes by complexity
- `src/xteam_agents/graph/nodes/analyze.py` - Classifies task complexity
- `src/xteam_agents/graph/nodes/execute.py` - Integrated execution with routing
- `src/xteam_agents/graph/builder.py` - Creates both graphs, shares resources

**Shared Resources:**
- **MemoryManager**: All agents (cognitive + adversarial) use same instance
- **LLM Provider**: Connection pooling across all agents
- **Memory Invariants**: Enforced for both systems

**Key Files:**
- `src/xteam_agents/agents/adversarial_graph.py` - Adversarial team LangGraph
- `src/xteam_agents/agents/orchestrator.py` - Orchestrator agent
- `src/xteam_agents/agents/base.py` - BaseAgent and BaseCritic classes
- `src/xteam_agents/agents/nodes/pairs/*.py` - All 10 agent-critic pairs
- `examples/integrated_execution.py` - Working example of both modes

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

Uses FastMCP to expose four tool categories:
1. **Task Tools** (`server/tools/task_tools.py`) - submit_task, get_task_status, cancel_task, list_tasks
2. **Memory Tools** (`server/tools/memory_tools.py`) - query_memory, search_knowledge, get_knowledge_graph
3. **Admin Tools** (`server/tools/admin_tools.py`) - system_health, register_capability, list_agents
4. **MAGIC Tools** (`server/tools/magic_tools.py`) - configure_magic, respond_to_escalation, list_pending_escalations, submit_feedback, get_confidence_scores, get_magic_session, get_evolution_metrics

**Transport Modes:**
- STDIO: Default, for Claude Desktop integration
- HTTP: Development mode with `--http` flag

**REST API Endpoints** (in addition to MCP tools):
- `GET /api/magic/escalations` - List pending escalations
- `POST /api/magic/escalations/{id}/respond` - Respond to escalation
- `GET /api/magic/sessions` - List active sessions
- `POST /api/magic/feedback` - Submit feedback
- `GET /api/magic/confidence/{task_id}` - Get confidence scores
- `GET /api/magic/evolution` - Get evolution metrics

### Task Orchestration

**TaskOrchestrator** (`src/xteam_agents/orchestrator.py`):
- Manages task lifecycle through state machine
- Status flow: PENDING → ANALYZING → PLANNING → EXECUTING → VALIDATING → COMMITTING → COMPLETED/FAILED
- Background async execution
- Task state persisted in Redis during execution
- Final artifacts stored in Qdrant/Neo4j after validation

### MAGIC System: Human-AI Collaboration

**NEW**: The system now includes the MAGIC (Metacognitive Awareness, Adaptive Learning, Generative Collaboration, Intelligent Escalation, Continuous Evolution) system for optional human-AI collaboration at every pipeline stage.

**Key Features:**
- **Optional Overlay**: Zero overhead when disabled (`MAGIC_ENABLED=false`)
- **5 Autonomy Levels**: SUPERVISED → GUIDED → COLLABORATIVE (default) → AUTONOMOUS → TRUSTED
- **Intelligent Escalation**: Routes to humans based on confidence and autonomy level
- **Confidence Scoring**: Multi-dimensional assessment (factual_accuracy, completeness, relevance, coherence, novelty_risk)
- **Human Checkpoints**: 4 available stages (after_analyze, after_plan, after_execute, after_validate)
- **Feedback Learning**: Converts human feedback to persistent guidelines
- **Evolution Metrics**: Tracks escalation rate, approval rate, autonomy progression

**Architecture:**
```
Pipeline Flow with MAGIC Checkpoints:
analyze → [checkpoint_after_analyze?] → plan → [checkpoint_after_plan?]
  → execute → [checkpoint_after_execute?] → validate → [checkpoint_after_validate?] → commit
```

**Key Files:**
- `src/xteam_agents/magic/core.py` - MAGICCore coordinator
- `src/xteam_agents/magic/metacognition.py` - Confidence assessment engine
- `src/xteam_agents/magic/escalation.py` - Escalation routing logic
- `src/xteam_agents/magic/session.py` - Collaborative session management
- `src/xteam_agents/magic/feedback.py` - Feedback collection and guideline generation
- `src/xteam_agents/magic/evolution.py` - Progressive autonomy adjustments
- `src/xteam_agents/graph/nodes/human_checkpoint.py` - Checkpoint nodes
- `src/xteam_agents/models/magic.py` - All MAGIC data models

**Configuration:**
```bash
MAGIC_ENABLED=true|false              # Enable/disable MAGIC system
MAGIC_DEFAULT_AUTONOMY=collaborative  # Default autonomy level
MAGIC_DEFAULT_CONFIDENCE_THRESHOLD=0.6  # Escalation threshold
MAGIC_DEFAULT_ESCALATION_TIMEOUT=300  # Human response timeout (seconds)
MAGIC_DEFAULT_FALLBACK=continue       # Fallback policy on timeout
MAGIC_DEFAULT_CHECKPOINTS=""          # Default checkpoints
MAGIC_WEBHOOK_URL=""                  # Optional notification webhook
```

**Per-Task Configuration:**
```json
{
  "description": "Task description",
  "magic": {
    "autonomy_level": "guided",
    "confidence_threshold": 0.8,
    "checkpoints": ["after_analyze", "after_plan"],
    "escalation_timeout": 600
  }
}
```

### QA Automation System

**NEW**: QA Automation orchestration with multiple agent-powered testing phases.

**Architecture:**
- **User Story Analyst**: Generates user stories with acceptance criteria from system understanding
- **Test Engineer Agents**: Create test code for E2E, API, visual, performance, security, accessibility
- **QA Orchestrator**: Coordinates analysis → test_creation → execution → reporting phases
- **Progress Matrix**: Tracks coverage, pass rates, automation status per feature

**Supported Test Types:**
- E2E Tests (Puppeteer/Playwright) - Full user workflows
- API Tests (Jest/Axios) - REST endpoint validation
- Visual Regression (PixelMatch) - Screenshot comparison
- Performance Tests (Lighthouse) - Load time and metrics
- Security Tests (OWASP) - Vulnerability scanning
- Accessibility Tests (Axe) - A11y compliance

**Key Files:**
- `qa-automation/src/agents/orchestrator.ts` - QA orchestration orchestrator
- `qa-automation/src/agents/user-story-analyst.ts` - User story generation
- `qa-automation/tests/e2e/**/*.spec.ts` - E2E test suites
- `qa-automation/tests/api/**/*.spec.ts` - API test suites
- `qa-automation/reports/` - Test results and progress matrix

**Running QA:**
```bash
cd qa-automation
npm install

# Generate user stories
npm run qa:orchestrate -- --phase=analysis

# Run all tests
npm run test:all

# Generate report
npm run qa:orchestrate -- --phase=reporting

# View results
npm run qa:serve-report
```

**Dashboard Integration:**
- New "QA Automation" page in Streamlit dashboard
- Real-time test result visualization
- Coverage metrics and pass rates
- User story tracking with automation status

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

### Configuring MAGIC System per Task

1. When submitting task via MCP, include `magic` metadata:
```json
{
  "description": "Complex task requiring human oversight",
  "context": {...},
  "magic": {
    "autonomy_level": "guided",
    "confidence_threshold": 0.75,
    "checkpoints": ["after_analyze", "after_plan"],
    "escalation_timeout": 600
  }
}
```

2. System will:
   - Create MAGICTaskConfig from metadata
   - Place human checkpoints at specified stages
   - Assess confidence at each node
   - Escalate to human if confidence < threshold
   - Track feedback and generate guidelines

### Adding a New MAGIC Subsystem

1. Create module in `src/xteam_agents/magic/your_system.py`
2. Implement required interface with async methods
3. Register in `MAGICCore` initialization in `magic/core.py`
4. Add corresponding MCP tools in `server/tools/magic_tools.py`
5. Add Pydantic models to `src/xteam_agents/models/magic.py` if needed
6. Update state schema in `src/xteam_agents/models/state.py`

## Docker and Traefik Setup

The project includes Traefik reverse proxy for production deployments:

- **Automatic HTTPS**: Let's Encrypt certificates with auto-renewal
- **Service Discovery**: Docker labels for automatic routing
- **Email**: cert@example.com for Let's Encrypt notifications
- **Server IP**: YOUR_SERVER_IP (production)

**Traefik Configuration in docker-compose.yml**:
- All services use `expose` instead of `ports` (internal only)
- Traefik labels define routing rules and SSL configuration
- Services are only accessible via HTTPS through Traefik
- HTTP automatically redirects to HTTPS

**Important**: When modifying services, use Traefik labels for external access, not direct port mapping.

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

**MAGIC System Configuration:**
- `MAGIC_ENABLED`: Enable/disable human-AI collaboration (default: false)
- `MAGIC_DEFAULT_AUTONOMY`: Default autonomy level (default: collaborative)
- `MAGIC_DEFAULT_CONFIDENCE_THRESHOLD`: Escalation threshold 0.0-1.0 (default: 0.6)
- `MAGIC_DEFAULT_ESCALATION_TIMEOUT`: Human response timeout in seconds (default: 300)
- `MAGIC_DEFAULT_FALLBACK`: Fallback on timeout - continue|pause|fail (default: continue)
- `MAGIC_DEFAULT_CHECKPOINTS`: Comma-separated checkpoints to enable (default: empty)
- `MAGIC_WEBHOOK_URL`: Optional webhook for escalation notifications (default: empty)

Configuration loaded via Pydantic Settings in `src/xteam_agents/config.py`.

## Important Files for Understanding

**Core Architecture:**
- `src/xteam_agents/graph/builder.py` - Graph structure and flow (with conditional MAGIC checkpoint edges)
- `src/xteam_agents/memory/manager.py` - Memory invariants and enforcement
- `src/xteam_agents/orchestrator.py` - Task lifecycle management, MAGICCore initialization
- `src/xteam_agents/models/state.py` - State schema with MAGIC fields and reducers

**Agent Nodes:**
- `src/xteam_agents/graph/nodes/commit.py` - The gatekeeper to shared memory, guideline commitment
- `src/xteam_agents/graph/nodes/validate.py` - Validation decision logic
- `src/xteam_agents/graph/nodes/human_checkpoint.py` - MAGIC checkpoint nodes at 4 stages
- `src/xteam_agents/graph/edges.py` - Routing logic including replan conditions and checkpoint branches

**MAGIC System:**
- `src/xteam_agents/magic/core.py` - MAGICCore central coordinator
- `src/xteam_agents/magic/metacognition.py` - Confidence assessment with 5 dimensions
- `src/xteam_agents/magic/escalation.py` - Escalation decision matrix by autonomy level
- `src/xteam_agents/magic/feedback.py` - Feedback collection and guideline queuing
- `src/xteam_agents/magic/session.py` - Collaborative session management with async response waiting
- `src/xteam_agents/magic/evolution.py` - Progressive autonomy adjustments and metrics
- `src/xteam_agents/models/magic.py` - All MAGIC Pydantic models and enums

**Tool System:**
- `src/xteam_agents/llm/tools.py` - Tool creation and restrictions
- `src/xteam_agents/action/executor.py` - Action execution with handlers

**Server & MCP:**
- `src/xteam_agents/server/app.py` - MCP server entry point with MAGIC tools registration
- `src/xteam_agents/server/tools/magic_tools.py` - 7 MAGIC MCP tools
- `src/xteam_agents/__main__.py` - CLI entry point

**QA Automation:**
- `qa-automation/src/agents/orchestrator.ts` - QA orchestration phases
- `qa-automation/src/agents/user-story-analyst.ts` - User story generation
- `qa-automation/tests/` - Test suite organization by type

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
        "MAGIC_ENABLED": "true",
        ...
      }
    }
  }
}
```
3. Restart Claude Desktop
4. Use MCP tools: `submit_task`, `get_task_status`, MAGIC tools, etc.

### Testing MAGIC System

```bash
# Test MAGIC components (all backward compatibility tests included)
pytest tests/unit/test_magic.py -v

# Test with MAGIC enabled in environment
MAGIC_ENABLED=true pytest tests/unit/test_magic.py

# Test with specific autonomy level
MAGIC_DEFAULT_AUTONOMY=guided pytest tests/unit/test_magic.py

# Run integration tests with local backends
docker-compose up -d
MAGIC_ENABLED=true pytest tests/integration/ -v
docker-compose down
```

### Running QA Automation

```bash
cd qa-automation

# Install dependencies
npm install

# Generate user stories and analysis
npm run qa:orchestrate -- --phase=analysis

# Run all test suites
npm run test:all

# Run only E2E tests
npm run test:e2e -- --watch

# Run only API tests
npm run test:api

# Generate reports
npm run qa:orchestrate -- --phase=reporting

# View Allure report
npm run qa:serve-report
```

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
- `test_magic.py` - Comprehensive MAGIC system unit tests with backward compatibility checks

**Integration Tests** (`tests/integration/`):
- Test components together with real backends
- Use testcontainers for isolated backend instances
- Slower but verify real interactions

**E2E Tests** (`tests/e2e/`):
- Full system tests with docker-compose
- Test complete task flows through MCP interface
- Most realistic but slowest

**QA Tests** (`qa-automation/tests/`):
- E2E tests for Streamlit dashboard (Puppeteer/Playwright)
- API tests for REST endpoints (Jest/Axios)
- Visual regression tests (PixelMatch)
- Performance tests (Lighthouse)
- Security tests (OWASP vulnerability scanning)
- Accessibility tests (Axe)
- Organized by test type with corresponding Jest configs

**MAGIC System Testing:**
- All MAGIC features tested in `tests/unit/test_magic.py`
- Backward compatibility verified (zero overhead when disabled)
- Escalation decision matrix tested across all autonomy levels
- Feedback-to-guideline conversion tested
- Async response waiting with timeouts tested
- Evolution metrics calculation tested
- Human checkpoint passthrough tested when MAGIC disabled

## Dashboard Features

The Streamlit dashboard includes several pages for monitoring and controlling the system:

**Standard Pages:**
- **Live Agents** - Real-time agent state with Mission Control header, cognitive graph visualization
- **Adversarial Team** - 21-agent team status, debates, quality scoring
- **Quality Metrics** - Task pass rates, resolution times, performance analysis
- **Tasks** - Task list, status tracking, artifact viewing
- **Chat** - Real-time communication interface
- **Workspace** - Custom workspace configuration

**MAGIC Control Page** (when `MAGIC_ENABLED=true`):
- **Pending Escalations** - Live escalation list with response buttons and confidence scores
- **Active Sessions** - Real-time collaborative session list with message feeds
- **Confidence Dashboard** - Radar chart with 5-dimensional breakdown
- **Feedback & Learning** - Submit feedback, generated guidelines, human preference profiles
- **Evolution Metrics** - Escalation rate, approval rate, autonomy progression

**QA Dashboard** (in `qa-automation/`):
- **User Stories** - Progress matrix, coverage tracking
- **Test Results** - Pass rates, failed test details
- **Coverage Metrics** - Automated vs manual vs not tested breakdown
- **Performance Trends** - Test execution times over time

## Security Considerations

1. **Memory Isolation**: Architecture prevents agents from directly writing to shared memory
2. **Capability Registry**: Only registered actions can be executed by agents
3. **Audit Trail**: All significant events logged to append-only PostgreSQL audit table
4. **Validation Gate**: Reviewer must approve before commit_node writes to shared memory
5. **Timeout Enforcement**: All actions have configurable timeouts to prevent runaway execution
6. **MAGIC Write Invariant**: Feedback system respects commit_node's exclusive write permission to shared memory
7. **Escalation Security**: Only valid autonomy levels and confidence thresholds accepted
8. **Session Expiration**: Collaborative sessions expire after 4 hours (configurable)
