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
    nanobanana_api_key: str | None = None

    jwt_secret: str = "dev-secret-change-me"


settings = Settings()
