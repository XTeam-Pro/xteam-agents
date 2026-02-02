"""Configuration management using Pydantic Settings."""

from enum import Enum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider to use (openai or anthropic)",
    )
    openai_api_key: SecretStr | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: SecretStr | None = Field(default=None, description="Anthropic API key")
    llm_model: str = Field(
        default="gpt-4o",
        description="Model name (e.g., gpt-4o, claude-3-5-sonnet-20241022)",
    )
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, ge=1)

    # Redis Configuration (Episodic Memory)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for episodic memory",
    )
    redis_key_prefix: str = Field(default="xteam:")

    # Qdrant Configuration (Semantic Memory)
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant connection URL for semantic memory",
    )
    qdrant_collection: str = Field(default="xteam_semantic")
    qdrant_api_key: SecretStr | None = Field(default=None)

    # Neo4j Configuration (Procedural Memory)
    neo4j_url: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URL for procedural memory",
    )
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: SecretStr = Field(default=SecretStr("password"))
    neo4j_database: str = Field(default="neo4j")

    # PostgreSQL Configuration (Audit Log)
    postgres_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/xteam",
        description="PostgreSQL connection URL for audit log",
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name",
    )
    embedding_dimensions: int = Field(default=1536)

    # Server Configuration
    server_host: str = Field(default="0.0.0.0")
    server_port: int = Field(default=8000)

    # Task Configuration
    task_timeout_seconds: int = Field(default=300, ge=1)
    max_retries: int = Field(default=3, ge=0)
    max_replan_iterations: int = Field(default=3, ge=1)

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_json: bool = Field(default=True)

    # n8n Integration
    n8n_url: str | None = Field(default=None, description="n8n webhook URL")
    n8n_api_key: SecretStr | None = Field(default=None)

    def get_llm_api_key(self) -> str:
        """Get the API key for the configured LLM provider."""
        if self.llm_provider == LLMProvider.OPENAI:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
            return self.openai_api_key.get_secret_value()
        else:
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic provider")
            return self.anthropic_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
