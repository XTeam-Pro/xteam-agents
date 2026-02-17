"""Tests for ResourceBudget."""

import time

from xteam_agents.platform.budget import ResourceBudget


class TestResourceBudget:
    def test_defaults(self):
        b = ResourceBudget()
        assert b.max_tokens == 100_000
        assert b.max_depth == 3
        assert b.tokens_used == 0
        assert not b.is_exhausted()

    def test_remaining_tokens(self):
        b = ResourceBudget(max_tokens=1000, tokens_used=300)
        assert b.remaining_tokens() == 700

    def test_remaining_tokens_cannot_go_negative(self):
        b = ResourceBudget(max_tokens=100, tokens_used=200)
        assert b.remaining_tokens() == 0

    def test_consume_tokens(self):
        b = ResourceBudget(max_tokens=1000)
        b.consume_tokens(500)
        assert b.tokens_used == 500
        assert b.remaining_tokens() == 500

    def test_increment_iteration(self):
        b = ResourceBudget(max_iterations=3)
        assert b.iterations_used == 0
        b.increment_iteration()
        assert b.iterations_used == 1

    def test_exhausted_by_tokens(self):
        b = ResourceBudget(max_tokens=100)
        b.consume_tokens(100)
        assert b.is_exhausted()

    def test_exhausted_by_iterations(self):
        b = ResourceBudget(max_iterations=2)
        b.increment_iteration()
        b.increment_iteration()
        assert b.is_exhausted()

    def test_exhausted_by_depth(self):
        b = ResourceBudget(max_depth=2, current_depth=3)
        assert b.is_exhausted()

    def test_exhausted_by_time(self):
        b = ResourceBudget(max_time_seconds=1.0, time_started=time.time() - 2.0)
        assert b.is_exhausted()

    def test_not_exhausted(self):
        b = ResourceBudget(max_tokens=1000, max_iterations=10)
        b.consume_tokens(50)
        b.increment_iteration()
        assert not b.is_exhausted()

    def test_allocate_child(self):
        b = ResourceBudget(
            max_tokens=10000,
            tokens_used=4000,
            max_depth=3,
            current_depth=0,
            max_iterations=10,
        )
        child = b.allocate_child(0.5)
        # 6000 remaining * 0.5 = 3000
        assert child.max_tokens == 3000
        assert child.current_depth == 1
        assert child.max_depth == 3
        assert child.max_iterations == 5

    def test_allocate_child_fraction_clamped(self):
        b = ResourceBudget(max_tokens=10000)
        child_low = b.allocate_child(0.0)
        assert child_low.max_tokens > 0  # clamped to 0.01

        child_high = b.allocate_child(2.0)
        assert child_high.max_tokens == 10000  # clamped to 1.0

    def test_to_dict(self):
        b = ResourceBudget(max_tokens=5000, tokens_used=1000, max_depth=2)
        d = b.to_dict()
        assert d["max_tokens"] == 5000
        assert d["tokens_used"] == 1000
        assert d["remaining_tokens"] == 4000
        assert d["max_depth"] == 2
        assert isinstance(d["is_exhausted"], bool)

    def test_from_dict(self):
        b = ResourceBudget.from_dict({"max_tokens": 50000, "max_depth": 5})
        assert b.max_tokens == 50000
        assert b.max_depth == 5
        assert b.tokens_used == 0

    def test_from_dict_defaults(self):
        b = ResourceBudget.from_dict({})
        assert b.max_tokens == 100_000
        assert b.max_depth == 3

    def test_elapsed_seconds(self):
        b = ResourceBudget(time_started=time.time() - 5.0)
        assert b.elapsed_seconds() >= 4.9

    def test_remaining_time(self):
        b = ResourceBudget(max_time_seconds=10.0, time_started=time.time() - 3.0)
        remaining = b.remaining_time()
        assert 6.0 <= remaining <= 7.5
