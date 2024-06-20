from __future__ import annotations

import datetime
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator

from pyrogram.types import User as PyrogramUser
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import aliased
from sqlalchemy.orm import sessionmaker

from src.adapters.football_api.models import GETFixturesResponse
from src.adapters.football_api.models import GETPlayerResponse
from src.adapters.football_api.models import GETTeamInformationResponse
from src.config import get_config
from src.shared.models import Fixture
from src.shared.models import FixtureStatusEnum
from src.shared.models import Player
from src.shared.models import Team
from src.shared.models import User
from src.shared.tables import DrawTable
from src.shared.tables import FixtureTable
from src.shared.tables import PlayerTable
from src.shared.tables import TeamTable
from src.shared.tables import UserTable


@lru_cache
def get_session_factory() -> sessionmaker:
    engine = create_async_engine(get_config().async_postgres_url)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.flush()
            await session.rollback()
            raise e
        finally:
            await session.close()


@lru_cache
def get_database_api() -> DatabaseAPI:
    return DatabaseAPI()


class EntryNotSaved(Exception): ...


class EntryNotFound(Exception): ...


class DatabaseAPI:
    @staticmethod
    async def add_user_from_pyrogram_user(user: PyrogramUser) -> None:
        async with get_session() as session:
            try:
                session.add(UserTable.from_pyrogram_user(user))
                await session.commit()
            except IntegrityError:
                await session.flush()
                await session.rollback()
                query = (
                    update(UserTable)
                    .where(UserTable.telegram_api_user_id == user.id)
                    .values(first_name=user.first_name, last_name=user.last_name, username=user.username)
                )
                await session.execute(query)
                await session.commit()

    @staticmethod
    async def add_team_from_football_api_team_response(response: GETTeamInformationResponse) -> None:
        async with get_session() as session:
            try:
                session.add(TeamTable.from_football_api_team_response(response))
                await session.commit()
            except IntegrityError:
                pass

    @staticmethod
    async def add_draw(telegram_api_user_id: int, football_api_team_id: int) -> None:
        async with get_session() as session:
            try:
                session.add(
                    DrawTable(telegram_api_user_id=telegram_api_user_id, football_api_team_id=football_api_team_id)
                )
                await session.commit()
            except IntegrityError:
                pass

    @staticmethod
    async def add_fixture_from_football_api_fixture_response(response: GETFixturesResponse) -> None:
        async with get_session() as session:
            try:
                session.add(FixtureTable.from_football_api_fixture_response(response))
                await session.commit()
            except IntegrityError:
                await session.flush()
                await session.rollback()
                query = (
                    update(FixtureTable)
                    .where(FixtureTable.football_api_fixture_id == response["fixture"]["id"])
                    .values(
                        status=response["fixture"]["status"]["short"],
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
                )
                await session.execute(query)
                await session.commit()

    @staticmethod
    async def add_player_from_football_api_player_response(response: GETPlayerResponse) -> None:
        async with get_session() as session:
            try:
                session.add(PlayerTable.from_football_api_player_response(response))
                await session.commit()
            except IntegrityError:
                await session.flush()
                await session.rollback()
                query = (
                    update(PlayerTable)
                    .where(PlayerTable.football_api_player_id == response["player"]["id"])
                    .values(
                        yellow_cards=response["statistics"][0]["cards"]["yellow"],
                        yellow_then_red_cards=response["statistics"][0]["cards"]["yellowred"],
                        red_cards=response["statistics"][0]["cards"]["red"],
                        goals=response["statistics"][0]["goals"]["total"],
                    )
                )
                await session.execute(query)
                await session.commit()

    @staticmethod
    async def get_user_by_telegram_api_user_id(telegram_api_user_id: int) -> User:
        async with get_session() as session:
            query = select(UserTable).where(UserTable.telegram_api_user_id == telegram_api_user_id)
            return (await session.execute(query)).scalar().to_model()

    @staticmethod
    async def get_user_by_football_api_team_id(football_api_team_id: int) -> User:
        async with get_session() as session:
            query = (
                select(UserTable)
                .join(DrawTable, DrawTable.telegram_api_user_id == UserTable.telegram_api_user_id)
                .where(DrawTable.football_api_team_id == football_api_team_id)
            )
            return (await session.execute(query)).scalar().to_model()

    @staticmethod
    async def get_teams_by_telegram_api_user_id(telegram_api_user_id: int) -> list[Team]:
        async with get_session() as session:
            query = (
                select(TeamTable)
                .join(DrawTable, DrawTable.football_api_team_id == TeamTable.football_api_team_id)
                .where(DrawTable.telegram_api_user_id == telegram_api_user_id)
                .order_by(TeamTable.name)
            )
            return [entry.to_model() for entry in (await session.execute(query)).scalars()]

    @staticmethod
    async def get_fixture_by_football_api_fixture_id(football_api_fixture_id: int) -> Fixture:
        async with get_session() as session:
            query = select(FixtureTable).where(FixtureTable.football_api_fixture_id == football_api_fixture_id)
            return (await session.execute(query)).scalar().to_model()

    @staticmethod
    async def get_team_by_football_api_team_id(football_api_team_id: int) -> Team:
        async with get_session() as session:
            query = select(TeamTable).where(TeamTable.football_api_team_id == football_api_team_id)
            return (await session.execute(query)).scalar().to_model()

    @staticmethod
    async def get_football_api_fixture_ids_by_telegram_api_user_id(telegram_api_user_id: int) -> list[int]:
        draw1 = aliased(DrawTable)
        draw2 = aliased(DrawTable)
        async with get_session() as session:
            query = (
                select(FixtureTable.football_api_fixture_id)
                .join(draw1, draw1.football_api_team_id == FixtureTable.home_team_football_api_team_id)
                .join(draw2, draw2.football_api_team_id == FixtureTable.away_team_football_api_team_id)
                .where(
                    or_(
                        draw1.telegram_api_user_id == telegram_api_user_id,
                        draw2.football_api_team_id == telegram_api_user_id,
                    )
                )
            )
            return [entry for entry in (await session.execute(query)).scalars()]

    @staticmethod
    async def get_fixtures_by_date(date: datetime.date) -> list[Fixture]:
        async with get_session() as session:
            query = (
                select(FixtureTable).where(func.DATE(FixtureTable.kick_off) == date).order_by(FixtureTable.kick_off)
            )
            return [entry.to_model() for entry in (await session.execute(query)).scalars()]

    @staticmethod
    async def get_completed_fixtures() -> list[Fixture]:
        async with get_session() as session:
            query = (
                select(FixtureTable)
                .where(FixtureTable.status.in_(FixtureStatusEnum.is_finished()))
                .order_by(FixtureTable.kick_off)
            )
            return [entry.to_model() for entry in (await session.execute(query)).scalars()]

    @staticmethod
    async def get_teams() -> list[Team]:
        async with get_session() as session:
            query = select(TeamTable).order_by(TeamTable.name)
            return [entry.to_model() for entry in (await session.execute(query)).scalars()]

    @staticmethod
    async def get_players() -> list[Player]:
        async with get_session() as session:
            query = select(PlayerTable).order_by(PlayerTable.football_api_team_id)
            return [entry.to_model() for entry in (await session.execute(query)).scalars()]

    @staticmethod
    async def get_youngest_goalscorer_player() -> Player:
        async with get_session() as session:
            query = (
                select(PlayerTable)
                .where(
                    and_(
                        PlayerTable.goals.isnot(None),
                        PlayerTable.goals != 0,
                    )
                )
                .order_by(PlayerTable.date_of_birth.desc())
                .limit(1)
            )
            return (await session.execute(query)).scalar().to_model()

    @staticmethod
    async def get_oldest_goalscorer_player() -> Player:
        async with get_session() as session:
            query = (
                select(PlayerTable)
                .where(
                    and_(
                        PlayerTable.goals.isnot(None),
                        PlayerTable.goals != 0,
                    )
                )
                .order_by(PlayerTable.date_of_birth)
                .limit(1)
            )
            return (await session.execute(query)).scalar().to_model()

    @staticmethod
    async def get_user_by_team_name(name: str) -> User:
        async with get_session() as session:
            query = (
                select(UserTable)
                .join(DrawTable, DrawTable.telegram_api_user_id == UserTable.telegram_api_user_id)
                .join(TeamTable, DrawTable.football_api_team_id == TeamTable.football_api_team_id)
                .where(TeamTable.name == name)
            )
            try:
                return (await session.execute(query)).scalar().to_model()
            except AttributeError:
                raise EntryNotFound(f"{name} not found")
