# 🔗 Using the Integrated System

## Overview

The XTeam Agents system now integrates two powerful components:

1. **Cognitive OS** - Fast, structured workflow with validated knowledge pipeline
2. **Adversarial Agent Team** - High-quality output through 21 AI agents working together

The system **automatically routes** tasks to the best execution mode based on complexity.

---

## Quick Start

### 1. Run the Example

```bash
# Make sure services are running
docker-compose up -d

# Run integrated execution example
python examples/integrated_execution.py
```

This example demonstrates both execution modes side-by-side.

### 2. Use via MCP Server

```bash
# Start MCP server
python -m xteam_agents

# Submit tasks via Claude Desktop or API
# The system will automatically route based on complexity
```

---

## How It Works

### Automatic Routing

```
┌─────────────────────────────────────────┐
│         Task Analysis Phase             │
│                                         │
│  LLM analyzes task complexity:         │
│  • simple: Typo fixes, logging         │
│  • medium: API endpoints, tests        │
│  • complex: Architecture, refactoring  │
│  • critical: Security, migrations      │
└────────────┬────────────────────────────┘
             ↓
     ┌───────┴────────┐
     │                │
  simple/          complex/
  medium           critical
     │                │
     ↓                ↓
┌─────────┐    ┌──────────────┐
│Standard │    │ Adversarial  │
│   LLM   │    │  Agent Team  │
│         │    │  (21 agents) │
└─────────┘    └──────────────┘
```

### Execution Modes

#### Standard Mode (Simple/Medium Tasks)

**When:**
- Typo fixes
- Adding logging
- Simple refactoring
- Writing tests
- Documentation updates

**How:**
- Single LLM call
- Fast (seconds)
- Suitable for straightforward tasks

**Example:**
```python
from xteam_agents.models.state import AgentState

task = AgentState(
    task_id=uuid.uuid4(),
    description="Fix typo: 'recieve' → 'receive'",
    priority=1,
)

result = await graph.ainvoke(task)
# Automatically uses standard execution
```

#### Adversarial Mode (Complex/Critical Tasks)

**When:**
- System architecture decisions
- Security implementations
- Performance optimizations
- Database migrations
- Multi-component refactoring

**How:**
- 21 AI agents collaborate
- Agent-Critic pairs iterate
- 5D quality scoring
- Orchestrator resolves conflicts
- Slower but higher quality

**Example:**
```python
task = AgentState(
    task_id=uuid.uuid4(),
    description=(
        "Design secure authentication system with JWT, "
        "bcrypt, RBAC, and rate limiting"
    ),
    priority=5,
)

result = await graph.ainvoke(task)
# Automatically uses adversarial execution
```

---

## Agent-Critic Pairs

When adversarial mode is used, specialized pairs work together:

### 1. TechLead Pair
- **Agent**: Chooses tech stack, defines approach
- **Critic**: Challenges technical decisions

### 2. Architect Pair
- **Agent**: Designs system architecture
- **Critic**: Stress-tests for scalability, finds bottlenecks

### 3. Backend Pair
- **Agent**: Implements API and business logic
- **Critic**: Reviews code quality, finds issues

### 4. Frontend Pair
- **Agent**: Designs UI components
- **Critic**: Validates UX and accessibility (WCAG 2.1)

### 5. Data Pair
- **Agent**: Designs database schemas
- **Critic**: Validates normalization, performance

### 6. DevOps Pair
- **Agent**: Plans CI/CD, infrastructure
- **Critic**: Tests resilience, disaster recovery

### 7. QA Pair (Perfectionist)
- **Agent**: Designs test strategy
- **Critic**: Hunts for coverage gaps, edge cases

### 8. AIArchitect Pair
- **Agent**: Designs ML pipelines
- **Critic**: Validates model selection, MLOps

### 9. Security Pair (Blue/Red Team)
- **Agent**: Implements security measures
- **Critic**: Attacks to find vulnerabilities (OWASP Top 10)

### 10. Performance Pair (Adversarial)
- **Agent**: Optimizes performance
- **Critic**: Stress-tests claims, finds bottlenecks

---

## Quality Scoring

Each critic evaluates on **5 dimensions** (0-10 scale):

1. **Correctness** - Technically correct?
2. **Completeness** - All requirements addressed?
3. **Quality** - Code/design quality acceptable?
4. **Performance** - Performance considerations met?
5. **Security** - Security requirements satisfied?

