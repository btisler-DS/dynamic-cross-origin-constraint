"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"


class Settings(BaseSettings):
    app_name: str = "Project Synapse"
    debug: bool = False
    database_url: str = f"sqlite:///{(_DATA_DIR / 'synapse.db').as_posix()}"
    data_dir: str = str(_DATA_DIR)
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    default_seed: int = 42
    max_concurrent_runs: int = 2

    model_config = {"env_prefix": "SYNAPSE_"}


settings = Settings()
