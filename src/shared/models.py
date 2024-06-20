from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel
from pydantic import Field

from src.shared.utils.emoji import COUNTRIES_TO_FLAGS_MAP
from src.shared.utils.insults import get_insult
from src.shared.utils.telegram import telegram_tag
from src.shared.utils.time import date_to_str


class SweepstakeCategoryIDEnum(StrEnum):
    FIRST_PLACE = "First place"
    SECOND_PLACE = "Second place"
    WORST_TEAM = "Worst team"
    FILTHIEST_TEAM = "Filthiest team"
    TEAM_WITH_BIGGEST_LOSS = "Biggest loss"
    YOUNGEST_GOALSCORER = "Youngest goalscorer"
    OLDEST_GOALSCORER = "Oldest goalscorer"


class SweepstakeCategory(BaseModel):
    id: Annotated[SweepstakeCategoryIDEnum, Field()]
    prize_money: Annotated[int, Field()]
    team: Annotated[Team | None, Field()] = None
    user: Annotated[User | None, Field()] = None
    data: Annotated[str | None, Field()] = None

    @property
    def message(self) -> str:
        return (
            "🏆 {id} 🏆\n"
            "🎁 Prize: £{prize_money} 💰\n"
            "👥 Participant: {user_telegram_tag} 🎉\n"
            "🤝 Team: {team_name} {team_emoji}\n"
            "{data}"
        ).format(
            id=self.id,
            prize_money=self.prize_money,
            user_telegram_tag=self.user.telegram_tag if self.user else "TBD",
            team_name=self.team.name if self.team else "TBD",
            team_emoji=self.team.emoji if self.team else "",
            data=f"📊 Data: {self.data} ℹ️\n" if self.data else "",
        )


class SweepstakeContext(BaseModel):
    categories: list[SweepstakeCategory]

    @property
    def message(self) -> str:
        return "\n".join([c.message for c in self.categories])


def get_verb(score1: int, score2: int) -> str:
    if score1 == score2:
        return "drew with"
    if score1 > score2:
        return "beat"
    return "lost to"


class FixtureStatusEnum(StrEnum):
    TO_BE_DEFINED = "TBD"
    NOT_STARTED = "NS"
    FIRST_HALF = "1H"
    HALF_TIME = "HT"
    SECOND_HALF = "2H"
    EXTRA_TIME = "ET"
    BREAK_TIME = "BT"
    PENALTIES = "P"
    MATCH_SUSPENDED = "SUSP"
    MATCH_INTERRUPTED = "INT"
    FULL_TIME = "FT"
    FULL_TIME_AFTER_ET = "AET"
    FULL_TIME_AFTER_PENALTIES = "PEN"
    MATCH_POSTPONED = "PST"
    MATCH_CANCELLED = "CANC"
    MATCH_ABANDONED = "ABD"
    TECHNICAL_LOSS = "AWD"
    WALK_OVER = "WO"
    LIVE = "LIVE"

    @classmethod
    def not_started(cls) -> list[FixtureStatusEnum]:
        return [cls.TO_BE_DEFINED, cls.NOT_STARTED]

    @classmethod
    def in_progress(cls) -> list[FixtureStatusEnum]:
        return [
            cls.FIRST_HALF,
            cls.HALF_TIME,
            cls.SECOND_HALF,
            cls.EXTRA_TIME,
            cls.BREAK_TIME,
            cls.PENALTIES,
            cls.LIVE,
        ]

    @classmethod
    def is_finished(cls) -> list[FixtureStatusEnum]:
        return [
            cls.FULL_TIME,
            cls.FULL_TIME_AFTER_ET,
            cls.FULL_TIME_AFTER_PENALTIES,
            cls.TECHNICAL_LOSS,
            cls.WALK_OVER,
        ]


class DateContext(BaseModel):
    date: datetime.date
    fixture_contexts: list[FixtureContext]

    @property
    def message(self) -> str:
        if self.fixture_contexts:
            return "\n\n".join([fc.message for fc in self.fixture_contexts])
        else:
            return f"No fixtures {date_to_str(self.date)}"

    @property
    def morning_message(self) -> str:
        if self.fixture_contexts:
            return "\n\n".join([fc.not_started_message for fc in self.fixture_contexts])
        else:
            return f"No fixtures {date_to_str(self.date)}"

    @property
    def evening_message(self) -> str:
        if self.fixture_contexts:
            return "\n\n".join([fc.is_finished_message for fc in self.fixture_contexts])
        else:
            return f"No fixtures {date_to_str(self.date)}"


