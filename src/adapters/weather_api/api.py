from __future__ import annotations

from functools import lru_cache

import httpx

from src.adapters.weather_api.models import Weather
from src.config import get_config

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


@lru_cache
def get_oweather_api() -> OWeatherAPI:
    return OWeatherAPI()


class OWeatherAPI:
    @classmethod
    async def get_weather_in(cls, location: str) -> Weather:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                WEATHER_URL,
                params={"q": location, "appid": get_config().OPEN_WEATHER_MAP_API_KEY},
            )
        return Weather.from_response(response.json())
