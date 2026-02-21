from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    app_name: str = "Trendr"
    api_prefix: str = "/v1"

    database_url: str

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str
    celery_result_backend: str

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    nanobanana_api_key: str | None = None
    text_provider_default: str = "openai"
    text_provider_fallbacks: str = "openai_stub"

    jwt_secret: str = "dev-secret-change-me"
    secrets_encryption_key: str | None = None

    @property
    def text_provider_fallback_list(self) -> list[str]:
        return [item.strip() for item in self.text_provider_fallbacks.split(",") if item.strip()]


settings = Settings()
