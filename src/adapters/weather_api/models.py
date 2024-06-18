from __future__ import annotations

from datetime import datetime
from typing import List
from typing import TypedDict

from pydantic import BaseModel

WEATHER_ID_TO_EMOJI = {
    200: "🌩",
    201: "⛈️",
    202: "⛈",
    210: "🌩",
    211: "🌩",
    212: "🌩",
    221: "🌩",
    230: "🌩",
    231: "🌩",
    232: "⛈",
    300: "🌧",
    301: "🌧",
    302: "🌧",
    310: "🌧",
    311: "🌧",
    312: "🌧",
    313: "🌧",
    314: "🌧",
    321: "🌧",
    500: "🌧",
    501: "🌧",
    502: "🌧",
    503: "🌧",
    504: "🌧",
    511: "🌧",
    520: "🌧",
    521: "🌧",
    522: "🌧",
    531: "🌧",
    600: "🌨",
    601: "🌨",
    602: "🌨",
    611: "🌨",
    612: "🌨",
    613: "🌨",
    615: "🌨",
    616: "🌨",
    620: "🌨",
    621: "🌨",
    622: "🌨",
    701: "🌁",
    711: "🌁",
    721: "🌁",
    731: "🌁",
    741: "🌁",
    751: "🌁",
    761: "🌁",
    762: "🌁",
    771: "🌁",
    781: "🌁",
    800: "☀️",
    801: "🌤",
    802: "⛅",
    803: "🌥",
    804: "☁️",
}


def f_to_c(f: float) -> float:
    return (f - 32) * 5.0 / 9.0


def k_to_c(k: float) -> int:
    return int(k - 273.15)


class Weather(BaseModel):
    name: str
    dt: datetime
    emoji: str
    description: str
    feels_like: float

    @classmethod
    def from_response(cls, response: WeatherResponse) -> Weather:
        return cls(
            name=response["name"],
            dt=datetime.fromtimestamp(response["dt"]),
            emoji=WEATHER_ID_TO_EMOJI[response["weather"][0]["id"]],
            description=response["weather"][0]["description"],
            feels_like=k_to_c(response["main"]["feels_like"]),
        )

    @property
    def weather_message(self) -> str:
        if self.dt.hour <= 12:
            time_of_day = "morning"
        elif self.dt.hour <= 18:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"
        weather_emoji = self.emoji
        return f"{weather_emoji} Good {time_of_day}, {self.description} in {self.name} right now, and it feels like {self.feels_like}C {weather_emoji}"


class WeatherCoodResponse(TypedDict):
    lat: float
    lon: float


class WeatherMainResponse(TypedDict):
    feels_like: float
    humidity: int
    pressure: int
    temp: float
    temp_max: int
    temp_min: int


class WeatherSysResponse(TypedDict):
    country: str
    id: int
    sunrise: int
    sunset: int
    type: int


class SubWeatherResponse(TypedDict):
    description: str
    icon: str
    id: int
    main: str


class WeatherWindResponse(TypedDict):
    deg: int
    speed: float


class WeatherResponse(TypedDict):
    base: str
    cod: int
    coord: WeatherCoodResponse
    dt: int
    id: int
    main: WeatherMainResponse
    name: str
    sys: WeatherSysResponse
    timezone: int
    visibility: int
    weather: List[SubWeatherResponse]
    wind: WeatherWindResponse
