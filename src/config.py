from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

root = Path(__file__).parent.parent
load_dotenv(root / ".env")


class Config(BaseSettings):
    TELEGRAM_BOT_TOKEN: Annotated[str, Field()]
    TELEGRAM_API_ID: Annotated[str, Field()]
    TELEGRAM_API_HASH: Annotated[str, Field()]
    TELEGRAM_CHAT_ID: Annotated[int, Field()]
    FOOTBALL_API_KEY: Annotated[str, Field()]
    POSTGRES_URL: Annotated[str, Field()]
    OPEN_WEATHER_MAP_API_KEY: Annotated[str, Field()]

    @property
    def async_postgres_url(self) -> str:
        return self.POSTGRES_URL.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache
def get_config() -> Config:
    return Config()
