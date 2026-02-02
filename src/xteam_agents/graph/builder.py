"""Build the cognitive LangGraph."""

from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from xteam_agents.action.executor import ActionExecutor
from xteam_agents.config import Settings
from xteam_agents.graph.edges import route_after_validation
from xteam_agents.graph.nodes.analyze import create_analyze_node
from xteam_agents.graph.nodes.commit import create_commit_node
from xteam_agents.graph.nodes.execute import create_execute_node
from xteam_agents.graph.nodes.plan import create_plan_node
from xteam_agents.graph.nodes.validate import create_validate_node
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


def build_cognitive_graph(
    settings: Settings,
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
    action_executor: ActionExecutor,
) -> StateGraph:
    """
    Build the cognitive LangGraph.

    Graph Flow:
    ```
    START → [analyze] → [plan] → [execute] → [validate] → route_after_validation
                           ↑                                    │
                           └──────── (replan) ─────────────────┘
                                                                │
                                                       (commit) ↓
                                                            [commit] → END
                                                                │
                                                        (fail)  ↓
                                                            [fail_handler] → END
    ```

    Memory Invariants:
    - analyze, plan, execute, validate: Can only write to episodic (private) memory
    - commit: ONLY node that writes to shared memory (semantic, procedural)
    - All nodes can read from any memory type

    Args:
        settings: Application settings
        llm_provider: LLM provider instance
        memory_manager: Memory manager instance
        action_executor: Action executor instance

    Returns:
        Compiled LangGraph
    """
    logger.info("building_cognitive_graph")

    # Create the state graph
    graph = StateGraph(AgentState)

    # Create node functions
    analyze_node = create_analyze_node(llm_provider, memory_manager)
    plan_node = create_plan_node(llm_provider, memory_manager)
    execute_node = create_execute_node(llm_provider, memory_manager, action_executor)
    validate_node = create_validate_node(llm_provider, memory_manager)
    commit_node = create_commit_node(memory_manager)

    # Add nodes to graph
    graph.add_node("analyze", analyze_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("validate", validate_node)
    graph.add_node("commit", commit_node)
    graph.add_node("fail_handler", _fail_handler_node(memory_manager))

    # Set entry point
    graph.set_entry_point("analyze")

    # Add edges
    # Linear flow: analyze → plan → execute → validate
    graph.add_edge("analyze", "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "validate")

    # Conditional routing after validation
    graph.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "commit": "commit",
            "plan": "plan",  # Replan loop
            "fail": "fail_handler",
        },
    )

    # Terminal edges
    graph.add_edge("commit", END)
    graph.add_edge("fail_handler", END)

    logger.info("cognitive_graph_built")

    return graph


def _fail_handler_node(memory_manager: MemoryManager):
    """Create a fail handler node."""
    from xteam_agents.models.audit import AuditEntry, AuditEventType

    async def fail_handler(state: AgentState) -> dict[str, Any]:
        """Handle task failure."""
        logger.warning(
            "fail_handler_enter",
            task_id=str(state.task_id),
            error=state.error,
        )

        # Log the failure
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.TASK_FAILED,
                node_name="fail_handler",
                description=f"Task failed: {state.error or 'Unknown error'}",
                data={
                    "iteration_count": state.iteration_count,
                    "validation_attempts": state.validation_attempts,
                },
            )
        )

        return {
            "current_node": "end",
            "is_failed": True,
        }

    return fail_handler


def compile_graph(graph: StateGraph):
    """
    Compile the graph for execution.

    Args:
        graph: The state graph to compile

    Returns:
        Compiled graph ready for invocation
    """
    return graph.compile()
