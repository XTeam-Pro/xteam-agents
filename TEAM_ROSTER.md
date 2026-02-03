# 🎭 Adversarial Agent Team Roster

## Complete Team Structure: 21 Agents

---

## 🎯 SUPREME COORDINATOR

### OrchestratorAgent
```
Role: Master coordinator and final authority
Model: claude-opus-4-5 (temp 0.3)
Authority: SUPREME - All conflicts resolved here
Can escalate: NO (highest level)
```

**Responsibilities**:
- Task classification
- Pair selection
- Conflict resolution
- Final decision & commit authority

---

## 👥 AGENT PAIRS (10 Pairs = 20 Agents)

### Pair 1: 🧠 Technical Leadership

| Agent | Critic |
|-------|--------|
| **TechLeadAgent** | **TechLeadCritic** |
| Technical decisions | Challenges decisions |
| Model: opus (0.3) | Model: opus (0.7) |
| Strategy: Precise | Strategy: Constructive |
| Threshold: 8.0 | Max iter: 3 |

---

### Pair 2: 🏗 System Architecture

| Agent | Critic |
|-------|--------|
| **ArchitectAgent** | **ArchitectCritic** |
| Designs architecture | Stress-tests design |
| Model: sonnet (0.5) | Model: sonnet (0.8) |
| Strategy: Balanced | Strategy: Constructive |
| Threshold: 8.0 | Max iter: 3 |

---

### Pair 3: ⚙ Backend Development

| Agent | Critic |
|-------|--------|
| **BackendAgent** | **BackendCritic** |
| Implements logic | Code review |
| Model: sonnet (0.2) | Model: sonnet (0.6) |
| Strategy: Precise | Strategy: Constructive |
| Threshold: 7.0 | Max iter: 3 |

---

### Pair 4: 🎨 Frontend Development

| Agent | Critic |
|-------|--------|
| **FrontendAgent** | **FrontendCritic** |
| Builds UI | UX validation |
| Model: sonnet (0.4) | Model: sonnet (0.7) |
| Strategy: Creative | Strategy: Constructive |
| Threshold: 7.0 | Max iter: 3 |

---

### Pair 5: 🗄 Data Engineering

| Agent | Critic |
|-------|--------|
| **DataAgent** | **DataCritic** |
| Designs schemas | Data integrity |
| Model: sonnet (0.2) | Model: sonnet (0.6) |
| Strategy: Precise | Strategy: Constructive |
| Threshold: 7.5 | Max iter: 3 |

---

### Pair 6: 🚀 DevOps & Infrastructure

| Agent | Critic |
|-------|--------|
| **DevOpsAgent** | **DevOpsCritic** |
| Infrastructure | Resilience testing |
| Model: sonnet (0.3) | Model: sonnet (0.7) |
| Strategy: Reliable | Strategy: Constructive |
| Threshold: 7.5 | Max iter: 3 |

---

### Pair 7: 🧪 Quality Assurance

| Agent | Critic |
|-------|--------|
| **QAAgent** | **QACritic** |
| Tests & validates | Edge case hunter |
| Model: sonnet (0.1) | Model: sonnet (0.8) |
| Strategy: Thorough | Strategy: **Perfectionist** |
| Threshold: 8.0 | Max iter: 3 |

---

### Pair 8: 🤖 AI Architecture

| Agent | Critic |
|-------|--------|
| **AIAgentArchitect** | **AIArchitectCritic** |
| AI systems design | AI safety validation |
| Model: opus (0.5) | Model: opus (0.7) |
| Strategy: Innovative | Strategy: Constructive |
| Threshold: 8.0 | Max iter: 3 |

---

### Pair 9: 🔐 Security (Red Team vs Blue Team)

| Agent (Blue Team) | Critic (Red Team) |
|-------------------|-------------------|
| **SecurityAgent** | **SecurityCritic** |
| Defensive security | Offensive attacks |
| Model: opus (0.1) | Model: opus (**0.9**) |
| Strategy: Protective | Strategy: **Adversarial** |
| Threshold: **9.0** | Max iter: **5** |
| Min score: **7.0** | Most creative |

⚠️ **Special**: Highest standards, most iterations, adversarial approach

---

### Pair 10: ⚡ Performance Engineering

| Agent | Critic |
|-------|--------|
| **PerformanceAgent** | **PerformanceCritic** |
| Optimizes performance | Stress testing |
| Model: sonnet (0.3) | Model: sonnet (0.7) |
| Strategy: Methodical | Strategy: **Perfectionist** |
| Threshold: 7.5 | Max iter: 3 |

---

## 📊 Agent Statistics

### Total Count
- **21 Total Agents**
- **1 Orchestrator**
- **10 Action Agents**
- **10 Critic Agents**

### Model Distribution
- **5 Opus agents** (high-stakes decisions)
- **16 Sonnet agents** (standard work)

### Temperature Range
- **Lowest**: 0.1 (QA, Security)
- **Highest**: 0.9 (SecurityCritic)
- **Average**: 0.5

### Approval Thresholds
- **Highest**: 9.0 (Security)
- **Standard**: 7.0-8.0
- **Strictest pair**: Security (9.0 avg, 7.0 min)

---

## 🎭 Critic Strategies Summary

