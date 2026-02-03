```markdown
# Agent Team Usage Guide

## Quick Start

### 1. Submit a Task

```python
from xteam_agents.agents import AgentTeamState, classify_task

# Create initial state
task = "Add user authentication with JWT tokens"
state = AgentTeamState(
    task_id="task_001",
    original_request=task,
    task_categories=classify_task(task)
)

# Categories will be automatically classified:
# ['security', 'backend_logic', 'data_model']
```

### 2. Task Flows Through Agents

```
User Request
    ↓
TechLeadAgent (classifies, sets scope, constraints)
    ↓
[SecurityAgent] (security review - MUST approve)
    ↓
[ArchitectAgent] (if architecture changes needed)
    ↓
[DataAgent] (designs user/session tables)
    ↓
[BackendAgent] (implements JWT logic, API endpoints)
    ↓
[QAAgent] (tests authentication flows)
    ↓
TechLeadAgent (final approval)
    ↓
CommitNode (writes to shared memory)
```

## Agent Responsibilities

### 🧠 TechLeadAgent
**When**: ALWAYS first and last
**Does**:
- Classifies task categories
- Sets immutable scope & constraints
- Final approval gate
- Handles escalations

**Example Decision**:
```python
TechLeadDecision(
    task_id="task_001",
    decision_type=DecisionType.APPROVE,
    scope="Implement JWT authentication for API",
    constraints=[
        "Use bcrypt for password hashing",
        "Tokens expire in 1 hour",
        "No storing tokens in localStorage"
    ],
    risks=[
        "Token refresh mechanism needed",
        "Session management complexity"
    ],
    routing_decision=[
        AgentRole.SECURITY,
        AgentRole.DATA,
        AgentRole.BACKEND,
        AgentRole.QA
    ]
)
```

---

### 🏗 ArchitectAgent
**When**: Architecture changes, system boundaries, new components
**Does**:
- Defines component structure
- Identifies integration points
- Plans failure modes
- Creates architecture diagrams

**Triggers**: Keywords like "architecture", "system design", "boundaries"

---

### ⚙ BackendAgent
**When**: Business logic, APIs, integrations
**Does**:
- Implements API endpoints
- Business logic
- Third-party integrations
- Backend tests

**Triggers**: Keywords like "api", "backend", "business logic", "integration"

---

### 🎨 FrontendAgent
**When**: UI, UX, client-side logic
**Does**:
- React/Vue components
- State management
- UI tests
- Accessibility

**Triggers**: Keywords like "ui", "ux", "frontend", "interface"

---

### 🗄 DataAgent
**When**: Database schemas, migrations, queries
**Does**:
- Schema design
- Migrations
- Index optimization
- Query performance

**Triggers**: Keywords like "database", "schema", "migration", "sql"

---

### 🚀 DevOpsAgent
**When**: Deployment, CI/CD, infrastructure
**Does**:
- CI/CD pipelines
- Deployment strategies
- Monitoring setup
- Rollback plans

**Triggers**: Keywords like "deploy", "ci/cd", "infrastructure", "monitoring"

---

### 🧪 QAAgent
**When**: After execution agents complete
**Does**:
- Runs all tests
- Finds edge cases
- Validates correctness
- Reports bugs

**Always runs**: For any execution task

---

### 🤖 AIAgentArchitect
**When**: AI/LLM features, agent systems
**Does**:
- AI architecture design
- LLM orchestration
- Memory system design
- Tool configuration

**Triggers**: Keywords like "llm", "agent", "ai", "orchestration"

---

### 🔐 SecurityAgent
**When**: Auth, permissions, sensitive data
**Does**:
- Threat analysis
- Vulnerability scanning
- Access model design
- Compliance checks

**Triggers**: Keywords like "security", "auth", "permission", "sensitive"

---

### ⚡ PerformanceAgent
**When**: Performance requirements, optimization
**Does**:
- Bottleneck analysis
- Load testing
- Resource optimization
- Performance recommendations

**Triggers**: Keywords like "performance", "optimization", "latency", "scale"

---

## RACI Matrix Example

For a task like "Add user authentication":

| Domain | TechLead | Security | Data | Backend | QA |
|--------|----------|----------|------|---------|-----|
| Security Model | A | R | C | C | I |
| Database Schema | A | C | R | C | C |
| API Implementation | A | I | C | R | C |
| Testing | A | C | C | C | R |
| Final Approval | A/R | I | I | I | I |

**Legend**: A=Accountable, R=Responsible, C=Consulted, I=Informed

---

## Escalation Scenarios

### Scenario 1: Ambiguous Requirements
```python
# BackendAgent encounters unclear requirement
state.add_escalation(
    from_agent=AgentRole.BACKEND,
    reason=EscalationReason.AMBIGUOUS_REQUIREMENTS,
    context={"question": "Should passwords be case-sensitive?"},
    proposed_solution="Make passwords case-sensitive (industry standard)",
    urgency="normal"
)
# → Routes back to TechLeadAgent for clarification
```

### Scenario 2: Architecture Violation
```python
# BackendAgent wants to add new microservice
state.add_escalation(
    from_agent=AgentRole.BACKEND,
    reason=EscalationReason.ARCHITECTURE_VIOLATION,
    context={"proposed": "Create separate auth microservice"},
    proposed_solution="Discuss with ArchitectAgent",
    urgency="high"
)
# → TechLeadAgent reviews with ArchitectAgent
```

### Scenario 3: Security Risk
```python
# SecurityAgent finds critical issue
state.add_escalation(
    from_agent=AgentRole.SECURITY,
    reason=EscalationReason.SECURITY_RISK,
    context={"vulnerability": "Potential SQL injection"},
    proposed_solution="Use parameterized queries",
    urgency="critical"
)
# → Blocks all progress until resolved
```

---

## Immutable Context Rule

⚠️ **CRITICAL**: Once TechLeadAgent makes a decision, it's **IMMUTABLE**

```python
# ❌ WRONG - Agent cannot change scope
def backend_node(state):
    state.tech_lead_decision.scope = "Different scope"  # FORBIDDEN!

