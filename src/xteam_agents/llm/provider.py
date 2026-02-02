"""Configurable LLM provider using LangChain."""

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from xteam_agents.config import LLMProvider as LLMProviderEnum
from xteam_agents.config import Settings

logger = structlog.get_logger()


class LLMProvider:
    """
    Provides configurable LLM instances.

    Supports OpenAI and Anthropic models through LangChain.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: BaseChatModel | None = None

    @property
    def model(self) -> BaseChatModel:
        """Get the LLM model instance, creating if needed."""
        if self._model is None:
            self._model = self._create_model()
        return self._model

    def _create_model(self) -> BaseChatModel:
        """Create the appropriate LLM model based on settings."""
        if self.settings.llm_provider == LLMProviderEnum.OPENAI:
            return self._create_openai_model()
        elif self.settings.llm_provider == LLMProviderEnum.ANTHROPIC:
            return self._create_anthropic_model()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")

    def _create_openai_model(self) -> ChatOpenAI:
        """Create OpenAI chat model."""
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required")

        model = ChatOpenAI(
            model=self.settings.llm_model,
            api_key=self.settings.openai_api_key.get_secret_value(),
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
        )

        logger.info(
            "llm_provider_initialized",
            provider="openai",
            model=self.settings.llm_model,
        )

        return model

    def _create_anthropic_model(self) -> ChatAnthropic:
        """Create Anthropic chat model."""
        if not self.settings.anthropic_api_key:
            raise ValueError("Anthropic API key is required")

        model = ChatAnthropic(
            model=self.settings.llm_model,
            api_key=self.settings.anthropic_api_key.get_secret_value(),
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
        )

        logger.info(
            "llm_provider_initialized",
            provider="anthropic",
            model=self.settings.llm_model,
        )

        return model

    def get_model_with_tools(self, tools: list) -> BaseChatModel:
        """
        Get model bound with tools.

        Args:
            tools: List of LangChain tools to bind

        Returns:
            Model with tools bound
        """
        return self.model.bind_tools(tools)

    def get_model_for_agent(self, agent_name: str) -> BaseChatModel:
        """
        Get model for a specific agent.
        
        Can handle standard agents or dynamic personas.
        """
        # For now, all agents use the same model
        # Could extend to support different models per agent or specific configs for personas
        return self.model
