"""Registry for condition predicates used in conditional pipeline edges.

Maps condition names (strings in YAML specs) to Python functions
that evaluate state and return routing decisions.
"""

from __future__ import annotations

from typing import Any, Callable

import structlog

logger = structlog.get_logger()

ConditionFn = Callable[[Any], str]


class ConditionRegistry:
    """Registry of named condition predicates for pipeline routing."""

    def __init__(self) -> None:
        self._conditions: dict[str, ConditionFn] = {}
        self._register_builtins()

    def register(self, name: str, fn: ConditionFn) -> None:
        self._conditions[name] = fn
        logger.debug("condition_registered", name=name)

    def get(self, name: str) -> ConditionFn:
        if name not in self._conditions:
            raise KeyError(f"Condition not found: {name}")
        return self._conditions[name]

    def has(self, name: str) -> bool:
        return name in self._conditions

    def list_all(self) -> list[str]:
        return list(self._conditions.keys())

    def _register_builtins(self) -> None:
        """Register built-in condition predicates."""

        def validation_router(state: Any) -> str:
            """Route after validation node in cognitive OS pipeline."""
            if getattr(state, "is_validated", False):
                return "commit"
            iteration_count = getattr(state, "iteration_count", 0)
            max_iterations = getattr(state, "max_iterations", 10)
            if iteration_count >= max_iterations:
                return "reflect"
            return "plan"

        def route_after_pairs(state: Any) -> str:
            """Route after pair execution in adversarial pipeline."""
            failed = getattr(state, "failed_pairs", [])
            completed = getattr(state, "completed_pairs", [])
            if len(failed) > len(completed):
                return "fail"
            get_unresolved = getattr(state, "get_unresolved_conflicts", None)
            if get_unresolved and get_unresolved():
                return "conflicts"
            return "finalize"

        def route_after_conflicts(state: Any) -> str:
            """Route after conflict resolution."""
            return "finalize"

        self.register("validation_router", validation_router)
        self.register("route_after_pairs", route_after_pairs)
        self.register("route_after_conflicts", route_after_conflicts)
