"""Configuration management for ESPN Fantasy Hockey."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

DEFAULT_YEAR = 2026


def load_config() -> "ESPNConfig":
    """Load configuration from environment variables.

    Looks for .env file in current directory or parent directories.
    """
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

    load_dotenv(env_path)

    year_str = os.environ.get("ESPN_YEAR")
    year = int(year_str) if year_str else DEFAULT_YEAR

    return ESPNConfig(
        league_id=int(os.environ["ESPN_LEAGUE_ID"]),
        swid=os.environ["ESPN_SWID"],
        espn_s2=os.environ["ESPN_S2"],
        year=year,
    )


class ESPNConfig(BaseModel):
    """ESPN API configuration."""

    league_id: int = Field(description="ESPN Fantasy League ID")
    swid: str = Field(description="ESPN SWID cookie value")
    espn_s2: str = Field(description="ESPN S2 cookie value")
    year: int = Field(default=DEFAULT_YEAR, description="Season year")
