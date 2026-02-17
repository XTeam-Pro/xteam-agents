"""Tests for ExecutionContext and PipelineResult."""

from uuid import uuid4

from xteam_agents.platform.budget import ResourceBudget
from xteam_agents.platform.context import ExecutionContext, PipelineResult, PipelineStatus


class TestPipelineStatus:
    def test_values(self):
        assert PipelineStatus.PENDING == "pending"
        assert PipelineStatus.COMPLETED == "completed"
        assert PipelineStatus.BUDGET_EXHAUSTED == "budget_exhausted"


class TestPipelineResult:
    def test_completed_summary(self):
        r = PipelineResult(
            pipeline_id="test.pipeline",
            status=PipelineStatus.COMPLETED,
            result="All done",
        )
        assert r.summary == "All done"

    def test_completed_no_result(self):
        r = PipelineResult(
            pipeline_id="test.pipeline",
            status=PipelineStatus.COMPLETED,
        )
        assert r.summary == "Completed successfully"

    def test_failed_summary(self):
        r = PipelineResult(
            pipeline_id="test.pipeline",
            status=PipelineStatus.FAILED,
            error="Something went wrong",
        )
        assert "Something went wrong" in r.summary

    def test_budget_exhausted_summary(self):
        r = PipelineResult(
            pipeline_id="test.pipeline",
            status=PipelineStatus.BUDGET_EXHAUSTED,
            budget_consumed={"tokens_used": 1000},
        )
        assert "Budget exhausted" in r.summary

    def test_pending_summary(self):
        r = PipelineResult(
            pipeline_id="test.pipeline",
            status=PipelineStatus.PENDING,
        )
        assert "pending" in r.summary

    def test_child_results(self):
        child = PipelineResult(
            pipeline_id="child",
            status=PipelineStatus.COMPLETED,
        )
        parent = PipelineResult(
            pipeline_id="parent",
            status=PipelineStatus.COMPLETED,
            child_results=[child],
        )
        assert len(parent.child_results) == 1
        assert parent.child_results[0].pipeline_id == "child"


class TestExecutionContext:
    def test_creation(self):
        budget = ResourceBudget()
        ctx = ExecutionContext(
            pipeline_id="test.pipeline",
            task_id=uuid4(),
            budget=budget,
        )
        assert ctx.depth == 0
        assert ctx.status == PipelineStatus.PENDING
        assert ctx.parent_context_id is None

    def test_start(self):
        ctx = ExecutionContext(
            pipeline_id="test",
            task_id=uuid4(),
            budget=ResourceBudget(),
        )
        ctx.start()
        assert ctx.status == PipelineStatus.RUNNING
        assert ctx.started_at is not None

    def test_complete(self):
        ctx = ExecutionContext(
            pipeline_id="test",
            task_id=uuid4(),
            budget=ResourceBudget(),
        )
        ctx.start()
        ctx.complete(PipelineStatus.COMPLETED)
        assert ctx.status == PipelineStatus.COMPLETED
        assert ctx.completed_at is not None

    def test_visit_node(self):
        ctx = ExecutionContext(
            pipeline_id="test",
            task_id=uuid4(),
            budget=ResourceBudget(),
        )
        ctx.visit_node("analyze")
        ctx.visit_node("plan")
        assert ctx.nodes_visited == ["analyze", "plan"]

    def test_can_spawn_child(self):
        budget = ResourceBudget(max_depth=3)
        ctx = ExecutionContext(
            pipeline_id="test",
            task_id=uuid4(),
            depth=1,
            budget=budget,
        )
        assert ctx.can_spawn_child()

    def test_cannot_spawn_at_max_depth(self):
        budget = ResourceBudget(max_depth=2)
        ctx = ExecutionContext(
            pipeline_id="test",
            task_id=uuid4(),
            depth=2,
            budget=budget,
        )
        assert not ctx.can_spawn_child()

    def test_cannot_spawn_exhausted_budget(self):
        budget = ResourceBudget(max_tokens=100, max_depth=3)
        budget.consume_tokens(100)
        ctx = ExecutionContext(
            pipeline_id="test",
            task_id=uuid4(),
            depth=0,
            budget=budget,
        )
        assert not ctx.can_spawn_child()

    def test_create_child_context(self):
        budget = ResourceBudget(max_tokens=10000, max_depth=3)
        parent = ExecutionContext(
            pipeline_id="parent",
            task_id=uuid4(),
            depth=0,
            budget=budget,
        )

        child_task = uuid4()
        child = parent.create_child_context(
            pipeline_id="child",
            task_id=child_task,
            budget_fraction=0.5,
        )

        assert child.depth == 1
        assert child.parent_context_id == parent.context_id
        assert child.pipeline_id == "child"
        assert child.task_id == child_task
        assert child.budget.max_tokens == 5000
        assert child.context_id in parent.child_context_ids

    def test_execution_time(self):
        ctx = ExecutionContext(
            pipeline_id="test",
            task_id=uuid4(),
            budget=ResourceBudget(),
        )
        assert ctx.execution_time() is None

        ctx.start()
        ctx.complete()
        et = ctx.execution_time()
        assert et is not None
        assert et >= 0
