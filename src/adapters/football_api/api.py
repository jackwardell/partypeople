from __future__ import annotations

import asyncio
from datetime import date
from enum import IntEnum
from enum import StrEnum
from functools import lru_cache
from typing import Any

import httpx
from httpx import Headers
from httpx import Timeout

from src.adapters.football_api.models import GETFixturesEventResponse
from src.adapters.football_api.models import GETFixturesResponse
from src.adapters.football_api.models import GETPlayerResponse
from src.adapters.football_api.models import GETTeamInformationResponse
from src.config import get_config


class FootballAPILeagueID(IntEnum):
    EUROS = 4


class FootballAPISeasonID(IntEnum):
    EUROS_2024 = 2024


class FootballAPIEndpoints(StrEnum):
    FIXTURES = "/fixtures"
    TEAMS = "/teams"
    PLAYERS = "/players"
    FIXTURES_EVENTS = "/fixtures/events"
    STANDINGS = "/standings"


@lru_cache
def get_football_api() -> FootballAPI:
    return FootballAPI()


class FootballAPI:
    league_id: FootballAPILeagueID
    season_id: FootballAPISeasonID

    api_url: str
    timeout: Timeout
    headers: Headers

    def __init__(self) -> None:
        self.league_id = FootballAPILeagueID.EUROS
        self.season_id = FootballAPISeasonID.EUROS_2024

        self.api_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.timeout = Timeout(30)
        self.headers = Headers(
            {
                "X-RapidAPI-Key": get_config().FOOTBALL_API_KEY,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
            }
        )

    # @retry(stop=stop_after_attempt(5), wait=wait_fixed(2), retry=retry_if_exception_type(HTTPError))
    async def get(
        self,
        url_endpoint: FootballAPIEndpoints,
        params: dict[str, str | int],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            resp = await client.get(self.api_url + url_endpoint, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_teams(self) -> list[GETTeamInformationResponse]:
        params = {"league": self.league_id, "season": self.season_id}
        response = await self.get(FootballAPIEndpoints.TEAMS, params=params)
        return response["response"]

    async def get_fixtures(self, today_only: bool = False) -> list[GETFixturesResponse]:
        params = {"league": self.league_id, "season": self.season_id}
        if today_only:
            params["from"] = str(date.today())
            params["to"] = str(date.today())
        response = await self.get(FootballAPIEndpoints.FIXTURES, params=params)
        return response["response"]

    async def get_fixture_events(self, fixture_football_api_id: int) -> list[GETFixturesEventResponse]:
        params = {"fixture": fixture_football_api_id}
        response = await self.get(FootballAPIEndpoints.FIXTURES_EVENTS, params=params)
        return response["response"]

    async def get_players(self) -> list[GETPlayerResponse]:
        current_page = 1
        end_page = 1_000_000
        players = []
        while current_page <= end_page:
            params = {"league": self.league_id, "season": self.season_id, "page": current_page}
            response = await self.get(FootballAPIEndpoints.PLAYERS, params=params)
            end_page = response["paging"]["total"]
            players.extend([p for p in response["response"]])
            current_page += 1
            await asyncio.sleep(3)
        return players
