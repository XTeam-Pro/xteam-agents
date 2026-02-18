# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Setup (use venv — system Python is externally-managed)
python3 -m venv .venv
.venv/bin/pip install -e "../studyninja-magic-sdk"   # local dependency
.venv/bin/pip install -e ".[dev]"

# Run all unit tests
.venv/bin/pytest tests/unit/

# Run specific test file / test class / test
.venv/bin/pytest tests/unit/test_platform_spec.py -v
.venv/bin/pytest tests/unit/test_magic.py::TestConfidenceScore -v
.venv/bin/pytest tests/unit/test_models.py::TestAgentState::test_create_minimal

# Run with coverage
.venv/bin/pytest --cov=xteam_agents tests/unit/

# Lint
.venv/bin/ruff check src/
.venv/bin/ruff check src/ --fix

# Type check
.venv/bin/mypy src/xteam_agents

# Run the system
.venv/bin/python -m xteam_agents          # MCP STDIO mode (for Claude Desktop)
.venv/bin/python -m xteam_agents --http   # HTTP dev server
```

**Note**: `tests/unit/test_research_team.py` has a pre-existing import error (`ResearchPhase`). Exclude it with `--ignore=tests/unit/test_research_team.py` when running the full suite.

## Architecture Overview

### Core Pipeline: Validated Knowledge Flow

The system is a **cognitive operating system** where **only validated content reaches shared memory**:

```
START → analyze → plan → execute → validate → route_after_validation
                   ↑                              │
                   └───── (replan, max 3) ────────┘
                                                   │ (commit)
                                                   ↓
                                                commit → END
