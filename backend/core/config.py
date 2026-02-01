"""
Configuration management for commander.ai
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: str = "postgresql+asyncpg://commander:changeme@localhost:5432/commander_ai"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "commander_ai_memories"

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-ada-002"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000

    # Application Configuration
    app_env: str = "development"
    app_debug: bool = True
    app_log_level: str = "INFO"
    app_secret_key: str

    # WebSocket Configuration
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100

    # Memory Configuration
    stm_ttl_seconds: int = 3600  # 1 hour
    ltm_similarity_threshold: float = 0.7
    memory_consolidation_interval: int = 3600  # Run every hour

    # Agent Configuration
    max_consultation_depth: int = 3  # Prevent infinite consultation loops
    agent_timeout_seconds: int = 300  # 5 minutes
    task_queue_size: int = 1000

    # MVP Configuration
    mvp_user_id: str = "00000000-0000-0000-0000-000000000001"

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    cors_allow_credentials: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
