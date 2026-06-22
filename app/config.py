from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cohere_api_key: str = ""
    database_url: str = "postgresql+asyncpg://psap:psap@localhost:5432/psap_rag"
    redis_url: str = "redis://localhost:6379/0"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"
    llm_provider: str = "cohere"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
