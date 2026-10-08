from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAFESITO_", env_file=".env", extra="ignore")

    database_path: Path = PROJECT_ROOT / "data" / "cafesito.db"
    sales_csv_path: Path = PROJECT_ROOT / "data" / "raw" / "coffee_shop_sales.csv"
    models_dir: Path = PROJECT_ROOT / "models"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
