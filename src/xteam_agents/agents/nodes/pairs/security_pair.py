"""Security Agent and Critic pair (Blue Team vs Red Team)."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class SecurityAgent(BaseAgent):
    """
    SecurityAgent (Blue Team) implements security measures.

    Responsibilities:
    - Design security architecture
    - Implement authentication/authorization
    - Plan encryption strategy
    - Setup security monitoring
    - Plan incident response
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.SECURITY)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a SecurityAgent (Blue Team) - responsible for security architecture and defense.

Your role:
- Design security architecture
- Implement authentication and authorization
- Plan encryption and secrets management
- Setup security monitoring and logging
- Plan incident response procedures

Focus on:
- Defense in depth
- Principle of least privilege
- Zero trust architecture
- Security monitoring
- Compliance (GDPR, SOC2, etc)

Output format:
{{
    "security_architecture": {{
        "approach": "zero-trust|defense-in-depth|etc",
        "layers": ["network", "application", "data"],
        "principles": ["least_privilege", "fail_secure", "defense_in_depth"]
    }},
    "authentication": {{
        "mechanism": "JWT|OAuth2|SAML|etc",
        "mfa": true|false,
        "session_management": "stateless|stateful",
        "password_policy": {{
            "min_length": 12,
            "complexity": "high",
            "rotation": "90 days"
        }}
    }},
    "authorization": {{
        "model": "RBAC|ABAC|ACL",
        "enforcement": "middleware|decorator|gateway",
        "granularity": "resource-level|action-level"
    }},
    "encryption": {{
        "at_rest": {{
            "algorithm": "AES-256",
            "key_management": "AWS KMS|Vault"
        }},
        "in_transit": {{
            "protocol": "TLS 1.3",
            "certificate_management": "Let's Encrypt|ACM"
        }},
        "secrets_management": "HashiCorp Vault|AWS Secrets Manager"
    }},
    "monitoring": {{
        "security_events": ["failed_login", "privilege_escalation", "data_access"],
        "tools": ["SIEM", "IDS/IPS"],
        "alerting": ["Slack", "PagerDuty"],
        "log_retention": "1 year"
    }},
    "incident_response": {{
        "detection": "automated|manual",
        "response_time": "15 minutes",
        "escalation_path": ["on-call", "security-team", "ciso"],
        "playbooks": ["breach", "ddos", "data-leak"]
    }},
    "compliance": ["GDPR", "SOC2", "ISO27001"]
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute security architecture design."""
        task_prompt = f"""
Design the security architecture for this task:

TASK: {state.original_request}

Consider:
1. What authentication/authorization is needed?
2. How to protect data (encryption)?
3. What security monitoring is required?
4. How to detect and respond to incidents?
5. What compliance requirements apply?

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
                f"Strengthened security measures" if previous_feedback else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "security_architecture" in content:
            approach = content["security_architecture"].get("approach", "")
            return f"Security with {approach} architecture"
        return str(content)[:200]


class SecurityCritic(BaseCritic):
    """
    SecurityCritic (Red Team) attacks security measures.

    Strategy: Adversarial (Red Team)
    Focus:
    - Finding vulnerabilities
    - Attack vector identification
    - Penetration testing scenarios
    - Security bypass attempts
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.SECURITY_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are a SecurityCritic (Red Team) - you attack security measures to find vulnerabilities.

Your role:
- Find security vulnerabilities
- Identify attack vectors
- Attempt to bypass security controls
- Test for OWASP Top 10 vulnerabilities
- Challenge security assumptions

Strategy: Adversarial (actively try to break security)

Attack vectors to test:
1. Authentication bypass
2. Authorization flaws (privilege escalation)
3. Injection attacks (SQL, XSS, command)
4. Broken access control
5. Security misconfiguration
6. Sensitive data exposure
7. Insufficient logging
8. SSRF and other API attacks
9. Cryptographic failures
10. Supply chain vulnerabilities

Be aggressive in finding weaknesses - assume attacker mindset.

Output format:
{{
    "decision": "APPROVED|REQUEST_REVISION",
    "correctness": 1-10,
    "completeness": 1-10,
    "quality": 1-10,
    "performance": 1-10,
    "security": 1-10,
    "feedback": "Overall assessment",
    "vulnerabilities_found": [
        {{
            "type": "SQL Injection|XSS|etc",
            "severity": "critical|high|medium|low",
            "attack_vector": "How to exploit",
            "impact": "What attacker can achieve",
            "mitigation": "How to fix"
        }},
        ...
    ],
    "concerns": ["concern 1", "concern 2", ...],
    "suggestions": ["suggestion 1", "suggestion 2", ...]
}}

Be thorough and assume the worst-case attacker."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate security measures (Red Team attack)."""
        eval_prompt = self._build_evaluation_prompt(state, agent_output)

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=eval_prompt),
        ]

        response = await self.invoke_llm(messages)
        eval_data = self._parse_evaluation_response(response)

        # Extract vulnerabilities if present
        vulnerabilities = eval_data.get("vulnerabilities_found", [])

        # Add vulnerabilities to concerns
        vulnerability_concerns = [
            f"[{v.get('severity', 'unknown').upper()}] {v.get('type', 'Unknown')}: {v.get('attack_vector', 'No details')}"
            for v in vulnerabilities
        ]

        evaluation = CriticEvaluation(
            correctness=float(eval_data.get("correctness", 5.0)),
            completeness=float(eval_data.get("completeness", 5.0)),
            quality=float(eval_data.get("quality", 5.0)),
            performance=float(eval_data.get("performance", 5.0)),
            security=float(eval_data.get("security", 5.0)),
            feedback=eval_data.get("feedback", "No feedback provided"),
            concerns=eval_data.get("concerns", []) + vulnerability_concerns,
            suggestions=eval_data.get("suggestions", []),
            approved=(eval_data.get("decision") == "APPROVED"),
        )

        # All security concerns are critical
        concerns = evaluation.concerns
        must_address = [
            c
            for c in concerns
            if any(
                word in c.lower()
                for word in [
                    "vulnerability",
                    "attack",
                    "exploit",
                    "injection",
                    "xss",
                    "csrf",
                    "critical",
                    "high",
                    "bypass",
                    "exposure",
                ]
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
