# Implement "Self-Evolution" via Automated Retrospectives

This plan introduces a meta-cognitive loop where the system analyzes its own performance (both successes and failures) to generate "Guidelines" that improve future task execution.

## 1. New Memory Concept: Guidelines
We will treat "Guidelines" as a specialized form of Semantic Memory with high retrieval priority.
- **Storage**: Semantic Memory (Qdrant)
- **Metadata**: `type="guideline"`, `trigger="failure" | "success"`
- **Content**: Concise rules like "Always verify Docker container status before connecting."

## 2. New Node: `Reflect` (Retrospective)
We will introduce a `reflect_node` that runs at the end of a task lifecycle.

### Logic
1.  **Input**: Final `AgentState` (completed or failed).
2.  **Analysis**: The LLM analyzes the `audit_log` and `execution_result`.
    - *If Failed*: Identify the root cause and propose a rule to prevent it.
    - *If Succeeded*: Identify what went particularly well or optimization opportunities.
3.  **Output**: A new `MemoryArtifact` (Guideline).
4.  **Commit**: The node uses `MemoryManager.commit_to_shared` to save the guideline.

## 3. Graph Modification
We will modify `build_cognitive_graph` in `src/xteam_agents/graph/builder.py`:
- **Current**: `commit` -> `END`, `fail_handler` -> `END`
- **New**: `commit` -> `reflect` -> `END`, `fail_handler` -> `reflect` -> `END`

## 4. Integration with Analyst/Architect
We will update `analyze_node` and `plan_node` to actively retrieve Guidelines.
- **Analyst**: When gathering context, specifically query for `type="guideline"` relevant to the current task description.
- **Architect**: Include relevant guidelines in the system prompt to ensure plans adhere to learned rules.

## Implementation Steps
1.  **Create `src/xteam_agents/graph/nodes/reflect.py`**: Implement the retrospective logic.
2.  **Update `src/xteam_agents/graph/builder.py`**: Wire the new node into the graph.
3.  **Update `src/xteam_agents/graph/nodes/analyze.py`**: Inject guidelines into the context.
4.  **Verify**: Run a task that fails, check if a guideline is created, run a similar task, check if the guideline is applied.
