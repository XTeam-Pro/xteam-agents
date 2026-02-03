"""DevOps Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class DevOpsAgent(BaseAgent):
    """
    DevOpsAgent manages infrastructure and deployment.

    Responsibilities:
    - Design CI/CD pipelines
    - Plan deployment strategy
    - Setup monitoring
    - Configure infrastructure
    - Plan disaster recovery
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.DEVOPS)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a DevOpsAgent - responsible for infrastructure and deployment.

Your role:
- Design CI/CD pipelines
- Plan deployment strategies
- Setup monitoring and alerting
- Configure infrastructure (IaC)
- Plan backup and disaster recovery

Focus on:
- Automation
- Reliability
- Observability
- Security
- Cost optimization

Output format:
{{
    "ci_cd_pipeline": {{
        "stages": ["build", "test", "deploy"],
        "tools": ["GitHub Actions", "Jenkins", etc],
        "environments": ["dev", "staging", "prod"],
        "deployment_strategy": "blue-green|canary|rolling"
    }},
    "infrastructure": {{
        "provider": "AWS|GCP|Azure",
        "components": ["load_balancer", "app_servers", "database"],
        "iac_tool": "Terraform|CloudFormation|Pulumi",
        "scaling": "horizontal|vertical|auto"
    }},
    "monitoring": {{
        "metrics": ["cpu", "memory", "latency", "errors"],
        "tools": ["Prometheus", "Grafana", "DataDog"],
        "alerts": [{{"condition": "...", "threshold": "...", "action": "..."}}]
    }},
    "backup_recovery": {{
        "backup_frequency": "hourly|daily|weekly",
        "retention": "30 days",
        "recovery_strategy": "...",
        "rto": "1 hour",
        "rpo": "5 minutes"
    }},
    "security": ["security measure 1", ...]
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute DevOps planning."""
        task_prompt = f"""
Plan the infrastructure and deployment for this task:

TASK: {state.original_request}

Consider:
1. What CI/CD pipeline is needed?
2. How to deploy reliably?
3. What monitoring is required?
4. How to handle failures?
5. What's the backup strategy?

Provide your response as JSON matching the format in your system prompt.
"""

        messages = self._build_messages(state, task_prompt, previous_feedback)
        response = await self.invoke_llm(messages)

        try:
            content = self._parse_json_response(response)
        except:
            content = {"raw_response": response}

        return AgentOutput(
            agent_role=self.config.role,
            iteration=0,
            content=content,
            rationale=self._extract_rationale(content),
            changes_from_previous=(
                f"Updated infrastructure plan" if previous_feedback else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "ci_cd_pipeline" in content:
            strategy = content["ci_cd_pipeline"].get("deployment_strategy", "")
            return f"DevOps with {strategy} deployment"
        return str(content)[:200]


class DevOpsCritic(BaseCritic):
    """
    DevOpsCritic tests infrastructure resilience.

    Strategy: Constructive
    Focus:
    - Deployment reliability
    - Monitoring coverage
    - Disaster recovery
    - Security hardening
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.DEVOPS_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a DevOpsCritic - you test infrastructure resilience.

Your role:
- Review deployment strategy
- Check monitoring coverage
- Validate backup plans
- Find security gaps
- Test failure scenarios

Strategy: Constructive (find issues and suggest improvements)

Focus on:
1. Can the system recover from failures?
2. Is monitoring comprehensive?
3. Is the backup strategy sufficient?
4. Are there security vulnerabilities?
5. Will deployment work smoothly?

Be thorough about reliability and security."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate DevOps plan."""
        eval_prompt = self._build_evaluation_prompt(state, agent_output)

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=eval_prompt),
        ]

        response = await self.invoke_llm(messages)
        eval_data = self._parse_evaluation_response(response)

        evaluation = CriticEvaluation(
            correctness=float(eval_data.get("correctness", 5.0)),
            completeness=float(eval_data.get("completeness", 5.0)),
            quality=float(eval_data.get("quality", 5.0)),
            performance=float(eval_data.get("performance", 5.0)),
            security=float(eval_data.get("security", 5.0)),
            feedback=eval_data.get("feedback", "No feedback provided"),
            concerns=eval_data.get("concerns", []),
            suggestions=eval_data.get("suggestions", []),
            approved=(eval_data.get("decision") == "APPROVED"),
        )

        concerns = eval_data.get("concerns", [])
        must_address = [
            c
            for c in concerns
            if any(
                word in c.lower()
                for word in ["failure", "security", "monitoring", "backup", "disaster"]
            )
        ]

        return CriticReview(
            critic_role=self.config.role,
            iteration=0,
            evaluation=evaluation,
            decision=eval_data.get("decision", "REQUEST_REVISION"),
            detailed_feedback=eval_data.get("feedback", ""),
            must_address=must_address,
            nice_to_have=eval_data.get("suggestions", [])[:3],
        )
