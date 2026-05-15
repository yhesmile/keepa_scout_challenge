from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Keepa Scout'
    app_env: str = Field(default='development', alias='APP_ENV')
    host: str = Field(default='0.0.0.0', alias='HOST')
    port: int = Field(default=8000, alias='PORT')
    db_path: str = Field(default='data/scout.db', alias='DB_PATH')
    keepa_api_keys: str = Field(default='', alias='KEEPA_API_KEYS')
    keepa_domain: int = Field(default=1, alias='KEEPA_DOMAIN')
    keepa_base_url: str = Field(default='https://api.keepa.com', alias='KEEPA_BASE_URL')
    keepa_batch_size: int = Field(default=50, alias='KEEPA_BATCH_SIZE')
    llm_provider: str = Field(default='openai-compatible', alias='LLM_PROVIDER')
    llm_model: str = Field(default='gpt-4o-mini', alias='LLM_MODEL')
    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    openai_base_url: str | None = Field(default=None, alias='OPENAI_BASE_URL')
    deepseek_api_key: str | None = Field(default=None, alias='DEEPSEEK_API_KEY')
    moonshot_api_key: str | None = Field(default=None, alias='MOONSHOT_API_KEY')

    @property
    def database_url(self) -> str:
        db_file = Path(self.db_path)
        if not db_file.is_absolute():
            db_file = Path.cwd() / db_file
        db_file.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_file.as_posix()}"

    @property
    def keepa_keys(self) -> list[str]:
        return [key.strip() for key in self.keepa_api_keys.split(',') if key.strip()]

    def get_openai_credentials(self) -> tuple[str | None, str | None]:
        if self.openai_api_key:
            return self.openai_api_key, self.openai_base_url
        if self.deepseek_api_key:
            return self.deepseek_api_key, 'https://api.deepseek.com/v1'
        if self.moonshot_api_key:
            return self.moonshot_api_key, 'https://api.moonshot.cn/v1'
        return None, self.openai_base_url

    @property
    def resolved_llm_model(self) -> str:
        default_model = (self.llm_model or '').strip()
        if self.deepseek_api_key and default_model in {'', 'gpt-4o-mini'}:
            return 'deepseek-chat'
        if self.moonshot_api_key and default_model in {'', 'gpt-4o-mini'}:
            return 'moonshot-v1-8k'
        return default_model or 'gpt-4o-mini'


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
