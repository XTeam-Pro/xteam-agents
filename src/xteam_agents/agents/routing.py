"""Routing logic for agent team orchestration."""

import structlog

from .config import (
    AgentRole,
    TaskCategory,
    classify_task,
    get_required_agents,
    needs_review,
)
from .state import AgentTeamState, DecisionType

logger = structlog.get_logger()


class AgentRouter:
    """Routes tasks between agents based on rules."""

    def __init__(self):
        self.logger = logger.bind(component="AgentRouter")

    def route_initial(self, state: AgentTeamState) -> str:
        """Route initial task - always goes to TechLead."""
        self.logger.info("Routing initial task to TechLead", task_id=state.task_id)
        return "tech_lead_classify"

    def route_after_tech_lead(self, state: AgentTeamState) -> str:
        """Route after TechLead classification."""
        if not state.tech_lead_decision:
            self.logger.error("No TechLead decision found", task_id=state.task_id)
            return "fail_handler"

        decision = state.tech_lead_decision

        if decision.decision_type == DecisionType.REJECT:
            self.logger.info("Task rejected by TechLead", task_id=state.task_id)
            return "fail_handler"

        if decision.decision_type == DecisionType.ESCALATE:
            self.logger.info("Task escalated to user", task_id=state.task_id)
            return "escalate_to_user"

        # Determine which thinking phase agents are needed
        categories = state.task_categories
        reviews = needs_review(categories)

        # Route to thinking phase
        if reviews["architecture"] and TaskCategory.ARCHITECTURE in categories:
            self.logger.info("Routing to ArchitectAgent", task_id=state.task_id)
            state.current_phase = "thinking"
            return "architect"

        if reviews["security"] and TaskCategory.SECURITY in categories:
            self.logger.info("Routing to SecurityAgent", task_id=state.task_id)
            state.current_phase = "thinking"
            return "security"

        if reviews["performance"] and TaskCategory.PERFORMANCE in categories:
            self.logger.info("Routing to PerformanceAgent", task_id=state.task_id)
            state.current_phase = "thinking"
            return "performance"

        if TaskCategory.AI_SYSTEM in categories:
            self.logger.info("Routing to AIAgentArchitect", task_id=state.task_id)
            state.current_phase = "thinking"
            return "ai_architect"

        # Skip thinking phase, go straight to execution
        self.logger.info("Skipping thinking phase, routing to execution", task_id=state.task_id)
        return self.route_to_execution(state)

    def route_after_thinking(self, state: AgentTeamState) -> str:
        """Route after thinking phase (Architect/Security/Performance/AI)."""
        # Check if all required thinking agents have completed
        categories = state.task_categories
        reviews = needs_review(categories)

        # Check architecture
        if reviews["architecture"] and not state.architecture_plan:
            if AgentRole.ARCHITECT not in state.completed_agents:
                return "architect"

        # Check security
        if reviews["security"] and not state.security_clearance:
            if AgentRole.SECURITY not in state.completed_agents:
                return "security"

        # Check performance
        if reviews["performance"] and not state.performance_requirements:
            if AgentRole.PERFORMANCE not in state.completed_agents:
                return "performance"

        # Check AI architecture
        if TaskCategory.AI_SYSTEM in categories:
            if AgentRole.AI_ARCHITECT not in state.completed_agents:
                return "ai_architect"

        # All thinking agents done, move to execution
        self.logger.info("Thinking phase complete, routing to execution", task_id=state.task_id)
        return self.route_to_execution(state)

    def route_to_execution(self, state: AgentTeamState) -> str:
        """Route to execution agents."""
        state.current_phase = "execution"
        categories = state.task_categories

        # Priority order for execution
        if TaskCategory.DATA_MODEL in categories:
            if AgentRole.DATA not in state.completed_agents:
                self.logger.info("Routing to DataAgent", task_id=state.task_id)
                return "data"

        if TaskCategory.BACKEND_LOGIC in categories:
            if AgentRole.BACKEND not in state.completed_agents:
                self.logger.info("Routing to BackendAgent", task_id=state.task_id)
                return "backend"

        if TaskCategory.FRONTEND_UI in categories:
            if AgentRole.FRONTEND not in state.completed_agents:
                self.logger.info("Routing to FrontendAgent", task_id=state.task_id)
                return "frontend"

        if TaskCategory.INFRASTRUCTURE in categories:
            if AgentRole.DEVOPS not in state.completed_agents:
                self.logger.info("Routing to DevOpsAgent", task_id=state.task_id)
                return "devops"

        # All execution agents done, move to QA
        self.logger.info("Execution phase complete, routing to QA", task_id=state.task_id)
        state.current_phase = "qa"
        return "qa"

    def route_after_execution(self, state: AgentTeamState) -> str:
        """Route after execution agents."""
        # Check if all required execution agents have completed
        categories = state.task_categories

        if TaskCategory.DATA_MODEL in categories and AgentRole.DATA not in state.completed_agents:
            return "data"

        if (
            TaskCategory.BACKEND_LOGIC in categories
            and AgentRole.BACKEND not in state.completed_agents
        ):
            return "backend"

        if (
            TaskCategory.FRONTEND_UI in categories
            and AgentRole.FRONTEND not in state.completed_agents
        ):
            return "frontend"

        if (
            TaskCategory.INFRASTRUCTURE in categories
            and AgentRole.DEVOPS not in state.completed_agents
        ):
            return "devops"

        # All done, move to QA
        self.logger.info("All execution agents complete, routing to QA", task_id=state.task_id)
        state.current_phase = "qa"
        return "qa"

    def route_after_qa(self, state: AgentTeamState) -> str:
        """Route after QA validation."""
        if not state.qa_results:
            self.logger.error("No QA results found", task_id=state.task_id)
            return "fail_handler"

        qa = state.qa_results

        if qa.validation_status == "failed":
            self.logger.warning("QA validation failed", task_id=state.task_id, bugs=len(qa.bugs_found))

            # Check iteration limit
            if state.has_exceeded_max_iterations():
                self.logger.error("Max iterations exceeded", task_id=state.task_id)
                return "fail_handler"

            # Escalate to TechLead for decision on next steps
            state.add_escalation(
                from_agent=AgentRole.QA,
                reason="architecture_violation",  # Using as proxy for QA failure
                context={"bugs_found": len(qa.bugs_found), "tests_failed": qa.tests_failed},
                proposed_solution="Fix bugs and re-run QA",
                urgency="high",
            )
            return "tech_lead_escalation"

        if qa.validation_status == "passed":
            self.logger.info("QA validation passed, routing to final approval", task_id=state.task_id)
            state.current_phase = "approval"
            return "tech_lead_approval"

        self.logger.error("Unknown QA status", task_id=state.task_id, status=qa.validation_status)
        return "fail_handler"

    def route_after_final_approval(self, state: AgentTeamState) -> str:
        """Route after TechLead final approval."""
        if not state.final_approval:
            self.logger.error("No final approval found", task_id=state.task_id)
            return "fail_handler"

        if state.final_approval.approved:
            self.logger.info("Task approved, routing to commit", task_id=state.task_id)
            return "commit"

        self.logger.warning("Task not approved", task_id=state.task_id)
        return "fail_handler"

    def handle_escalation(self, state: AgentTeamState) -> str:
        """Handle escalation to TechLead."""
        escalations = state.get_active_escalations()

        if not escalations:
            self.logger.error("No active escalations found", task_id=state.task_id)
            return "fail_handler"

        # Route to TechLead to handle escalation
        self.logger.info(
            "Handling escalation",
            task_id=state.task_id,
            count=len(escalations),
            reasons=[e.reason for e in escalations],
        )
        return "tech_lead_escalation"

    def route_conditional(self, state: AgentTeamState) -> str:
        """Main conditional routing function."""
        phase = state.current_phase

        self.logger.debug("Routing", task_id=state.task_id, phase=phase, current_agent=state.current_agent)

        # Check for active escalations
        if state.get_active_escalations():
            return self.handle_escalation(state)

        # Route based on current phase
        if phase == "classification":
            return self.route_after_tech_lead(state)
        elif phase == "thinking":
            return self.route_after_thinking(state)
        elif phase == "execution":
            return self.route_after_execution(state)
        elif phase == "qa":
            return self.route_after_qa(state)
        elif phase == "approval":
            return self.route_after_final_approval(state)
        else:
            self.logger.error("Unknown phase", task_id=state.task_id, phase=phase)
            return "fail_handler"


