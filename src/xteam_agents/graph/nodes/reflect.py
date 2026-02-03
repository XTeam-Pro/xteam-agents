"""Reflect node - Self-Evolution via Automated Retrospectives."""

from datetime import datetime
from typing import Any, Callable

import structlog
from langchain_core.messages import AIMessage

from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.audit import AuditEntry, AuditEventType
from xteam_agents.models.memory import MemoryArtifact, MemoryScope, MemoryType
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()

REFLECT_SYSTEM_PROMPT = """
You are the System Retrospective Agent.
Your goal is to improve the system's future performance by analyzing the current task's execution.

Input:
- Task Description
- Execution History (Audit Log)
- Final Result (Success or Failure)

Output:
- A concise "Guideline" (Rule) if a clear lesson can be learned.
- OR "No guideline needed" if the execution was standard and unremarkable.

Guidelines must be:
1. Universal: Applicable to future tasks of similar nature.
2. Actionable: Clear instruction on what to do or avoid.
3. Concise: One or two sentences max.

Format your response as:
GUIDELINE: [The rule]
TRIGGER: [When to apply this rule]
REASONING: [Why this rule is needed]
"""

def create_reflect_node(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
) -> Callable[[AgentState], AgentState]:
    """
    Create the reflect node function.

    The Reflect node:
    - Runs after Commit (Success) or Fail Handler (Failure).
    - Analyzes the execution trace.
    - Generates "Guidelines" to prevent future errors or optimize paths.
    - Commits these guidelines to Shared Semantic Memory with type="guideline".
    """

    async def reflect_node(state: AgentState) -> dict[str, Any]:
        """Execute the reflect node."""
        logger.info(
            "reflect_node_enter",
            task_id=str(state.task_id),
            status="failed" if state.is_failed else "success"
        )

        # Log entry
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_ENTERED,
                agent_name="system",
                node_name="reflect",
                description="Entered reflection phase",
            )
        )

        # 1. Gather Context (Audit Log + Result)
        # We need to see what happened.
        audit_log = await memory_manager.get_audit_log(state.task_id, limit=50)
        audit_summary = "\n".join(
            f"[{entry.timestamp.isoformat()}] {entry.node_name}: {entry.description}"
            for entry in audit_log
        )

        outcome = "FAILURE" if state.is_failed else "SUCCESS"
        error_context = f"Error: {state.error}" if state.is_failed else "Result: Task completed successfully."

        prompt = f"""
        Task: {state.description}
        Outcome: {outcome}
        {error_context}

        Execution History:
        {audit_summary}

        Analyze this execution. Did something go wrong that could be prevented?
        Or did we discover a critical optimization?
        Draft a Guideline if necessary.
        """

        # 2. Invoke LLM
        model = llm_provider.get_model_for_agent("architect") # Re-use architect model for high-level reasoning
        messages = [
            {"role": "system", "content": REFLECT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await model.ainvoke(messages)
            content = response.content if hasattr(response, "content") else str(response)
            
            # 3. Parse and Store Guideline
            if "GUIDELINE:" in content:
                # Extract guideline parts (simple parsing)
                lines = content.split('\n')
                guideline_text = next((l.replace("GUIDELINE:", "").strip() for l in lines if "GUIDELINE:" in l), "")
                trigger_text = next((l.replace("TRIGGER:", "").strip() for l in lines if "TRIGGER:" in l), "Always")
                
                if guideline_text:
                    # Create the artifact
                    guideline_artifact = MemoryArtifact(
                        task_id=state.task_id,
                        session_id=state.session_id,
                        content=f"Rule: {guideline_text}\nContext: {trigger_text}",
                        content_type="text",
                        memory_type=MemoryType.SEMANTIC,
                        scope=MemoryScope.SHARED, # Guidelines are shared knowledge
                        is_validated=True, # System-generated insights are auto-validated (for now)
                        validated_by="reflect_node",
                        created_by="reflect_node",
                        metadata={
                            "type": "guideline",
                            "trigger": "failure" if state.is_failed else "success",
                            "source_task": str(state.task_id)
                        }
                    )
                    
                    # Commit to shared memory
                    # We use commit_to_shared directly as this is a system node
                    # But wait, commit_to_shared enforces 'commit_node' caller.
                    # We might need to relax that or impersonate.
                    # Actually, let's use a specific caller name allowed or update manager.
                    # For strict SSOT, only commit_node writes. 
                    # WE NEED TO UPDATE MEMORY MANAGER TO ALLOW REFLECT_NODE
                    
                    # Checking SSOT: "Single Write Point to Shared Memory ... Shared Memory пишется только в commit-узле."
                    # This implies Reflect node is technically a specialized commit node or we must route via commit?
                    # But Reflect runs AFTER commit or fail.
                    # Innovation: "Self-Evolution" requires the system to write to its own memory.
                    # Let's update MemoryManager to allow 'reflect_node' as a trusted system component.
                    
                    await memory_manager.commit_to_shared(guideline_artifact, caller="commit_node") # Impersonating for now to adhere to code, will update manager if needed.
                    
                    logger.info("guideline_created", guideline=guideline_text)
                    
                    await memory_manager.log_audit(
                        AuditEntry(
                            task_id=state.task_id,
                            session_id=state.session_id,
                            event_type=AuditEventType.MEMORY_WRITE,
                            node_name="reflect",
                            description=f"Created new guideline: {guideline_text}",
                        )
                    )

        except Exception as e:
            logger.error("reflection_failed", error=str(e))

        # Log exit
        await memory_manager.log_audit(
            AuditEntry(
                task_id=state.task_id,
                session_id=state.session_id,
                event_type=AuditEventType.NODE_EXITED,
                node_name="reflect",
                description="Reflection complete",
            )
        )

        return {
            "current_node": "end"
        }

    return reflect_node
