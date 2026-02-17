"""Dynamic LangGraph builder from declarative PipelineSpec.

Constructs LangGraph StateGraph instances at runtime from YAML-defined
pipeline specifications. Enables dynamic topology without code changes.
"""

from __future__ import annotations

from typing import Any, Callable

import structlog
from langgraph.graph import END, StateGraph

from xteam_agents.models.state import AgentState
from xteam_agents.platform.conditions import ConditionRegistry
from xteam_agents.platform.errors import AgentSpecNotFoundError, ConditionNotFoundError
from xteam_agents.platform.registry import AgentRegistry
from xteam_agents.platform.spec import PipelineSpec

logger = structlog.get_logger()

# State schema name -> class mapping
STATE_SCHEMAS: dict[str, type] = {
    "AgentState": AgentState,
}


def register_state_schema(name: str, schema_class: type) -> None:
    """Register a state schema for use in pipeline specs."""
    STATE_SCHEMAS[name] = schema_class


class DynamicGraphBuilder:
    """Builds LangGraph from PipelineSpec at runtime."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        condition_registry: ConditionRegistry,
        node_factory: Callable[[str, dict], Callable] | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.condition_registry = condition_registry
        self._node_factory = node_factory

    def set_node_factory(self, factory: Callable[[str, dict], Callable]) -> None:
        """Set the factory that creates node functions from agent specs."""
        self._node_factory = factory

    def build(self, spec: PipelineSpec) -> Any:
        """Build and compile a LangGraph from pipeline spec."""
        logger.info("building_graph_from_spec", pipeline_id=spec.id, nodes=len(spec.nodes))

        state_class = STATE_SCHEMAS.get(spec.state_schema, AgentState)
        graph = StateGraph(state_class)

        # Add nodes
        for node_spec in spec.nodes:
            if not node_spec.agent_id.startswith("__system__."):
                if not self.agent_registry.has(node_spec.agent_id):
                    raise AgentSpecNotFoundError(node_spec.agent_id)

            if self._node_factory:
                node_fn = self._node_factory(node_spec.agent_id, node_spec.config_overrides)
            else:
                node_fn = self._create_passthrough_node(node_spec.node_name)

            graph.add_node(node_spec.node_name, node_fn)

        graph.set_entry_point(spec.entry_point)

        # Direct edges
        for edge in spec.edges:
            if edge.target == "__end__":
                graph.add_edge(edge.source, END)
            else:
                graph.add_edge(edge.source, edge.target)

        # Conditional edges
        for cedge in spec.conditional_edges:
            if not self.condition_registry.has(cedge.condition):
                raise ConditionNotFoundError(cedge.condition)

            predicate = self.condition_registry.get(cedge.condition)
            resolved_routes = {}
            for key, target in cedge.routes.items():
                resolved_routes[key] = END if target == "__end__" else target

            graph.add_conditional_edges(cedge.source, predicate, resolved_routes)

        logger.info("graph_built_from_spec", pipeline_id=spec.id)
        return graph.compile()

    def _create_passthrough_node(self, node_name: str) -> Callable:
        async def passthrough(state: Any) -> dict:
            logger.debug("passthrough_node", node=node_name)
            return {"current_node": node_name}

        return passthrough
