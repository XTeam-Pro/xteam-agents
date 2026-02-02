"""Embedding provider using LangChain."""

import structlog
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from xteam_agents.config import LLMProvider, Settings

logger = structlog.get_logger()


class EmbeddingProvider:
    """
    Provides text embeddings using LangChain.

    Supports OpenAI embeddings (Anthropic doesn't have an embedding model,
    so we always use OpenAI for embeddings even when using Anthropic for LLM).
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._embeddings: Embeddings | None = None

    @property
    def embeddings(self) -> Embeddings:
        """Get embeddings instance, creating if needed."""
        if self._embeddings is None:
            self._embeddings = self._create_embeddings()
        return self._embeddings

    def _create_embeddings(self) -> Embeddings:
        """Create the embeddings instance."""
        # Always use OpenAI for embeddings
        api_key = None
        if self.settings.openai_api_key:
            api_key = self.settings.openai_api_key.get_secret_value()
        elif self.settings.llm_provider == LLMProvider.OPENAI:
            raise ValueError("OpenAI API key required for embeddings")

        if api_key is None:
            raise ValueError(
                "OpenAI API key required for embeddings. "
                "Set OPENAI_API_KEY even when using Anthropic for LLM."
            )

        embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            api_key=api_key,
            dimensions=self.settings.embedding_dimensions,
        )

        logger.info(
            "embedding_provider_initialized",
            model=self.settings.embedding_model,
            dimensions=self.settings.embedding_dimensions,
        )

        return embeddings

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Embedding vector as list of floats
        """
        embedding = await self.embeddings.aembed_query(text)
        return embedding

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = await self.embeddings.aembed_documents(texts)
        return embeddings

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.settings.embedding_dimensions
