# XTeam Agents

**Cognitive Operating System + Adversarial Agent Team + Human-AI Collaboration (Enterprise Grade)**
Status: **PRODUCTION READY**
Reference: [SSOT.md](./SSOT.md) (Single Source of Truth) | [CLAUDE.md](./CLAUDE.md) (Development Guide)

Integrated AI system combining:
- **Cognitive OS**: Validated knowledge pipeline with 4 memory backends
- **Adversarial Agent Team**: 21 AI agents for high-quality complex tasks
- **MAGIC System**: Human-AI collaboration with intelligent escalation & progressive autonomy
- **QA Automation**: Multi-agent powered testing orchestration
- **Automatic Routing**: Simple tasks → fast, Complex tasks → thorough

✨ **NEW**: MAGIC System & QA Automation! See [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) and [CLAUDE.md](./CLAUDE.md)

## Architecture

See [SSOT.md](./SSOT.md) for the canonical architectural definition.

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

### Integrated Execution

**NEW**: The system now automatically routes tasks based on complexity:

| Complexity | Mode | Execution | Time |
|------------|------|-----------|------|
| simple | Standard | Single LLM call | ~5s |
| medium | Standard | Single LLM call | ~10s |
| complex | Adversarial | 21-agent team | ~60s |
| critical | Adversarial | 21-agent team + extended validation | ~120s |

**Adversarial Agent Team** (activated for complex/critical tasks):
- 1 Orchestrator (supreme coordinator)
- 10 Agent-Critic Pairs (iterative refinement)
- 5D Quality Scoring (Correctness, Completeness, Quality, Performance, Security)
- Conflict resolution and final approval

See [INTEGRATION_USAGE.md](./INTEGRATION_USAGE.md) for details.

### MAGIC System: Human-AI Collaboration

**NEW**: Optional human-AI collaboration layer at every pipeline stage:

- **5 Autonomy Levels**: SUPERVISED → GUIDED → COLLABORATIVE → AUTONOMOUS → TRUSTED
- **Intelligent Escalation**: Routes to human based on confidence and autonomy level
- **Confidence Scoring**: Multi-dimensional assessment (5 dimensions)
- **Human Checkpoints**: 4 optional stages (after_analyze, after_plan, after_execute, after_validate)
- **Feedback Learning**: Converts feedback to persistent guidelines
- **Progressive Autonomy**: Tracks metrics and recommends autonomy adjustments
- **100% Backward Compatible**: Zero overhead when disabled

Use cases:
- Critical decision tasks requiring human approval
- Tasks with domain-specific constraints
- Continuous learning from human feedback
- Compliance and audit requirements

See [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) for complete documentation.

### QA Automation System

**NEW**: Multi-agent powered QA orchestration:

- **User Story Analysis**: Automatic generation from system understanding
- **6 Test Types**: E2E, API, Visual Regression, Performance, Security, Accessibility
- **Test Creation Agents**: Automatic test code generation
- **Orchestration**: Phases: Analysis → Test Creation → Execution → Reporting
- **Progress Tracking**: Coverage matrix and automation status per feature
- **CI/CD Ready**: GitHub Actions integration included
- **Dashboard Integration**: Real-time QA metrics and reports

```bash
cd qa-automation
npm run qa:orchestrate -- --phase=analysis    # Generate user stories
npm run test:all                                # Run all test suites
npm run qa:serve-report                         # View Allure report
```

See [CLAUDE.md](./CLAUDE.md#qa-automation-system) for setup and usage.

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

### Try Integrated Execution

Run the example to see both standard and adversarial execution:

```bash
# Run integrated execution example
python examples/integrated_execution.py

# Or try adversarial team standalone
python examples/adversarial_example.py
```

**Example output:**
```
🔹 SIMPLE TASK → Standard Execution (5s)
🔸 COMPLEX TASK → Adversarial Team (60s)
   • 21 agents collaborate
   • Quality Score: 8.5/10
   • All pairs approved
```

**Documentation:**
- [Integration Architecture](./INTEGRATION_ARCHITECTURE.md) - Full technical details
- [Integration Usage](./INTEGRATION_USAGE.md) - How to use the integrated system
- [Team Roster](./TEAM_ROSTER.md) - All 21 agents

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

### MAGIC Human-AI Collaboration (Optional)

- `configure_magic` - Configure MAGIC for a task (autonomy, checkpoints, thresholds)
- `list_pending_escalations` - View escalations awaiting human response
- `respond_to_escalation` - Provide human approval/guidance
- `submit_feedback` - Submit feedback for system learning
- `get_confidence_scores` - View confidence assessment by stage
- `get_magic_session` - View collaborative session state
- `get_evolution_metrics` - View autonomy progression and recommendations

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
| `MAGIC_ENABLED` | Enable human-AI collaboration | `false` |
| `MAGIC_DEFAULT_AUTONOMY` | Default autonomy level | `collaborative` |
| `MAGIC_DEFAULT_CONFIDENCE_THRESHOLD` | Escalation threshold (0-1) | `0.6` |
| `MAGIC_DEFAULT_ESCALATION_TIMEOUT` | Human response timeout (seconds) | `300` |
| `MAGIC_WEBHOOK_URL` | Notification webhook | - |

See `.env.example` for all options and `CLAUDE.md` for detailed configuration guide.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=xteam_agents

# Test MAGIC system (includes backward compatibility)
pytest tests/unit/test_magic.py -v

# Type checking
mypy src/xteam_agents

# Linting
ruff check src/

# QA Automation tests
cd qa-automation
npm install
npm run test:all
npm run qa:serve-report
```

For detailed development instructions, see [CLAUDE.md](./CLAUDE.md).

## Production Deployment

For production deployment with Traefik reverse proxy and automatic SSL certificates, see [DEPLOYMENT.md](DEPLOYMENT.md).

Quick start for production:
```bash
# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run setup script
sudo ./scripts/setup-traefik.sh
```

Services will be available at:
- https://example.com (MCP Server)
- https://traefik.example.com (Traefik Dashboard)
- https://qdrant.example.com (Vector DB)
- https://neo4j.example.com (Graph DB)
- https://n8n.example.com (Workflows)

See [TRAEFIK.md](TRAEFIK.md) for detailed Traefik configuration.

## License

MIT