# Global router instance
router = AgentRouter()


# Route functions for LangGraph
def route_initial_task(state: AgentTeamState) -> str:
    """Route initial task."""
    return router.route_initial(state)


def route_after_tech_lead_classification(state: AgentTeamState) -> str:
    """Route after TechLead classification."""
    return router.route_after_tech_lead(state)


def route_after_thinking_phase(state: AgentTeamState) -> str:
    """Route after thinking phase."""
    return router.route_after_thinking(state)


def route_after_execution_phase(state: AgentTeamState) -> str:
    """Route after execution phase."""
    return router.route_after_execution(state)


def route_after_qa_phase(state: AgentTeamState) -> str:
    """Route after QA phase."""
    return router.route_after_qa(state)


def route_after_final_approval(state: AgentTeamState) -> str:
    """Route after final approval."""
    return router.route_after_final_approval(state)


def route_on_escalation(state: AgentTeamState) -> str:
    """Route when escalation occurs."""
    return router.handle_escalation(state)


# Helper function for agents to request escalation
def should_escalate(state: AgentTeamState, agent: AgentRole, condition: str) -> bool:
    """Determine if agent should escalate based on condition."""
    escalation_conditions = {
        "ambiguous_requirements": lambda s: not s.tech_lead_decision or not s.tech_lead_decision.scope,
        "architecture_violation": lambda s: s.architecture_plan
        and not s.architecture_plan.approved_by_tech_lead,
        "security_risk": lambda s: s.security_clearance
        and s.security_clearance.clearance_level == "REJECTED",
        "qa_failure": lambda s: s.qa_results and s.qa_results.validation_status == "failed",
        "max_iterations": lambda s: s.has_exceeded_max_iterations(),
    }

    condition_fn = escalation_conditions.get(condition)
    if condition_fn and condition_fn(state):
        logger.info("Escalation condition met", agent=agent, condition=condition, task_id=state.task_id)
        return True

    return False
