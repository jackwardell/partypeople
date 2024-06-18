from __future__ import annotations

import datetime
from pyrogram.types import User as PyrogramUser
from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.adapters.football_api.models import GETFixturesResponse
from src.adapters.football_api.models import GETPlayerResponse
from src.adapters.football_api.models import GETTeamInformationResponse
from src.shared.models import Draw
from src.shared.models import Fixture
from src.shared.models import Player
from src.shared.models import Team
from src.shared.models import User


class BaseTable(DeclarativeBase):
    pass


class UserTable(BaseTable):
    __tablename__ = "user"

    telegram_api_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None]

    @classmethod
    def from_pyrogram_user(cls, user: PyrogramUser) -> UserTable:
        return cls(
            telegram_api_user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
        )

    def to_model(self) -> User:
        return User.model_validate(self, from_attributes=True)


class TeamTable(BaseTable):
    __tablename__ = "team"

    football_api_team_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    code: Mapped[str]

    @classmethod
    def from_football_api_team_response(cls, response: GETTeamInformationResponse) -> TeamTable:
        return cls(
            football_api_team_id=response["team"]["id"],
            name=response["team"]["name"],
            code=response["team"]["code"],
        )

    def to_model(self) -> Team:
        return Team.model_validate(self, from_attributes=True)


class DrawTable(BaseTable):
    __tablename__ = "draw"

    telegram_api_user_id: Mapped[int] = mapped_column(ForeignKey("user.telegram_api_user_id"), primary_key=True)
    football_api_team_id: Mapped[int] = mapped_column(ForeignKey("team.football_api_team_id"), primary_key=True)

    def to_model(self) -> Draw:
        return Draw.model_validate(self, from_attributes=True)


class PlayerTable(BaseTable):
    __tablename__ = "player"

    football_api_player_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    date_of_birth: Mapped[datetime.date]
    football_api_team_id: Mapped[int] = mapped_column(ForeignKey("team.football_api_team_id"))
    yellow_cards: Mapped[int | None]
    yellow_then_red_cards: Mapped[int | None]
    red_cards: Mapped[int | None]
    goals: Mapped[int | None]

    @classmethod
    def from_football_api_player_response(cls, response: GETPlayerResponse) -> PlayerTable:
        return cls(
            football_api_player_id=response["player"]["id"],
            first_name=response["player"]["firstname"],
            last_name=response["player"]["lastname"],
            date_of_birth=datetime.date.fromisoformat(response["player"]["birth"]["date"]),
            football_api_team_id=response["statistics"][0]["team"]["id"],
            yellow_cards=response["statistics"][0]["cards"]["yellow"],
            yellow_then_red_cards=response["statistics"][0]["cards"]["yellowred"],
            red_cards=response["statistics"][0]["cards"]["red"],
            goals=response["statistics"][0]["goals"]["total"],
        )

    def to_model(self) -> Player:
        return Player.model_validate(self, from_attributes=True)


#
class FixtureTable(BaseTable):
    __tablename__ = "fixture"

    football_api_fixture_id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str]
    home_team_football_api_team_id: Mapped[int] = mapped_column(ForeignKey("team.football_api_team_id"))
    away_team_football_api_team_id: Mapped[int] = mapped_column(ForeignKey("team.football_api_team_id"))
    home_team: Mapped[str]
    away_team: Mapped[str]
    home_team_goals: Mapped[int | None]
    away_team_goals: Mapped[int | None]
    home_team_winner: Mapped[bool | None]
    away_team_winner: Mapped[bool | None]
    kick_off: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    venue_city: Mapped[str]
    venue_name: Mapped[str]
    round: Mapped[str]
    home_goals_half_time: Mapped[int | None]
    away_goals_half_time: Mapped[int | None]
    home_goals_full_time: Mapped[int | None]
    away_goals_full_time: Mapped[int | None]
    away_goals_extra_time: Mapped[int | None]
    home_goals_extra_time: Mapped[int | None]
    home_goals_penalties: Mapped[int | None]
    away_goals_penalties: Mapped[int | None]

    @classmethod
    def from_football_api_fixture_response(cls, response: GETFixturesResponse) -> FixtureTable:
        return cls(
            football_api_fixture_id=response["fixture"]["id"],
            status=response["fixture"]["status"]["short"],
            home_team_football_api_team_id=response["teams"]["home"]["id"],
            away_team_football_api_team_id=response["teams"]["away"]["id"],
            home_team=response["teams"]["home"]["name"],
            away_team=response["teams"]["away"]["name"],
            home_team_goals=response["goals"]["home"],
            away_team_goals=response["goals"]["away"],
            home_team_winner=response["teams"]["home"]["winner"],
            away_team_winner=response["teams"]["away"]["winner"],
            kick_off=datetime.datetime.fromisoformat(response["fixture"]["date"]),
            venue_city=response["fixture"]["venue"]["city"],
            venue_name=response["fixture"]["venue"]["name"],
            round=response["league"]["round"],
            home_goals_half_time=response["score"]["halftime"]["home"],
            away_goals_half_time=response["score"]["halftime"]["away"],
            home_goals_full_time=response["score"]["fulltime"]["home"],
            away_goals_full_time=response["score"]["fulltime"]["away"],
            away_goals_extra_time=response["score"]["extratime"]["away"],
            home_goals_extra_time=response["score"]["extratime"]["home"],
            home_goals_penalties=response["score"]["penalty"]["home"],
            away_goals_penalties=response["score"]["penalty"]["away"],
        )

    def to_model(self) -> Fixture:
        return Fixture.model_validate(self, from_attributes=True)
