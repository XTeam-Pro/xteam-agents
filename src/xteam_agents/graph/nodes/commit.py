"""Commit node - the SINGLE write point to shared memory."""

from datetime import datetime
from typing import Any, Callable

import structlog

from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState
from xteam_agents.models.task import TaskStatus

logger = structlog.get_logger()


def create_commit_node(
    memory_manager: MemoryManager,
) -> Callable[[AgentState], AgentState]:
    """
    Create the commit node function.

    The commit_node is the ONLY node that can write to shared memory.
    It is a system function, not an LLM agent.

    This enforces the invariant that only validated content
    reaches the shared knowledge base.

    Responsibilities:
    1. Verify artifact is validated
    2. Generate embeddings
    3. Write to semantic memory (Qdrant)
    4. Write to procedural memory (Neo4j)
    5. Record in audit log
    """

    async def commit_node(state: AgentState) -> dict[str, Any]:
        """Execute the commit node."""
        logger.info(
            "commit_node_enter",
            task_id=str(state.task_id),
            is_validated=state.is_validated,
        )

        # INVARIANT: Only validated tasks can commit
        if not state.is_validated:
            logger.error(
                "commit_node_unvalidated",
                task_id=str(state.task_id),
            )
            await memory_manager.log_audit(
                AuditEntry(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    event_type=AuditEventType.SYSTEM_ERROR,
                    node_name="commit",
                    description="Attempted to commit unvalidated task",
                )
            )
            return {
                "is_failed": True,
                "error": "Cannot commit unvalidated task",
            }

        # Log entry
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_ENTERED,
                node_name="commit",
                description="Entered commit node",
            )
        )

        # Create the knowledge artifact
        # This contains the validated result that will be stored in shared memory
        knowledge_content = _create_knowledge_content(state)

        # Create validated artifact
        artifact = MemoryArtifact(
            task_id=state.task_id,
            session_id=state.session_id,
            content=knowledge_content,
            content_type="task_result",
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.SHARED,
            created_by="commit_node",
            is_validated=True,
            validated_by="reviewer",
            validated_at=datetime.utcnow(),
            metadata={
                "task_description": state.description[:200],
                "iteration_count": state.iteration_count,
                "validation_attempts": state.validation_attempts,
            },
        )

        # Commit to shared memory using the manager
        # This is the ONLY place that calls commit_to_shared
        try:
            await memory_manager.commit_to_shared(artifact, caller="commit_node")

            # If there are relationships to store, create procedural artifact
            if state.analysis and state.plan:
                # Create relationship between analysis and result
                procedural_artifact = artifact.model_copy(
                    update={
                        "memory_type": MemoryType.PROCEDURAL,
                        "relationship_type": "DERIVED_FROM",
                        "metadata": {
                            **artifact.metadata,
                            "has_analysis": True,
                            "has_plan": True,
                        },
                    }
                )
                await memory_manager.commit_to_shared(
                    procedural_artifact, caller="commit_node"
                )

            logger.info(
                "commit_node_success",
                task_id=str(state.task_id),
                artifact_id=str(artifact.id),
            )

        except Exception as e:
            logger.error(
                "commit_node_error",
                task_id=str(state.task_id),
                error=str(e),
            )
            await memory_manager.log_audit(
                AuditEntry(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    event_type=AuditEventType.SYSTEM_ERROR,
                    node_name="commit",
                    description=f"Commit failed: {str(e)}",
                )
            )
            return {
                "is_failed": True,
                "error": f"Commit failed: {str(e)}",
            }

        # Log successful commit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.TASK_COMPLETED,
                node_name="commit",
                description="Task committed to shared memory",
                data={"artifact_id": str(artifact.id)},
            )
        )

        # Log exit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_EXITED,
                node_name="commit",
                description="Commit complete",
            )
        )

        logger.info(
            "commit_node_complete",
            task_id=str(state.task_id),
        )

        # Return final state updates
        return {
            "current_node": "end",
            "artifacts": state.artifacts + [str(artifact.id)],
        }

    return commit_node


def _create_knowledge_content(state: AgentState) -> str:
    """
    Create the knowledge content to store in shared memory.

    This is a structured summary of the task execution that
    can be searched and retrieved later.
    """
    content_parts = [
        f"# Task: {state.description}",
        "",
        "## Analysis",
        state.analysis or "No analysis recorded.",
        "",
        "## Plan",
        state.plan or "No plan recorded.",
        "",
        "## Execution Result",
        state.execution_result or "No execution result recorded.",
        "",
        "## Subtasks",
    ]

    for subtask in state.subtasks:
        content_parts.append(
            f"- [{subtask.status.value}] {subtask.description}"
        )
        if subtask.result:
            content_parts.append(f"  Result: {subtask.result}")

    content_parts.extend([
        "",
        "## Metadata",
        f"- Iterations: {state.iteration_count}",
        f"- Validation Attempts: {state.validation_attempts}",
        f"- Priority: {state.priority}",
    ])

    return "\n".join(content_parts)
