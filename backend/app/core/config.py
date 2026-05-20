from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "供应链库存协同与智能补货管理系统"
    app_env: str = "dev"
    database_url: str = "sqlite:///./schema/supply_chain.db"
    example_data_dir: str = "./example"

    llm_provider: str = "rule"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2

    cache_ttl_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        raw = self.database_url.replace("sqlite:///", "", 1)
        return (BASE_DIR / raw.replace("./", "", 1)).resolve()

    @property
    def example_dir_path(self) -> Path:
        return (BASE_DIR / self.example_data_dir.replace("./", "", 1)).resolve()

    @property
    def schema_dir_path(self) -> Path:
        return self.database_path.parent


@lru_cache
def get_settings() -> Settings:
    return Settings()