# ✅ CORRECT - Agent escalates for scope change
def backend_node(state):
    state.add_escalation(
        from_agent=AgentRole.BACKEND,
        reason=EscalationReason.AMBIGUOUS_REQUIREMENTS,
        context={"request": "Need to expand scope to include OAuth"},
        urgency="high"
    )
```

---

## Example Workflows

### Example 1: Simple Backend Task

**Task**: "Add GET /api/users/:id endpoint"

**Flow**:
```
1. TechLeadAgent
   - Categories: [backend_logic]
   - Agents: [BackendAgent, QAAgent]

2. BackendAgent
   - Implements endpoint
   - Adds tests

3. QAAgent
   - Validates tests pass
   - Checks edge cases

4. TechLeadAgent
   - Approves
   - Commits
```

**Time**: ~2 minutes

---

### Example 2: Complex Feature

**Task**: "Add real-time chat with WebSocket support"

**Flow**:
```
1. TechLeadAgent
   - Categories: [architecture, backend_logic, frontend_ui, infrastructure]
   - Agents: [ArchitectAgent, BackendAgent, FrontendAgent, DevOpsAgent, QAAgent]

2. ArchitectAgent
   - Designs WebSocket architecture
   - Plans message queuing
   - Identifies failure modes

3. BackendAgent
   - Implements WebSocket server
   - Message handlers
   - Room management

4. FrontendAgent
   - WebSocket client
   - React components
   - Real-time state updates

5. DevOpsAgent
   - Load balancer config
   - WebSocket proxy setup
   - Monitoring

6. QAAgent
   - Connection tests
   - Message delivery tests
   - Load tests

7. TechLeadAgent
   - Reviews all outputs
   - Approves
   - Commits
