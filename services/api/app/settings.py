from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    project_name: str = "Contextual Document Assistant"
    environment: str = "development"
    debug: bool = False
    api_version: str = "v1"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False

    # AI Providers
    openai_api_key: SecretStr | None = None
    huggingface_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    # Pinecone
    pinecone_api_key: SecretStr | None = None
    pinecone_index: str | None = None
    pinecone_region: str | None = None

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service Endpoints
    vector_db_url: str | None = None
    embeddings_url: str | None = None
    llm_url: str | None = None


settings = Settings()