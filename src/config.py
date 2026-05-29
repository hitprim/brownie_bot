from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = ""
    webhook_secret: str = ""

    base_url: str = "http://localhost:8000"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/domovoy"

    groq_api_key: str = ""
    openrouter_api_key: str = ""

    llm_model: str = "deepseek/deepseek-chat"
    llm_fallback_model: str = "anthropic/claude-3.5-haiku"

    langsmith_api_key: str = ""
    langsmith_project: str = "domovoy"
    langchain_tracing_v2: bool = False

    debug: bool = False
    log_level: str = "INFO"

    @property
    def webhook_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/webhook"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