```

**Critical Invariant**: Only `commit_node` writes to shared memory (Qdrant/Neo4j). It's a pure system function, not an LLM agent.

### Three Execution Systems

| System | When Used | Agents | Entry Points |
|--------|----------|--------|-------------|
| **Cognitive OS** | All tasks | 5 nodes (analyze→commit) | `graph/builder.py` → `build_cognitive_graph()` |
| **Adversarial Team** | complex/critical tasks | 1 orchestrator + 10 agent-critic pairs | `agents/adversarial_graph.py` → `AdversarialGraphBuilder` |
| **Research Team** | Research tasks | 14+ specialists | `agents/research_team/research_graph.py` |

`UnifiedExecutor` in `integration/executor.py` routes by complexity: simple/medium → single LLM, complex/critical → Adversarial Team.

### Recursive Multi-Agent Platform (NEW)

The `platform/` module provides declarative agent infrastructure replacing hardcoded Python classes:

```
platform/
├── spec.py              # AgentSpec, CriticSpec, PipelineSpec, TeamSpec (Pydantic models)
├── registry.py          # AgentRegistry — find by capability/role/tags
├── loader.py            # SpecLoader — loads YAML specs from specs/ directory
├── budget.py            # ResourceBudget — token/time/depth limits, allocate_child()
├── context.py           # ExecutionContext, PipelineResult — hierarchical tracking
├── conditions.py        # ConditionRegistry — named predicates for conditional edges
├── graph_builder.py     # DynamicGraphBuilder — builds LangGraph from PipelineSpec
├── runtime.py           # AgentRuntime — execute_pipeline(), spawn_sub_pipeline()
├── composer.py          # TeamComposer — dynamic team assembly by capability matching
├── matcher.py           # CapabilityMatcher — scoring by capabilities/tags/keywords
├── meta_agent.py        # MetaAgent — execution metrics, optimization suggestions
├── topology_optimizer.py # TopologyOptimizer — applies MetaAgent suggestions
└── errors.py            # BudgetExhaustedError, MaxDepthExceededError, etc.
```

**YAML Specs** in `specs/` (29 agents, 3 pipelines, 2 teams):
```
specs/
├── agents/cognitive/    # analyst, architect, worker, reviewer, committer, reflector
├── agents/adversarial/  # orchestrator, tech_lead, architect, backend, frontend, data, devops, qa, ai_architect, security, performance
├── agents/research/     # chief_scientist, data_scientist, ml_researcher, cognitive_scientist, + 8 more
├── pipelines/           # cognitive_os.yml, adversarial_team.yml, research_team.yml
└── teams/               # adversarial_default.yml, research_default.yml
```

**Key concepts**:
- `AgentSpec` defines identity, LLM config, capabilities, tags, memory permissions, and optional inline critic
- `PipelineSpec` defines LangGraph topology declaratively (nodes → agents, edges, conditional edges with named conditions)
- `ResourceBudget` enables recursive execution: `allocate_child(fraction)` creates child budgets
- `AgentRuntime.spawn_sub_pipeline()` lets agents create child pipelines (max depth enforced)
- Registries loaded from YAML at `orchestrator.setup()` via `SpecLoader`
- `BaseAgent.from_spec()` and `BaseCritic.from_spec()` bridge specs to existing class hierarchy

### Memory Backends

| Backend | Type | Scope | Who Writes |
|---------|------|-------|------------|
| Redis | Episodic (short-term) | Private per task | Any node |
| Qdrant | Semantic (validated knowledge) | Shared | **commit_node ONLY** |
| Neo4j | Procedural (relationships) | Shared | **commit_node ONLY** |
| PostgreSQL | Audit log (append-only) | Shared | Any node |

### MAGIC System (Human-AI Collaboration)

Optional overlay enabled via `MAGIC_ENABLED=true`. 5 autonomy levels (SUPERVISED→TRUSTED), confidence scoring (5 dimensions), human checkpoints at 4 stages, feedback learning. Zero overhead when disabled.

Key files: `magic/core.py`, `magic/metacognition.py`, `magic/escalation.py`, `magic/session.py`, `magic/feedback.py`, `magic/evolution.py`.

### MCP Server

Entry point: `server/app.py`. Uses FastMCP. Tool categories:
- **Task**: submit_task, get_task_status, cancel_task, list_tasks
- **Memory**: query_memory, search_knowledge, get_knowledge_graph
- **Admin**: system_health, register_capability, list_agents
- **MAGIC**: configure_magic, respond_to_escalation, submit_feedback, etc.

Transport: STDIO (default, for Claude Desktop) or HTTP (`--http`).

## Source Layout

```
src/xteam_agents/
├── config.py              # Pydantic Settings (env vars)
├── orchestrator.py        # TaskOrchestrator — task lifecycle, registry init
├── graph/
│   ├── builder.py         # build_cognitive_graph() — static LangGraph
│   ├── edges.py           # route_after_validation, replan conditions
│   ├── nodes/             # analyze.py, plan.py, execute.py, validate.py, commit.py, human_checkpoint.py
│   └── prompts.py         # System prompts for cognitive agents
├── agents/
│   ├── base.py            # BaseAgent, BaseCritic (ABCs with from_spec())
│   ├── adversarial_config.py  # AGENT_CONFIGS, AGENT_PAIRS (hardcoded, being migrated to YAML)
│   ├── adversarial_graph.py   # AdversarialGraphBuilder
│   ├── adversarial_state.py   # AdversarialAgentState
│   ├── nodes/pairs/       # 10 agent-critic pair implementations
│   └── research_team/     # 14+ research agents, research_graph.py, research_state.py
├── platform/              # Recursive multi-agent platform (NEW)
├── specs/                 # YAML agent/pipeline/team definitions (NEW)
├── integration/           # executor.py (UnifiedExecutor), state_adapter.py
├── memory/                # manager.py, backends/ (redis, qdrant, neo4j, postgres)
├── magic/                 # MAGIC human-AI collaboration
├── action/                # executor.py, registry.py, handlers/
├── llm/                   # provider.py, tools.py
├── perception/            # engine.py (web search, HTML parsing)
├── models/                # state.py (AgentState), task.py, action.py, memory.py, audit.py, magic.py, observation.py
└── server/                # app.py, tools/ (task_tools, memory_tools, admin_tools, magic_tools)
```

## Configuration

All via environment variables (Pydantic Settings in `config.py`). Key groups:

- **LLM**: `LLM_PROVIDER` (openai/anthropic), `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `LLM_MODEL`
- **Memory**: `REDIS_URL`, `QDRANT_URL`, `NEO4J_URL`/`NEO4J_USER`/`NEO4J_PASSWORD`, `POSTGRES_URL`
- **Task**: `TASK_TIMEOUT_SECONDS`, `MAX_RETRIES`, `MAX_REPLAN_ITERATIONS`
- **Platform**: `SPECS_DIR` (custom YAML specs path, default: builtin)
- **MAGIC**: `MAGIC_ENABLED`, `MAGIC_DEFAULT_AUTONOMY`, `MAGIC_DEFAULT_CONFIDENCE_THRESHOLD`

## How to Add a New Agent (Declarative)

1. Create a YAML file in `specs/agents/<category>/your_agent.yml`:
```yaml
id: "category.your_agent"
name: "YourAgent"
role: "your_role"
persona: "System prompt describing the agent's behavior..."
capabilities: ["capability1", "capability2"]
tags: ["category", "domain"]
model: "claude-sonnet-4-5"
temperature: 0.5
max_tokens: 4096
can_spawn: false
```

2. The agent is automatically loaded by `SpecLoader` at startup and available via `AgentRegistry.get("category.your_agent")`.

3. To include in a pipeline, add a `NodeSpec` referencing the agent_id in the pipeline YAML.

## Key Patterns

- **State Schema**: `AgentState` (Pydantic) with custom reducers `merge_messages`, `merge_artifacts` for LangGraph
- **Node Factory**: Functions in `graph/nodes/` return async closures `(state: AgentState) -> dict`
- **Capability Registry**: Actions must be registered before execution (security boundary)
- **Replan Loop Protection**: Max 3 iterations, then routes to fail_handler
- **Agent-Critic Pairs**: Iterative refinement with 5D scoring (correctness, completeness, quality, performance, security)
- **Backward Compatibility**: Platform specs coexist with hardcoded agents. `from_spec()` bridges the two systems