class UserContext(BaseModel):
    user: User
    teams: list[Team]
    fixture_contexts: list[FixtureContext]

    @property
    def teams_message(self) -> str:
        if self.teams:
            return "You have: " + " & ".join([t.country_and_emoji for t in self.teams])
        else:
            return f"You have no teams you fucking {get_insult()}"

    @property
    def matches_message(self) -> str:
        fixture_contexts = [fc for fc in self.fixture_contexts if fc.fixture.status in FixtureStatusEnum.not_started()]
        if fixture_contexts:
            return "You have:\n" + "\n\n".join([fc.not_started_message for fc in fixture_contexts])
        else:
            return f"You have no matches you fucking {get_insult()}"

    @property
    def past_matches_message(self) -> str:
        fixture_contexts = [fc for fc in self.fixture_contexts if fc.fixture.status in FixtureStatusEnum.is_finished()]
        if fixture_contexts:
            return "You played:\n" + "\n\n".join([fc.is_finished_message for fc in fixture_contexts])
        else:
            return f"You have no matches you fucking {get_insult()}"

    @property
    def not_started_fixture_contexts(self) -> list[FixtureContext]:
        return [fc for fc in self.fixture_contexts if fc.fixture.status in FixtureStatusEnum.not_started()]

    @property
    def in_progress_fixture_contexts(self) -> list[FixtureContext]:
        return [fc for fc in self.fixture_contexts if fc.fixture.status in FixtureStatusEnum.in_progress()]

    @property
    def is_finished_fixture_contexts(self) -> list[FixtureContext]:
        return [fc for fc in self.fixture_contexts if fc.fixture.status in FixtureStatusEnum.is_finished()]


class FixtureContext(BaseModel):
    fixture: Fixture
    home_user: User
    away_user: User
    home_team: Team
    away_team: Team

    @property
    def is_draw(self) -> bool:
        return not self.fixture.home_team_winner and not self.fixture.away_team_winner

    @property
    def winning_or_home_team(self) -> Team | None:
        if self.fixture.home_team_winner is True:
            return self.home_team
        if self.fixture.away_team_winner is True:
            return self.away_team
        return self.home_team

    @property
    def losing_or_away_team(self) -> Team | None:
        if self.fixture.home_team_winner is False:
            return self.home_team
        if self.fixture.away_team_winner is False:
            return self.away_team
        return self.away_team

    @property
    def winning_or_home_user(self) -> User | None:
        if self.fixture.home_team_winner is True:
            return self.home_user
        if self.fixture.away_team_winner is True:
            return self.away_user
        return self.home_user

    @property
    def losing_or_away_user(self) -> User | None:
        if self.fixture.home_team_winner is False:
            return self.home_user
        if self.fixture.away_team_winner is False:
            return self.away_user
        return self.away_user

    @property
    def winning_or_home_team_goals(self) -> int | None:
        if self.winning_or_home_team.football_api_team_id == self.fixture.home_team_football_api_team_id:
            return self.fixture.home_team_goals
        if self.winning_or_home_team.football_api_team_id == self.fixture.away_team_football_api_team_id:
            return self.fixture.away_team_goals
        return self.fixture.home_team_goals

    @property
    def losing_or_away_teams_goals(self) -> int | None:
        if self.losing_or_away_team.football_api_team_id == self.fixture.home_team_football_api_team_id:
            return self.fixture.home_team_goals
        if self.losing_or_away_team.football_api_team_id == self.fixture.away_team_football_api_team_id:
            return self.fixture.away_team_goals
        return self.fixture.away_team_goals

    @property
    def not_started_message(self) -> str:
        return (
            "🤝 Teams: {home_team_name} {home_team_emoji} play {away_team_name} {away_team_emoji}\n"
            "🏟️ Stadium: {venue_name} in {venue_city} 🧑‍🤝‍🧑\n"
            "🦵 Kick Off: {kick_off_time} {kick_off_date} ⏱️\n"
            "🔢 Round: {round} 💫\n"
            "⚔️ Rivals: {home_user_telegram_tag} vs. {away_user_telegram_tag} 😈"
        ).format(
            home_team_name=self.home_team.name,
            home_team_emoji=self.home_team.emoji,
            away_team_name=self.away_team.name,
            away_team_emoji=self.away_team.emoji,
            venue_name=self.fixture.venue_name,
            venue_city=self.fixture.venue_city,
            kick_off_time=self.fixture.kick_off.time(),
            kick_off_date=date_to_str(self.fixture.kick_off.date()),
            round=self.fixture.round,
            home_user_telegram_tag=self.home_user.telegram_tag,
            away_user_telegram_tag=self.away_user.telegram_tag,
        )

    @property
    def in_progress_message(self) -> str:
        return (
            "🤝 Teams: {home_team_name} {home_team_emoji} are playing {away_team_name} {away_team_emoji} now\n"
            "🏟️ Score: {home_team_goals}-{away_team_goals} 🧑‍🤝‍🧑\n"
            "🔢 Round: {round} 💫\n"
            "⚔️ Rivals: {home_user_telegram_tag} vs. {away_user_telegram_tag} 😈"
        ).format(
            home_team_name=self.home_team.name,
            home_team_emoji=self.home_team.emoji,
            away_team_name=self.away_team.name,
            away_team_emoji=self.away_team.emoji,
            home_team_goals=self.fixture.home_team_goals,
            away_team_goals=self.fixture.away_team_goals,
            round=self.fixture.round,
            home_user_telegram_tag=self.home_user.telegram_tag,
            away_user_telegram_tag=self.away_user.telegram_tag,
        )

    @property
    def is_finished_message(self) -> str:
        return (
            "🏆 Teams: {winning_team_name} {winning_team_emoji} {verb} {losing_team_name} {losing_team_emoji} ✨\n"
            "🏟️ Score: {winning_team_goals}-{losing_team_goals} 🧑‍🤝‍🧑\n"
            "🔢 Round: {round} 💫\n"
            "🎉 Well done {winning_user_telegram_tag} and get rekt {losing_user_telegram_tag} 💀"
        ).format(
            winning_team_name=self.winning_or_home_team.name,
            winning_team_emoji=self.winning_or_home_team.emoji,
            winning_team_goals=self.winning_or_home_team_goals,
            verb=f"<i>{get_insult()}ed</i>" if not self.is_draw else "drew with",
            losing_team_name=self.losing_or_away_team.name,
            losing_team_emoji=self.losing_or_away_team.emoji,
            losing_team_goals=self.losing_or_away_teams_goals,
            round=self.fixture.round,
            winning_user_telegram_tag=self.winning_or_home_user.telegram_tag,
            losing_user_telegram_tag=self.losing_or_away_user.telegram_tag,
        )

    @property
    def message(self) -> str:
        if self.fixture.status in FixtureStatusEnum.is_finished():
            return self.is_finished_message
        if self.fixture.status in FixtureStatusEnum.in_progress():
            return self.in_progress_message
        return self.not_started_message