```

**Time**: ~15-20 minutes

---

### Example 3: Security-Critical Task

**Task**: "Implement password reset via email"

**Flow**:
```
1. TechLeadAgent
   - Categories: [security, backend_logic, data_model]
   - Agents: [SecurityAgent, DataAgent, BackendAgent, QAAgent]
   - Flags as security-critical

2. SecurityAgent (MUST approve before proceeding)
   - Token generation strategy
   - Token expiration (15 min recommended)
   - Rate limiting rules
   - Email validation
   → Clearance: APPROVED with conditions

3. DataAgent
   - password_reset_tokens table
   - Indexes on token + expiry

4. BackendAgent
   - /api/auth/reset-password endpoint
   - Email service integration
   - Token validation logic

5. QAAgent
   - Tests token expiration
   - Tests rate limiting
   - Tests email delivery

6. TechLeadAgent
   - Validates security conditions met
   - Approves
   - Commits
```

**Time**: ~10-15 minutes

---

## Configuration

### Agent Models (from config.py)

```python
AGENT_CONFIGS = {
    AgentRole.TECH_LEAD: AgentConfig(
        model="claude-opus-4-5",  # Strongest reasoning
        temperature=0.3,           # Conservative
    ),
    AgentRole.ARCHITECT: AgentConfig(
        model="claude-sonnet-4-5",
        temperature=0.5,
    ),
    AgentRole.SECURITY: AgentConfig(
        model="claude-opus-4-5",  # Critical decisions
        temperature=0.1,           # No risks
    ),
    # ... etc
}
```

### Task Classification

```python
from xteam_agents.agents import classify_task, get_required_agents

task = "Optimize database queries for user dashboard"
categories = classify_task(task)
# → [TaskCategory.DATA_MODEL, TaskCategory.PERFORMANCE]

agents = get_required_agents(categories)
# → {AgentRole.TECH_LEAD, AgentRole.DATA, AgentRole.PERFORMANCE, AgentRole.QA}
```

---

## Best Practices

### 1. Always Let TechLead Classify First
```python
# ❌ DON'T manually route
graph.add_edge(START, "backend")

# ✅ DO let TechLead classify
graph.add_edge(START, "tech_lead_classify")
```

### 2. Never Skip QA
```python
# ❌ DON'T skip QA
graph.add_edge("backend", "commit")

# ✅ DO include QA
graph.add_edge("backend", "qa")
graph.add_edge("qa", "tech_lead_approval")
```

### 3. Respect RACI Levels
```python
# Check if agent can execute
from xteam_agents.agents import can_agent_execute

if can_agent_execute("backend_logic", AgentRole.BACKEND):
    # Agent is R or A, can proceed
    pass
```

### 4. Escalate When Uncertain
```python
if condition_is_unclear:
    state.add_escalation(
        from_agent=current_agent,
        reason=EscalationReason.AMBIGUOUS_REQUIREMENTS,
        context={"question": "..."},
        urgency="normal"
    )
```

---

## Monitoring & Metrics

### Track Agent Performance

```python
# Agent completion times
state.messages  # Contains timestamps

# Escalation rate
escalation_rate = len(state.escalations) / len(state.completed_agents)

# QA pass rate
qa_pass_rate = state.qa_results.tests_passed / state.qa_results.tests_run

# Final approval rate
approval_rate = 1 if state.final_approval.approved else 0
```

---

## Troubleshooting

### Issue: Task Stuck in Loop
**Cause**: Iteration limit reached
**Solution**: Check state.has_exceeded_max_iterations()

### Issue: Escalation Not Handled
**Cause**: Routing not detecting escalations
**Solution**: Check route_on_escalation() is in conditional edges

### Issue: Agent Skipped
**Cause**: Routing rules not matching
**Solution**: Check task classification and routing rules

---

## Next Steps

1. Implement agent nodes (see `src/xteam_agents/agents/nodes/`)
2. Create LangGraph with routing
3. Add tools for each agent
4. Test with example tasks
5. Monitor and optimize

See `AGENTS_ARCHITECTURE.md` for full architecture details.
```