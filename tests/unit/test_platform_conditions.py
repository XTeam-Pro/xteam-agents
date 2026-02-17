"""Tests for ConditionRegistry and built-in predicates."""

from types import SimpleNamespace

import pytest

from xteam_agents.platform.conditions import ConditionRegistry


@pytest.fixture
def condition_registry():
    return ConditionRegistry()


class TestConditionRegistry:
    def test_builtins_registered(self, condition_registry):
        assert condition_registry.has("validation_router")
        assert condition_registry.has("route_after_pairs")
        assert condition_registry.has("route_after_conflicts")

    def test_list_all(self, condition_registry):
        all_names = condition_registry.list_all()
        assert len(all_names) >= 3
        assert "validation_router" in all_names

    def test_get_not_found(self, condition_registry):
        with pytest.raises(KeyError, match="Condition not found"):
            condition_registry.get("nonexistent")

    def test_register_custom(self, condition_registry):
        def my_condition(state):
            return "done"

        condition_registry.register("my_cond", my_condition)
        assert condition_registry.has("my_cond")
        assert condition_registry.get("my_cond") is my_condition


class TestValidationRouter:
    def test_routes_to_commit_when_validated(self, condition_registry):
        fn = condition_registry.get("validation_router")
        state = SimpleNamespace(is_validated=True, iteration_count=0, max_iterations=10)
        assert fn(state) == "commit"

    def test_routes_to_plan_when_not_validated(self, condition_registry):
        fn = condition_registry.get("validation_router")
        state = SimpleNamespace(is_validated=False, iteration_count=1, max_iterations=10)
        assert fn(state) == "plan"

    def test_routes_to_reflect_at_max_iterations(self, condition_registry):
        fn = condition_registry.get("validation_router")
        state = SimpleNamespace(is_validated=False, iteration_count=10, max_iterations=10)
        assert fn(state) == "reflect"


class TestRouteAfterPairs:
    def test_routes_to_finalize_when_clean(self, condition_registry):
        fn = condition_registry.get("route_after_pairs")
        state = SimpleNamespace(
            failed_pairs=[],
            completed_pairs=["p1", "p2"],
            get_unresolved_conflicts=lambda: [],
        )
        assert fn(state) == "finalize"

    def test_routes_to_fail_when_too_many_failures(self, condition_registry):
        fn = condition_registry.get("route_after_pairs")
        state = SimpleNamespace(
            failed_pairs=["f1", "f2", "f3"],
            completed_pairs=["p1"],
        )
        assert fn(state) == "fail"

    def test_routes_to_conflicts(self, condition_registry):
        fn = condition_registry.get("route_after_pairs")
        state = SimpleNamespace(
            failed_pairs=[],
            completed_pairs=["p1"],
            get_unresolved_conflicts=lambda: ["conflict1"],
        )
        assert fn(state) == "conflicts"


class TestRouteAfterConflicts:
    def test_always_routes_to_finalize(self, condition_registry):
        fn = condition_registry.get("route_after_conflicts")
        assert fn(None) == "finalize"