class User(BaseModel):
    telegram_api_user_id: Annotated[int, Field()]
    first_name: Annotated[str, Field()]
    last_name: Annotated[str | None, Field()]
    username: Annotated[str | None, Field()]

    @property
    def telegram_tag(self) -> str:
        return telegram_tag(self.telegram_api_user_id, self.first_name)


class Team(BaseModel):
    football_api_team_id: Annotated[int, Field()]
    name: Annotated[str, Field()]
    code: Annotated[str, Field()]

    @property
    def emoji(self) -> str:
        return COUNTRIES_TO_FLAGS_MAP[self.name]

    @property
    def country_and_emoji(self) -> str:
        return f"{self.emoji} {self.name} {self.emoji}"


class Draw(BaseModel):
    telegram_api_user_id: Annotated[int, Field()]
    football_api_team_id: Annotated[int, Field()]


class Player(BaseModel):
    football_api_player_id: int
    first_name: str
    last_name: str
    date_of_birth: datetime.date
    football_api_team_id: int
    yellow_cards: int | None
    yellow_then_red_cards: int | None
    red_cards: int | None
    goals: int | None

    @property
    def force_yellow_cards(self) -> int:
        return self.yellow_cards or 0

    @property
    def force_yellow_then_red_cards(self) -> int:
        return self.yellow_then_red_cards or 0

    @property
    def force_red_cards(self) -> int:
        return self.red_cards or 0


class Fixture(BaseModel):
    football_api_fixture_id: Annotated[int, Field()]
    status: Annotated[FixtureStatusEnum, Field()]
    home_team_football_api_team_id: Annotated[int, Field()]
    away_team_football_api_team_id: Annotated[int, Field()]
    home_team: Annotated[str, Field()]
    away_team: Annotated[str, Field()]
    home_team_goals: Annotated[int | None, Field()]
    away_team_goals: Annotated[int | None, Field()]
    home_team_winner: Annotated[bool | None, Field()]
    away_team_winner: Annotated[bool | None, Field()]
    kick_off: Annotated[datetime.datetime, Field()]
    venue_city: Annotated[str, Field()]
    venue_name: Annotated[str, Field()]
    round: Annotated[str, Field()]
    home_goals_half_time: Annotated[int | None, Field()]
    away_goals_half_time: Annotated[int | None, Field()]
    home_goals_full_time: Annotated[int | None, Field()]
    away_goals_full_time: Annotated[int | None, Field()]
    away_goals_extra_time: Annotated[int | None, Field()]
    home_goals_extra_time: Annotated[int | None, Field()]
    home_goals_penalties: Annotated[int | None, Field()]
    away_goals_penalties: Annotated[int | None, Field()]
