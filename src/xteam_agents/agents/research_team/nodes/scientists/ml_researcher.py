"""
ML Researcher - Исследователь машинного обучения

Разработка нейронных архитектур, обучение моделей,
оптимизация и внедрение ML систем для образования.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class MLResearcher(ResearchAgent):
    """
    ML Researcher - Исследователь машинного обучения.

    РОЛЬ:
    - Разработка нейронных архитектур для образовательных задач
    - Обучение и fine-tuning моделей
    - Оптимизация производительности моделей
    - Research в области Educational AI
    - Разработка adaptive learning алгоритмов на основе ML
    - Transfer learning для образовательных доменов

    КОМПЕТЕНЦИИ:

    1. Deep Learning Architectures
       - Transformer models для образовательного контента
       - Graph Neural Networks для knowledge graphs
       - Sequence models для траекторий обучения
       - Attention mechanisms для question answering
       - Multi-task learning architectures

    2. Specialized Educational Models
       - Knowledge Tracing (DKT, DKVMN, SAKT)
       - Question Generation models
       - Automatic grading systems
       - Concept prerequisite prediction
       - Student modeling

    3. Training & Optimization
       - Curriculum learning strategies
       - Few-shot learning для новых тем
       - Active learning для efficient data collection
       - Meta-learning для быстрой адаптации
       - Federated learning для privacy

    4. Model Evaluation
       - Benchmark creation
       - Cross-validation strategies
       - Fairness and bias detection
       - Interpretability analysis
       - A/B testing в production

    5. MLOps для образования
       - Model versioning
       - Continuous training pipelines
       - Monitoring в production
       - Adaptive retraining

    СПЕЦИАЛИЗАЦИЯ В STUDYNINJA:

    1. Adaptive Learning Models:
       - Модели для предсказания mastery level
       - Алгоритмы подбора следующего вопроса
       - Personalization engines
       - Difficulty estimation models

    2. Knowledge Graph AI:
       - GNN для recommendation в графе знаний
       - Link prediction для prerequisite relationships
       - Node classification (concept difficulty)
       - Graph-based student modeling

    3. Assessment AI:
       - Automated question generation
       - Difficulty calibration
       - Distractor generation для MCQ
       - Open-ended answer evaluation

    4. Predictive Analytics Models:
       - Early warning системы (dropout prediction)
       - Performance prediction
       - Optimal intervention timing
       - Learning path optimization

    5. NLP для образования:
       - Question understanding
       - Misconception detection
       - Explanation generation
       - Content summarization

    МЕТОДЫ РАБОТЫ:

    1. Model Architecture Design:
       - Анализ требований задачи
       - Literature review текущих подходов
       - Дизайн архитектуры
       - Обоснование выбора компонентов

    2. Experimentation:
       - Baseline models
       - Ablation studies
       - Hyperparameter optimization
       - Сравнение с SOTA

    3. Implementation:
       - PyTorch/TensorFlow реализация
       - Efficient data pipelines
       - Distributed training
       - Model compression

    4. Evaluation & Analysis:
       - Multiple metrics
       - Error analysis
       - Interpretability studies
       - Fairness audits

    РЕЗУЛЬТАТЫ РАБОТЫ:

    1. Model Architecture Documents
       - Детальное описание архитектуры
       - Обоснование дизайна
       - Математические формулировки
       - Диаграммы архитектуры

    2. Training Protocols
       - Hyperparameters
       - Training procedures
       - Data augmentation strategies
       - Regularization techniques

    3. Evaluation Reports
       - Benchmark results
       - Ablation study findings
       - Error analysis
       - Comparison with baselines

    4. Implementation Code
       - Model definitions
       - Training scripts
       - Inference pipelines
       - Unit tests

    5. Deployment Specifications
       - Model serving requirements
       - Latency/throughput targets
       - Monitoring metrics
       - Retraining triggers
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="ML Researcher",
            role="Исследователь машинного обучения и Neural Architectures Specialist",
            expertise=[
                "Deep Learning",
                "Neural Architecture Design",
                "Knowledge Tracing Models",
                "Graph Neural Networks",
                "Transformer Models",
                "Transfer Learning",
                "Few-shot Learning",
                "Meta-Learning",
                "AutoML",
                "Model Optimization",
                "Educational AI Research",
                "NLP for Education",
                "Reinforcement Learning (для adaptive learning)",
            ],
            research_methods=[
                "Architecture Search",
                "Ablation Studies",
                "Hyperparameter Optimization",
                "Cross-validation",
                "Transfer Learning",
                "Curriculum Learning",
                "Active Learning",
                "Model Interpretability Analysis",
                "Fairness Auditing",
                "Benchmark Development",
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Проведение исследования в роли ML Researcher.

        АЛГОРИТМ РАБОТЫ:

        ДЛЯ ЗАДАЧ MODEL_ARCHITECTURE:
        1. Анализ требований и constraints
        2. Literature review SOTA подходов
        3. Дизайн архитектуры
        4. Теоретическое обоснование
        5. Оценка computational complexity
        6. План экспериментов

        ДЛЯ ЗАДАЧ MODEL_TRAINING:
        1. Подготовка данных и pipelines
        2. Выбор hyperparameters (initial)
        3. Дизайн training loop
        4. Мониторинг и логирование
        5. Hyperparameter tuning
        6. Ensemble методы

        ДЛЯ ЗАДАЧ MODEL_EVALUATION:
        1. Определение evaluation metrics
        2. Baseline models
        3. Ablation studies
        4. Error analysis
        5. Fairness evaluation
        6. Interpretability analysis

        ДЛЯ ЗАДАЧ MODEL_OPTIMIZATION:
        1. Profiling bottlenecks
        2. Model compression (pruning, quantization)
        3. Knowledge distillation
        4. Inference optimization
        5. Hardware-aware optimization

        Returns:
            Обновления состояния с ML решениями
        """
        updates: Dict[str, Any] = {
            "messages": [],
        }

        # Запрос контекста по ML подходам
        ml_context = await self.query_knowledge_base(
            query=f"machine learning neural networks educational AI {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        task_instructions = self._get_task_instructions(state.task_type.value)

        user_prompt = f"""
ИССЛЕДОВАТЕЛЬСКАЯ ЗАДАЧА:
Тип: {state.task_type.value}
Вопрос: {state.research_question}

ЦЕЛИ:
{chr(10).join(f"- {obj}" for obj in state.objectives)}

ML КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ:
{chr(10).join(f"- {item.get('text', '')[:150]}..." for item in ml_context[:3])}

ДАННЫЕ ОТ DATA SCIENTIST:
{self._get_data_scientist_context(state)}

{task_instructions}

КРИТИЧНЫЕ ТРЕБОВАНИЯ ДЛЯ STUDYNINJA:
1. Real-time inference (<200ms latency для вопросов)
2. Интерпретируемость - учителя должны понимать рекомендации
3. Fairness - модель не должна дискриминировать группы студентов
4. Privacy - federated learning или differential privacy где возможно
5. Adaptability - быстрая адаптация к новым темам/студентам
6. Robustness - стабильность на out-of-distribution данных
7. Resource efficiency - возможность деплоя на ограниченных ресурсах

ФОРМАТ ОТВЕТА (JSON):
{{
  "architecture_overview": "Общее описание архитектуры",
  "architecture_components": [
    {{
      "component": "название",
      "description": "описание",
      "rationale": "обоснование"
    }}
  ],
  "mathematical_formulation": "Математическое описание модели",
  "training_strategy": {{
    "loss_function": "описание",
    "optimizer": "название и параметры",
    "learning_rate_schedule": "стратегия",
    "regularization": ["метод1", "метод2"],
    "data_augmentation": ["метод1", "метод2"]
  }},
  "hyperparameters": {{
    "param1": "value/range",
    "param2": "value/range"
  }},
  "evaluation_metrics": ["метрика1", "метрика2", ...],
  "baseline_comparisons": ["baseline1", "baseline2", ...],
  "computational_complexity": {{
    "training": "O(...)",
    "inference": "O(...)",
    "memory": "estimate"
  }},
  "expected_performance": "Ожидаемые результаты",
  "ablation_plan": ["что проверить 1", "что проверить 2", ...],
  "risks_and_mitigation": [
    {{"risk": "описание", "mitigation": "стратегия"}}
  ],
  "implementation_roadmap": ["step1", "step2", ...],
  "code_architecture": {{
    "model_class": "# PyTorch/TF code",
    "training_loop": "# pseudocode",
    "inference": "# pseudocode"
  }}
}}
"""

        response = await self.generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
            max_tokens=4500,
        )

        # Создание артефакта
        ml_artifact = await self.create_artifact(
            state=state,
            artifact_type="ml_model_design",
            title=f"ML Model Design: {state.task_type.value}",
            description="Дизайн ML модели от ML Researcher",
            content={
                "design": response,
                "ml_context": ml_context[:3],
            },
            metadata={
                "task_type": state.task_type.value,
                "phase": state.current_phase.value,
            },
        )

        updates["artifacts"] = [ml_artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "phase": state.current_phase.value,
            "message": f"Разработан ML подход для {state.task_type.value}",
            "summary": response[:300] + "..." if len(response) > 300 else response,
        })

        return updates

    def _get_task_instructions(self, task_type: str) -> str:
        """Специфические инструкции по типу задачи"""
        instructions = {
            "model_architecture": """
ЗАДАЧА: ДИЗАЙН АРХИТЕКТУРЫ МОДЕЛИ

РАЗРАБОТАЙТЕ:
1. Архитектуру модели
   - Input representation
   - Core architecture (Transformer/GNN/RNN/etc)
   - Output heads
   - Skip connections, attention mechanisms

2. Теоретическое обоснование
   - Почему эта архитектура подходит для задачи?
   - Inductive biases модели
   - Сравнение с альтернативами

3. Детали реализации
   - Размеры layers
   - Activation functions
   - Normalization strategies
   - Dropout/regularization

4. Computational analysis
   - FLOPs для forward pass
   - Memory requirements
   - Latency estimation
""",
            "model_training": """
ЗАДАЧА: СТРАТЕГИЯ ОБУЧЕНИЯ МОДЕЛИ

ОПРЕДЕЛИТЕ:
1. Training setup
   - Loss function (обоснование)
   - Optimizer и hyperparameters
   - Learning rate schedule
   - Batch size и accumulation

2. Regularization
   - Weight decay
   - Dropout
   - Data augmentation
   - Early stopping criteria

3. Training protocol
   - Number of epochs
   - Validation strategy
   - Checkpoint saving
   - Logging и мониторинг

4. Advanced techniques
   - Transfer learning strategy
   - Curriculum learning
   - Mixed precision training
   - Distributed training (если нужно)
""",
            "model_evaluation": """
ЗАДАЧА: ОЦЕНКА И ВАЛИДАЦИЯ МОДЕЛИ

ПРОВЕДИТЕ:
1. Comprehensive evaluation
   - Multiple metrics (accuracy, F1, AUC, etc)
   - Per-class/per-group analysis
   - Calibration analysis
   - Confidence interval estimation

2. Ablation studies
   - Removal of components
   - Simplification experiments
   - Feature importance

3. Error analysis
   - Confusion matrix analysis
   - Failure case analysis
   - Systematic errors

4. Fairness audit
   - Performance across demographic groups
   - Bias detection
   - Disparate impact analysis

5. Interpretability
   - Attention visualizations
   - Feature importance
   - SHAP/LIME analysis
""",
        }
        return instructions.get(task_type, "ЗАДАЧА: ОБЩАЯ ML РАЗРАБОТКА")

    def _get_data_scientist_context(self, state: ResearchState) -> str:
        """Получение контекста от Data Scientist"""
        data_artifacts = [
            a for a in state.artifacts
            if a.created_by == "Data Scientist" and a.artifact_type == "data_analysis"
        ]

        if not data_artifacts:
            return "Пока нет результатов от Data Scientist"

        latest = data_artifacts[-1]
        return f"Dataset info: {str(latest.content)[:300]}..."


class MLResearcherCritic(ResearchCritic):
    """
    Критик ML Researcher - эксперт по валидации ML решений.

    РОЛЬ:
    - Проверка корректности архитектур
    - Валидация training strategies
    - Оценка evaluation protocols
    - Выявление overfitting и других проблем

    ФОКУСЫ ПРОВЕРКИ:
    1. Architecture soundness
       - Соответствие архитектуры задаче
       - Computational feasibility
       - Potential bottlenecks

    2. Training validity
       - Корректность loss function
       - Адекватность hyperparameters
       - Risk of overfitting/underfitting

    3. Evaluation rigor
       - Comprehensive metrics
       - Proper validation strategy
       - Statistical significance

    4. Reproducibility
       - Seed control
       - Версionирование
       - Документация
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="ML Researcher Critic",
            review_focus=[
                "Архитектурная обоснованность",
                "Training strategy validity",
                "Evaluation comprehensiveness",
                "Computational feasibility",
                "Reproducibility",
            ],
            quality_criteria=[
                "Соответствие SOTA практикам",
                "Теоретическое обоснование",
                "Практическая реализуемость",
                "Comprehensive evaluation",
                "Fairness considerations",
                "Production readiness",
            ],
        )

    async def review_research(
        self,
        state: ResearchState,
        artifact_to_review=None,
    ) -> Dict[str, Any]:
        """Рецензирование ML дизайна"""
        ml_artifacts = [
            a for a in state.artifacts
            if a.created_by == "ML Researcher"
        ]

        if not ml_artifacts:
            return {
                "review_text": "Нет артефактов от ML Researcher",
                "reviewer": self.critic_name,
                "verdict": "PENDING",
            }

        latest_artifact = ml_artifacts[-1]

        review = await self.generate_review(
            content=str(latest_artifact.content),
            focus_areas=[
                "Корректность архитектуры",
                "Обоснованность training strategy",
                "Полнота evaluation план",
                "Feasibility для production",
                "Учет fairness и bias",
            ],
        )

        quality_score = self.get_quality_score(review)

        return {
            **review,
            "quality_score": quality_score,
            "artifact_reviewed": latest_artifact.title,
        }
