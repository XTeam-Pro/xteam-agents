"""Platform-specific exceptions for recursive multi-agent execution."""


class PlatformError(Exception):
    """Base exception for platform errors."""


class BudgetExhaustedError(PlatformError):
    """Raised when resource budget is exhausted."""

    def __init__(self, budget_info: dict | None = None):
        self.budget_info = budget_info or {}
        super().__init__(f"Resource budget exhausted: {self.budget_info}")


class MaxDepthExceededError(PlatformError):
    """Raised when maximum recursion depth is exceeded."""

    def __init__(self, current_depth: int, max_depth: int):
        self.current_depth = current_depth
        self.max_depth = max_depth
        super().__init__(f"Maximum recursion depth exceeded: {current_depth} > {max_depth}")


class AgentSpecNotFoundError(PlatformError):
    """Raised when an agent spec is not found in registry."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent spec not found: {agent_id}")


class PipelineSpecNotFoundError(PlatformError):
    """Raised when a pipeline spec is not found."""

    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        super().__init__(f"Pipeline spec not found: {pipeline_id}")


class SpawnNotAllowedError(PlatformError):
    """Raised when an agent tries to spawn but doesn't have permission."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent {agent_id} is not allowed to spawn child pipelines")


class ConditionNotFoundError(PlatformError):
    """Raised when a condition predicate is not found."""

    def __init__(self, condition_name: str):
        self.condition_name = condition_name
        super().__init__(f"Condition predicate not found: {condition_name}")
