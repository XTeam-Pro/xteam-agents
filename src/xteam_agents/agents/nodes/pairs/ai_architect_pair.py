"""AI Architect Agent and Critic pair."""

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ....config import Settings
from ...adversarial_config import AgentRole, CriticEvaluation, get_agent_config
from ...adversarial_state import AdversarialAgentState, AgentOutput, CriticReview
from ...base import BaseAgent, BaseCritic


class AIAgentArchitect(BaseAgent):
    """
    AIAgentArchitect designs AI/ML architecture.

    Responsibilities:
    - Design AI/ML pipelines
    - Select models and approaches
    - Plan training infrastructure
    - Design inference optimization
    - Plan MLOps workflow
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.AI_ARCHITECT)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are an AIAgentArchitect - responsible for AI/ML system architecture.

Your role:
- Design AI/ML pipelines and workflows
- Select appropriate models and approaches
- Plan training infrastructure
- Design inference optimization
- Establish MLOps practices

Focus on:
- Model selection rationale
- Training efficiency
- Inference performance
- Model versioning
- Monitoring and retraining

Output format:
{{
    "ml_pipeline": {{
        "problem_type": "classification|regression|generation|etc",
        "approach": "supervised|unsupervised|reinforcement",
        "stages": [
            {{
                "stage": "data_preparation",
                "tasks": ["cleaning", "feature_engineering"],
                "tools": ["pandas", "sklearn"]
            }},
            ...
        ]
    }},
    "model_architecture": {{
        "model_type": "transformer|cnn|lstm|etc",
        "framework": "PyTorch|TensorFlow|JAX",
        "pretrained": "gpt-4|bert|resnet|custom",
        "customization": "fine-tuning|full-training|prompt-engineering",
        "rationale": "Why this model"
    }},
    "training_infrastructure": {{
        "compute": "GPU|TPU|CPU",
        "distributed": true|false,
        "framework": "PyTorch DDP|Horovod|etc",
        "experiment_tracking": "MLflow|Weights&Biases|Neptune"
    }},
    "inference_optimization": {{
        "optimization": ["quantization", "pruning", "distillation"],
        "serving": "TorchServe|TFServing|Triton",
        "batching": true|false,
        "caching": "Redis|in-memory",
        "latency_target": "100ms"
    }},
    "mlops": {{
        "version_control": "DVC|Git-LFS",
        "ci_cd": "GitHub Actions|Kubeflow",
        "monitoring": ["model_drift", "data_drift", "performance"],
        "retraining_trigger": "scheduled|drift-based|performance-based"
    }}
}}"""

    async def execute(
        self,
        state: AdversarialAgentState,
        previous_feedback: Optional[str] = None,
    ) -> AgentOutput:
        """Execute AI/ML architecture design."""
        task_prompt = f"""
Design the AI/ML architecture for this task:

TASK: {state.original_request}

Consider:
1. What ML problem are we solving?
2. Which model architecture fits best?
3. What training infrastructure is needed?
4. How to optimize inference?
5. What MLOps practices to implement?

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
                f"Updated ML architecture based on feedback"
                if previous_feedback
                else None
            ),
        )

    def _parse_json_response(self, response: str) -> dict:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return {"raw_response": response}

    def _extract_rationale(self, content: dict) -> str:
        if "model_architecture" in content:
            model_type = content["model_architecture"].get("model_type", "")
            rationale = content["model_architecture"].get("rationale", "")
            return f"AI with {model_type}: {rationale}"
        return str(content)[:200]


class AIArchitectCritic(BaseCritic):
    """
    AIArchitectCritic validates ML design choices.

    Strategy: Constructive
    Focus:
    - Model selection validity
    - Training efficiency
    - Inference performance
    - MLOps maturity
    - Cost optimization
    """

    def __init__(self, settings: Settings, memory_manager=None, llm=None):
        config = get_agent_config(AgentRole.AI_ARCHITECT_CRITIC)
        super().__init__(config, settings, memory_manager, llm)

    def get_system_prompt(self) -> str:
        return """You are an AIArchitectCritic - you validate AI/ML architecture decisions.

Your role:
- Question model selection
- Validate training approach
- Check inference optimization
- Review MLOps practices
- Assess cost-effectiveness

Strategy: Constructive (find issues and suggest improvements)

Focus on:
1. Is the model appropriate for the problem?
2. Will training be efficient?
3. Can inference meet latency requirements?
4. Are MLOps practices sufficient?
5. Is the solution cost-effective?

Be thorough about model selection and performance requirements."""

    async def evaluate(
        self,
        state: AdversarialAgentState,
        agent_output: AgentOutput,
    ) -> CriticReview:
        """Evaluate AI/ML architecture."""
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
                for word in [
                    "model",
                    "training",
                    "inference",
                    "latency",
                    "performance",
                    "cost",
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
