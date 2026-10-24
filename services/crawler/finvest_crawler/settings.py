from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Crawler config from env / .env (FINVEST_ prefix). Never print it: database_url is hidden from repr."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FINVEST_", extra="ignore")

    data_dir: Path = Path("data")  # raw archive lives at data_dir/raw (F-020/A12)
    database_url: str = Field("postgresql+psycopg://finvest:finvest@localhost:5432/finvest", repr=False)
    source_ticks: str = "kbs"
    source_symbols: str = "vci"
    source_bars: str = "vci"
    source_snapshot: str = "ssi"
    user_agent: str = "finvest-personal/0.1 (+learning tool, single user)"
    retention_days: int | None = None  # None = keep everything (F-020)
    rate_per_s: dict[str, float] = {"kbs": 2, "vci": 2, "ssi": 1}
