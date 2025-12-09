# src/config.py
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file.

    This class is compatible with both pydantic v1 and v2. Required secrets
    are optional at construction time to avoid raising a ValidationError on
    import; callers that need them should validate and raise an appropriate
    error at runtime if a secret is required.
    """

    openai_api_key: Optional[str] = None
    ollama_host: str = "http://localhost:11434"
    redis_host: str = "localhost"
    redis_port: int = 6379
    database_url: Optional[str] = None

    # Pydantic v2: use model_config
    model_config = {"env_file": ".env"}

    # Pydantic v1 compatibility: keep inner Config for older installations
    class Config:
        env_file = ".env"


settings = Settings()