### Constructive (7 pairs)
- TechLead, Architect, Backend, Frontend, Data, DevOps, AI Architect
- **Goal**: Collaborative improvement
- **Approach**: Find issues, suggest fixes

### Adversarial (1 pair)
- Security (Red Team)
- **Goal**: Break the system
- **Approach**: Attacker mindset

### Perfectionist (2 pairs)
- QA, Performance
- **Goal**: Excellence at all costs
- **Approach**: Never satisfied

---

## 🔄 Typical Execution Flow

```
User Request
    ↓
🎯 OrchestratorAgent
    ├─ Classifies task
    ├─ Selects pairs
    └─ Defines criteria
        ↓
    ┌───────────────────────────────┐
    │ PHASE 1: Planning             │
    │ 🧠 TechLead ↔ TechLeadCritic │
    │ 🏗 Architect ↔ ArchitectCritic│
    └───────────────────────────────┘
        ↓
    ┌───────────────────────────────┐
    │ PHASE 2: Security & Perf      │
    │ 🔐 Security ↔ SecurityCritic  │
    │ ⚡ Performance ↔ PerfCritic    │
    └───────────────────────────────┘
        ↓
    ┌───────────────────────────────┐
    │ PHASE 3: Implementation       │
    │ 🗄 Data ↔ DataCritic         │
    │ ⚙ Backend ↔ BackendCritic    │
    │ 🎨 Frontend ↔ FrontendCritic │
    │ 🚀 DevOps ↔ DevOpsCritic     │
    └───────────────────────────────┘
        ↓
    ┌───────────────────────────────┐
    │ PHASE 4: Quality              │
    │ 🧪 QA ↔ QACritic              │
    └───────────────────────────────┘
        ↓
🎯 OrchestratorAgent
    ├─ Reviews all pairs
    ├─ Resolves conflicts
    └─ Final decision → COMMIT
```

---

## 🎖 Agent Specializations

### Enterprise-Grade Agents (Opus Model)
1. **OrchestratorAgent** - Supreme authority
2. **TechLeadAgent** - Technical leadership
3. **TechLeadCritic** - Challenge tech decisions
4. **AIAgentArchitect** - AI system design
5. **AIArchitectCritic** - AI safety
6. **SecurityAgent** - Blue team defense
7. **SecurityCritic** - Red team offense

### Production Agents (Sonnet Model)
8. **ArchitectAgent** - System architecture
9. **ArchitectCritic** - Architecture validation
10. **BackendAgent** - Business logic
11. **BackendCritic** - Code review
12. **FrontendAgent** - UI/UX
13. **FrontendCritic** - UX validation
14. **DataAgent** - Data architecture
15. **DataCritic** - Data integrity
16. **DevOpsAgent** - Infrastructure
17. **DevOpsCritic** - Resilience testing
18. **QAAgent** - Testing
19. **QACritic** - Edge cases
20. **PerformanceAgent** - Optimization
21. **PerformanceCritic** - Stress testing

---

## 📈 Success Metrics

### System-Wide KPIs
- **Overall Quality**: > 8.0/10
- **Approval Rate**: 60-80%
- **Avg Iterations**: 1.5-2.0
- **Escalation Rate**: < 10%

### Per-Pair Metrics
- **Iteration count**: Tracked
- **Approval scores**: 5-dimensional
- **Conflict rate**: Monitored
- **Resolution time**: Measured

---

## 🛡 Conflict Resolution Hierarchy

```
Level 1: Agent ↔ Critic (iterative, max 3-5 rounds)
    ↓ (if unresolved)
Level 2: Escalate to OrchestratorAgent
    ↓
Level 3: Orchestrator's BINDING decision
    ↓
NO FURTHER APPEALS (immutable)
```

---

## 🎯 Use Cases by Pair

| Pair | Primary Use Cases |
|------|-------------------|
| TechLead | Tech stack selection, major architectural decisions |
| Architect | System design, component boundaries, integrations |
| Backend | API implementation, business logic, integrations |
| Frontend | UI components, state management, UX |
| Data | Schema design, migrations, query optimization |
| DevOps | CI/CD, deployment, monitoring, infrastructure |
| QA | Testing strategy, test coverage, bug hunting |
| AIArchitect | LLM integration, agent systems, AI orchestration |
| Security | Auth, permissions, vulnerability assessment, compliance |
| Performance | Optimization, profiling, load testing, scaling |

---

## 📚 Quick Reference

### Start a Task
```python
state = AdversarialAgentState(
    task_id="task_001",
    original_request="Your task here"
)
```

### Get Pair Config
```python
from xteam_agents.agents import get_pair_config, AgentPairType

config = get_pair_config(AgentPairType.SECURITY)
# Returns: max_iterations=5, approval_threshold=9.0
```

### Check Critic
```python
from xteam_agents.agents import get_critic_for_agent, AgentRole

critic = get_critic_for_agent(AgentRole.BACKEND)
# Returns: AgentRole.BACKEND_CRITIC
```

---

## 🎓 Philosophy

> **"Every great solution comes from great opposition."**

The adversarial approach ensures:
- ✅ No blind spots
- ✅ Higher quality through challenge
- ✅ Natural error correction
- ✅ Continuous improvement
- ✅ Battle-tested solutions

---

**Total Team Strength**: 21 Agents working in adversarial harmony
**Status**: Ready for implementation
**Version**: 1.0