**Average score** determines approval:
- ≥8.0: Approved
- 7.0-7.9: Request revision
- <7.0: Rejected

---

## Iterative Refinement

```
Agent proposes solution
    ↓
Critic evaluates (5D scoring)
    ↓
Score ≥ threshold?
    ├─ YES → Approved
    └─ NO  → Iterate (up to 5 rounds)
              ↓
         Still not approved?
              ↓
         Escalate to Orchestrator
              ↓
         Orchestrator makes binding decision
```

---

## Memory Integration

All agents (cognitive + adversarial) share the **same MemoryManager**:

### Memory Flow

```
1. Agent/Critic work → Episodic Memory (private, draft)
2. If approved → Mark for validation
3. Cognitive OS validate node → Validates all
4. Cognitive OS commit node → Shared Memory
                              (Semantic + Procedural)
```

### Memory Invariants

- ✅ Agents write to **Episodic** (private) only
- ✅ Only **commit_node** writes to **Shared** memory
- ✅ All nodes can **read** from any memory
- ✅ Complete **audit trail** for all operations

---

## Configuration

### Complexity Thresholds

The system uses LLM to classify complexity. You can influence this by:

**Task Priority:**
```python
task = AgentState(
    description="Your task",
    priority=5,  # Higher priority → more likely complex classification
)
```

**Task Description:**
```python
# This will likely be classified as complex:
description = (
    "Design and implement secure authentication with "
    "multiple components, security review required"
)

# This will likely be classified as simple:
description = "Fix typo in README.md line 42"
```

### Agent Configuration

Edit `src/xteam_agents/agents/adversarial_config.py`:

```python
AGENT_CONFIGS = {
    AgentRole.TECH_LEAD: AgentConfig(
        role=AgentRole.TECH_LEAD,
        model="gpt-4",              # Change model
        temperature=0.7,            # Adjust creativity
        max_tokens=2000,            # Output length
    ),
    # ... other agents
}
```

### Pair Thresholds

```python
AGENT_PAIRS = {
    AgentPairType.TECH_LEAD: PairConfig(
        approval_threshold=7.5,     # Quality threshold
        max_iterations=5,           # Max refinement rounds
        escalation_enabled=True,    # Allow escalation
    ),
    # ... other pairs
}
```

---

## Monitoring

### Task Execution

```python
result = await graph.ainvoke(task)

# Check execution mode used
complexity = result.context.get("complexity")
print(f"Complexity: {complexity}")

# Check adversarial metadata (if used)
adv_metadata = result.context.get("adversarial_execution", {})
if adv_metadata:
    print(f"Quality Score: {adv_metadata['quality_score']}/10")
    print(f"Pairs Used: {adv_metadata['total_pairs']}")
    print(f"Approved: {adv_metadata['approved_pairs']}")
```

### Audit Trail

All actions are logged:

```python
# Query audit log
audit_log = await memory_manager.get_audit_log(task_id)

for entry in audit_log:
    print(f"{entry.timestamp}: {entry.event_type} - {entry.description}")
```

---

## Examples

### Example 1: Simple Task

```python
import asyncio
import uuid
from xteam_agents.graph.builder import build_cognitive_graph
from xteam_agents.models.state import AgentState
from xteam_agents.config import Settings
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.action.executor import ActionExecutor

async def run_simple_task():
    settings = Settings()
    llm_provider = LLMProvider(settings)
    memory_manager = MemoryManager(settings)
    action_executor = ActionExecutor(settings)

    await memory_manager.connect()

    graph = build_cognitive_graph(
        settings, llm_provider, memory_manager, action_executor
    )

    task = AgentState(
        task_id=uuid.uuid4(),
        description="Add console.log statement to debug function",
    )

    result = await graph.ainvoke(task)
    print(f"Result: {result.execution_result}")

    await memory_manager.disconnect()

asyncio.run(run_simple_task())
```

### Example 2: Complex Task

