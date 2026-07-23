"""系统配置 — 基于 pydantic-settings。"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "供应链多智能体协同管理系统"
    app_env: str = "dev"
    database_url: str = (
        "mysql+pymysql://root:@127.0.0.1:2881/supply_chain_multi_agent?charset=utf8mb4"
    )
    sqlite_fallback_url: str = "sqlite:///./schema/supply_chain.db"
    database_connect_timeout_seconds: int = 3
    example_data_dir: str = "./example"

    llm_provider: str = "deepseek"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    deepseek_api_key: SecretStr | None = Field(
        default=None, validation_alias="DEEPSEEK_API_KEY", repr=False
    )
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2

    cache_ttl_seconds: int = 60
    auth_secret_key: SecretStr = Field(
        default=SecretStr("course-demo-change-me-with-32-plus-bytes"),
        validation_alias="AUTH_SECRET_KEY",
        repr=False,
    )
    auth_token_ttl_seconds: int = 28800

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def database_path(self) -> Path:
        if not self.database_url.startswith("sqlite"):
            raise ValueError("database_path is only available for SQLite")
        raw = self.database_url.replace("sqlite:///", "", 1)
        return (BASE_DIR / raw.replace("./", "", 1)).resolve()

    @property
    def deepseek_api_key_value(self) -> str:
        return self.deepseek_api_key.get_secret_value() if self.deepseek_api_key else ""

    @property
    def auth_secret_key_value(self) -> str:
        return self.auth_secret_key.get_secret_value()

    @property
    def example_dir_path(self) -> Path:
        """示例数据 JSON 文件所在目录（绝对路径）。"""
        return (BASE_DIR / self.example_data_dir.replace("./", "", 1)).resolve()

    @property
    def schema_dir_path(self) -> Path:
        """数据库 schema 导出目录（绝对路径）。"""
        return (BASE_DIR / "schema").resolve()

    def resolve_sqlite_path(self, database_url: str) -> Path:
        """将 SQLite URL 解析为绝对文件路径。"""
        raw = database_url.replace("sqlite:///", "", 1)
        return (BASE_DIR / raw.replace("./", "", 1)).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
