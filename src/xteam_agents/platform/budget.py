"""Resource budget management for recursive pipeline execution.

Tracks token usage, time, depth, and parallelism to prevent
runaway recursive pipelines.
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field


class ResourceBudget(BaseModel):
    """Resource constraints for pipeline execution.

    Supports hierarchical budgeting: child pipelines get a fraction
    of the parent's remaining budget.
    """

    # Limits
    max_tokens: int = Field(default=100_000, ge=1)
    max_time_seconds: float = Field(default=300.0, ge=1.0)
    max_depth: int = Field(default=3, ge=1)
    max_parallel: int = Field(default=5, ge=1)
    max_iterations: int = Field(default=10, ge=1)

    # Tracking
    tokens_used: int = Field(default=0, ge=0)
    time_started: float = Field(default_factory=time.time)
    current_depth: int = Field(default=0, ge=0)
    iterations_used: int = Field(default=0, ge=0)

    def is_exhausted(self) -> bool:
        return (
            self.tokens_used >= self.max_tokens
            or self.elapsed_seconds() >= self.max_time_seconds
            or self.current_depth > self.max_depth
            or self.iterations_used >= self.max_iterations
        )

    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    def remaining_time(self) -> float:
        return max(0.0, self.max_time_seconds - self.elapsed_seconds())

    def elapsed_seconds(self) -> float:
        return time.time() - self.time_started

    def consume_tokens(self, count: int) -> None:
        self.tokens_used += count

    def increment_iteration(self) -> None:
        self.iterations_used += 1

    def allocate_child(self, fraction: float = 0.3) -> ResourceBudget:
        """Create a child budget with a fraction of remaining resources."""
        fraction = max(0.01, min(1.0, fraction))
        return ResourceBudget(
            max_tokens=int(self.remaining_tokens() * fraction),
            max_time_seconds=self.remaining_time() * fraction,
            max_depth=self.max_depth,
            max_parallel=self.max_parallel,
            max_iterations=max(1, int(self.max_iterations * fraction)),
            current_depth=self.current_depth + 1,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "tokens_used": self.tokens_used,
            "remaining_tokens": self.remaining_tokens(),
            "max_time_seconds": self.max_time_seconds,
            "elapsed_seconds": round(self.elapsed_seconds(), 2),
            "remaining_time": round(self.remaining_time(), 2),
            "max_depth": self.max_depth,
            "current_depth": self.current_depth,
            "max_iterations": self.max_iterations,
            "iterations_used": self.iterations_used,
            "is_exhausted": self.is_exhausted(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceBudget:
        return cls(
            max_tokens=data.get("max_tokens", 100_000),
            max_time_seconds=data.get("max_time_seconds", 300.0),
            max_depth=data.get("max_depth", 3),
            max_parallel=data.get("max_parallel", 5),
            max_iterations=data.get("max_iterations", 10),
        )