```python
async def run_complex_task():
    # ... same setup ...

    task = AgentState(
        task_id=uuid.uuid4(),
        description=(
            "Implement microservices architecture with: "
            "API Gateway, Auth Service, User Service, "
            "Event Bus, Service Discovery, "
            "with complete monitoring and CI/CD"
        ),
        priority=5,
    )

    result = await graph.ainvoke(task)

    # Show adversarial execution details
    adv_meta = result.context.get("adversarial_execution", {})
    print(f"Quality Score: {adv_meta.get('quality_score')}/10")
    print(f"Pairs Executed: {adv_meta.get('total_pairs')}")

asyncio.run(run_complex_task())
```

---

## Troubleshooting

### Task Always Uses Standard Execution

**Cause:** Complexity classifier defaults to "medium" on error or ambiguity.

**Solution:**
- Make task description more detailed
- Mention "architecture", "security", "multiple components"
- Increase priority to 4-5

### Adversarial Execution is Slow

**Expected:** Adversarial execution with 21 agents takes longer.

**Typical Times:**
- Simple (standard): 2-5 seconds
- Complex (adversarial): 30-120 seconds

**To Speed Up:**
- Reduce `max_iterations` in pair configs
- Use faster models (e.g., gpt-3.5-turbo) for some agents
- Enable parallel pair execution (future enhancement)

### Memory Not Shared

**Check:**
1. Both graphs created in `build_cognitive_graph()`
2. Same `memory_manager` instance passed to both
3. No multiple MemoryManager instances created

### Quality Scores Always Low

**Possible Causes:**
- Critic strategies too strict (Perfectionist, Adversarial)
- Approval thresholds too high
- Agent output format mismatches critic expectations

**Solution:**
- Adjust `approval_threshold` in `AGENT_PAIRS`
- Review critic prompts in `*_pair.py` files
- Check agent output format matches expected JSON

---

## Best Practices

### 1. Let the System Decide

Don't try to force complexity classification. Let the LLM analyze:

```python
# ✅ Good - descriptive, let system decide
description = "Refactor authentication module to use JWT with refresh tokens"

# ❌ Bad - too vague
description = "Fix auth"
```

### 2. Use Priority Appropriately

```python
priority=1  # Simple maintenance tasks
priority=2  # Regular development work
priority=3  # Important features
priority=4  # Critical features
priority=5  # Security, migrations, architecture
```

### 3. Monitor Quality Scores

Track quality scores over time to tune thresholds:

```python
if adv_meta:
    quality = adv_meta.get('quality_score')
    if quality < 7.0:
        logger.warning(f"Low quality score: {quality}")
```

### 4. Leverage Audit Trail

Use audit logs for debugging and optimization:

```python
# See which agents contributed
audit_log = await memory_manager.get_audit_log(task_id)
agent_names = {entry.agent_name for entry in audit_log}
print(f"Agents involved: {agent_names}")
```

---

## Advanced Usage

### Custom Complexity Classifier

Override the default classifier:

```python
# In graph/nodes/analyze.py
async def _classify_task_complexity(llm_provider, task, analysis):
    # Your custom logic
    if "security" in task.lower():
        return "critical"
    # ... etc
```

### Custom Agent Pairs

Add new pairs by creating `*_pair.py` in `agents/nodes/pairs/`:

```python
class MyAgent(BaseAgent):
    def __init__(self, settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.MY_AGENT)
        super().__init__(config, settings, memory_manager, llm)

    async def execute(self, state, feedback):
        # Your implementation
        pass

class MyCritic(BaseCritic):
    # Similar structure
    pass
```

Then register in `adversarial_graph.py`.

### Parallel Pair Execution

Future enhancement - pairs could run in parallel for faster execution:

```python
# Execute multiple pairs concurrently
results = await asyncio.gather(*[
    pair_registry.execute_pair(pair_type, state)
    for pair_type in selected_pairs
])
```

---

## Resources

- **Full Architecture**: [INTEGRATION_ARCHITECTURE.md](./INTEGRATION_ARCHITECTURE.md)
- **Agent Team Details**: [AGENTS_README.md](./AGENTS_README.md)
- **All 21 Agents**: [TEAM_ROSTER.md](./TEAM_ROSTER.md)
- **Working Example**: [examples/integrated_execution.py](./examples/integrated_execution.py)
- **Integration Tests**: [tests/integration/test_integrated_execution.py](./tests/integration/test_integrated_execution.py)

---

## Support

For issues or questions:
1. Check examples in `examples/`
2. Review architecture docs
3. Run integration tests to verify setup
4. Open issue on GitHub

**The integrated system is production-ready!** 🚀
