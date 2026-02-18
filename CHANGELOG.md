# Changelog — xteam-agents

All notable changes to xteam-agents are documented here.
Format: reverse chronological order.

---

## [1.0.0] — 2026-02-08 — Production Release

**Status**: PRODUCTION READY. Full integration of Cognitive OS, Adversarial Agent Team, and Research Team.

### Research Team Phase 2 (2026-02-08)

#### Methodologists Team (4 agents)
- `nodes/methodologists/lead_methodologist.py` (~250 lines)
- `nodes/methodologists/curriculum_designer.py` (~250 lines)
- `nodes/methodologists/assessment_designer.py` (~300 lines)
- `nodes/methodologists/adaptive_learning_specialist.py` (~350 lines)
- Competencies: Educational Standards (Common Core, NGSS), curriculum mapping, formative/summative assessment design, rubric development, ITS algorithms, personalization strategies

#### Content Team (5 agents)
- `nodes/content_team/content_architect.py` (~200 lines)
- `nodes/content_team/subject_matter_experts.py` — Math K-12 + Science NGSS SMEs
- `nodes/content_team/dataset_engineer.py` (~250 lines)
- `nodes/content_team/annotation_specialist.py` (~300 lines)
- Competencies: content taxonomy, metadata schemas, ETL pipelines, data versioning, annotation guidelines (IAA), quality control

#### Cognitive OS Integration
- `graph/nodes/execute_research.py` (~200 lines) — `execute_research_node()`, task classification, complexity estimation, research objectives extraction
- Automatic AgentState ↔ ResearchState conversion

#### Dashboard Improvements (2026-02-08)
- Streamlit monitoring UI: Adversarial Team metrics, quality scoring, 5 MAGIC tabs (Pending Escalations, Active Sessions, Confidence Dashboard, Feedback & Learning, Evolution Metrics)

### Adversarial Agent Team (2026-02-03)

#### Full Integration: Cognitive OS + Adversarial Team
- `integration/state_adapter.py` (350 lines) — state bridging
- `integration/executor.py` (250 lines) — UnifiedExecutor: routes simple/medium → single LLM, complex/critical → adversarial team
- `graph/nodes/analyze.py` — LLM-based complexity detection
- Integration tests (`tests/integration/test_integrated_execution.py`) — 400 lines, 8 tests

#### Adversarial Agent Team (21 agents, 10 agent-critic pairs)
- Orchestrator + TechLead, Architect, Backend, Frontend, Data, DevOps, QA, AI-Architect, Security, Performance
- LLM models: Claude Opus 4.6 (TechLead, AI-Arch, Security), Claude Sonnet 4.5 (others)
- 5D scoring: Correctness, Completeness, Quality, Performance, Security
- Iterative refinement until quality threshold met

#### Cognitive Operating System (LangGraph)
- 5-stage pipeline: `analyze → plan → execute → validate → commit → reflect`
- MAGIC checkpoints after analyze, plan, execute
- Standard path (~5s), complex path via UnifiedExecutor (~60–120s)

#### MAGIC Human-AI Collaboration
- 5 autonomy levels: SUPERVISED → GUIDED → COLLABORATIVE → AUTONOMOUS → TRUSTED
- Confidence scoring (5D: factual 30%, completeness 25%, relevance 20%, coherence 15%, novelty_risk 10%)
- Progressive autonomy: EvolutionEngine upgrades based on approval rate (>90% over 20+ tasks)

### Memory System (5 backends)
| Backend | Technology | Scope | Write Permission |
|---------|-----------|-------|-----------------|
| Episodic | Redis | Private | ANY node |
| Semantic | Qdrant | Shared | commit_node ONLY |
| Procedural | Neo4j | Shared | commit_node ONLY |
| Audit | PostgreSQL | Shared | ANY (append-only) |
| Task | PostgreSQL | Shared | Orchestrator only |

**Critical invariant**: ONLY `commit_node` writes to shared memory.

### MCP Server (21+ tools)
- Task management (5 tools), memory/knowledge (4), administration (5), MAGIC (7), code/filesystem, web search
- FastMCP 2.14 protocol

### Deployment (2026-02-03 → 2026-02-08)
- Traefik SSL configuration
- Environment: Docker Compose with `agents` profile
- Service: `xteam-agents` at port 8003, dashboard at 8501 (Streamlit)
- Fixes applied: validation loop problems, LLM provider initialization, memory backend connections

---

## [0.9.0] — 2026-01-XX — Initial Research Team

### Research Team Phase 1 (Scientists)
- Chief Scientist, Data Scientist, ML Researcher, Cognitive Scientist, Pedagogical Researcher
- `graph/nodes/research_team/` — initial pipeline structure
- `ResearchState`, `ResearchPipeline` (LangGraph)
- 3 research team types: Scientists, Methodologists, Content Team

### Declarative Platform
- YAML agent/pipeline/team specs: `platform/specs/agents/`, `pipelines/`, `teams/`
- `DynamicGraphBuilder` — creates LangGraph graphs from YAML at runtime
- `ResourceBudget` for token/depth limits
- `MetaAgent` for performance optimization
- 29 declarative agent specs, 3 pipelines

---

## [0.8.0] — 2026-01-XX — QA Automation & SSOT

### QA Automation
- Automated QA pipeline: test generation, execution, reporting
- Integration with StudyNinja-API test infrastructure

### SSOT (Single Source of Truth)
- MCP Server technical specification (`SSOT.md`)
- System role, tool contracts, memory invariants documented

---

*Note: Pre-0.8.0 history was not tracked in a changelog. The system was rebuilt from scratch in January 2026.*
