import datetime
from enum import StrEnum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from pyrogram import filters
from pyrogram.types import BotCommand

from src.adapters.football_api.api import FootballAPI
from src.adapters.football_api.api import get_football_api
from src.adapters.telegram_api.api import TelegramAPI
from src.adapters.telegram_api.api import get_telegram_api

# from src.adapters.weather_api.api import OWeatherAPI
# from src.adapters.weather_api.api import get_oweather_api
from src.shared.db.api import DatabaseAPI
from src.shared.db.api import get_database_api
from src.shared.models import DateContext
from src.shared.models import FixtureContext
from src.shared.models import SweepstakeCategory
from src.shared.models import SweepstakeCategoryIDEnum
from src.shared.models import SweepstakeContext
from src.shared.models import UserContext
from src.shared.utils.hardcoded import TELEGRAM_USER_ID_TO_FOOTBALL_API_TEAM_IDS


class BotSlashCommand(StrEnum):
    INSULT = "insult"
    # WEATHER = "weather"

    MY_TEAMS = "myteams"
    MY_MATCHES = "mymatches"
    MY_PAST_MATCHES = "mypastmatches"

    MATCHES_TODAY = "matchestoday"
    MATCHES_TOMORROW = "matchestomorrow"
    MATCHES_YESTERDAY = "matchesyesterday"

    INGEST_FIXTURES = "ingestfixtures"
    INGEST_PLAYERS = "ingestplayers"

    CATEGORIES = "categories"

    WHO_HAS = "whohas"


class App:
    scheduler: AsyncIOScheduler

    bot_commands: list[BotCommand]

    # oweather_api: OWeatherAPI
    football_api: FootballAPI
    telegram_api: TelegramAPI
    database_api: DatabaseAPI

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()

        self.bot_commands = []

        # self.oweather_api = get_oweather_api()
        self.telegram_api = get_telegram_api()
        self.football_api = get_football_api()
        self.database_api = get_database_api()

    def schedule(self, cron_expression: str) -> callable:

        def decorator(func: callable) -> callable:
            self.scheduler.add_job(func, CronTrigger.from_crontab(cron_expression, timezone="UTC"))
            return func

        return decorator

    def on_command(self, command: BotSlashCommand, description: str = "") -> callable:
        self.bot_commands.append(BotCommand(command, description))

        def decorator(func: callable) -> callable:
            self.telegram_api.on_message(filters.command(command))(func)
            return func

        return decorator

    async def setup_bot_commands(self) -> None:
        await self.telegram_api.add_bot_commands(self.bot_commands)

    async def ingest_users(self) -> None:
        logger.info("ingesting users...")
        for user in await self.telegram_api.get_chat_users():
            await self.database_api.add_user_from_pyrogram_user(user)
        logger.info("users ingested")

    async def ingest_teams(self) -> None:
        logger.info("ingesting teams...")
        for team in await self.football_api.get_teams():
            await self.database_api.add_team_from_football_api_team_response(team)
        logger.info("teams ingested")

    async def ingest_draws(self) -> None:
        logger.info("ingesting draws...")
        for user_id, team_ids in TELEGRAM_USER_ID_TO_FOOTBALL_API_TEAM_IDS.items():
            for team_id in team_ids:
                await self.database_api.add_draw(telegram_api_user_id=user_id, football_api_team_id=team_id)
        logger.info("draws ingested")

    async def ingest_fixtures(self) -> None:
        logger.info("ingesting fixtures...")
        for fixture in await self.football_api.get_fixtures():
            await self.database_api.add_fixture_from_football_api_fixture_response(fixture)
        logger.info("fixtures ingested")

    async def ingest_players(self) -> None:
        logger.info("ingesting players...")
        for player in await self.football_api.get_players():
            await self.database_api.add_player_from_football_api_player_response(player)
        logger.info("ingested players")

    async def on_startup(self) -> None:
        logger.info("starting up...")
        await self.ingest_users()
        await self.ingest_teams()
        await self.ingest_draws()
        await self.ingest_fixtures()
        await self.ingest_players()
        logger.info("started up")

    async def get_sweepstake_context(self) -> SweepstakeContext:
        logger.info("getting sweepstake context...")
        return SweepstakeContext(
            categories=[
                await self.get_first_place(),
                await self.get_second_place(),
                await self.get_worst_team(),
                await self.get_filthiest_team(),
                await self.get_team_with_biggest_loss(),
                await self.get_youngest_goal_scorer(),
                await self.get_oldest_goal_scorer(),
            ]
        )

    async def get_first_place(self) -> SweepstakeCategory:
        return SweepstakeCategory(
            id=SweepstakeCategoryIDEnum.FIRST_PLACE,
            prize_money=20,
            team=None,
            user=None,
        )

    async def get_second_place(self) -> SweepstakeCategory:
        return SweepstakeCategory(
            id=SweepstakeCategoryIDEnum.SECOND_PLACE,
            prize_money=10,
            team=None,
            user=None,
        )

    async def get_worst_team(self) -> SweepstakeCategory:
        teams_results_map = {
            team.football_api_team_id: {
                "team": team,
                "losses": 0,
                "goals_conceded": 0,
            }
            for team in await self.database_api.get_teams()
        }

        for fixture in await self.database_api.get_completed_fixtures():
            teams_results_map[fixture.home_team_football_api_team_id]["goals_conceded"] += fixture.away_team_goals or 0
            teams_results_map[fixture.away_team_football_api_team_id]["goals_conceded"] += fixture.home_team_goals or 0
            teams_results_map[fixture.home_team_football_api_team_id]["losses"] += 1 if fixture.away_team_winner else 0
            teams_results_map[fixture.away_team_football_api_team_id]["losses"] += 1 if fixture.home_team_winner else 0

        losses = 0
        worst_teams_results1 = []
        for team, results_map in teams_results_map.items():
            if results_map["losses"] > losses:
                losses = results_map["losses"]
                worst_teams_results1 = [results_map]
            elif results_map["losses"] == losses:
                worst_teams_results1.append(results_map)

        goals_conceded = 0
        worst_teams_results2 = []
        for team, results_map in teams_results_map.items():
            if results_map["goals_conceded"] > goals_conceded:
                goals_conceded = results_map["goals_conceded"]
                worst_teams_results2 = [results_map]
            elif results_map["goals_conceded"] == goals_conceded:
                worst_teams_results2.append(results_map)

        worst_team_football_api_team_ids = {i["team"].football_api_team_id for i in worst_teams_results1} & {
            j["team"].football_api_team_id for j in worst_teams_results2
        }
        assert len(worst_team_football_api_team_ids) == 1
        worst_team_football_api_team_id = worst_team_football_api_team_ids.pop()

        return SweepstakeCategory(
            id=SweepstakeCategoryIDEnum.WORST_TEAM,
            prize_money=5,
            team=teams_results_map[worst_team_football_api_team_id]["team"],
            user=await self.database_api.get_user_by_football_api_team_id(worst_team_football_api_team_id),
            data=(
                f"Lost {teams_results_map[worst_team_football_api_team_id]['losses']} games "
                f"and conceded {teams_results_map[worst_team_football_api_team_id]['goals_conceded']} goals"
            ),
        )

    async def get_filthiest_team(self) -> SweepstakeCategory:
        teams_results_map = {
            team.football_api_team_id: {
                "team": team,
                "yellows": 0,
                "reds": 0,
                "yellows_then_red": 0,
                "total": 0,
            }
            for team in await self.database_api.get_teams()
        }

        for player in await self.database_api.get_players():
            teams_results_map[player.football_api_team_id]["yellows"] += player.yellow_cards or 0
            teams_results_map[player.football_api_team_id]["reds"] += player.red_cards or 0
            teams_results_map[player.football_api_team_id]["yellows_then_red"] += player.yellow_then_red_cards or 0

        for team, results_map in teams_results_map.items():
            results_map["total"] = (
                (results_map["yellows"] * 1) + (results_map["yellows_then_red"] * 2) + (results_map["reds"] * 3)
            )

        worst_team_map = sorted(list(teams_results_map.values()), key=lambda x: x["total"], reverse=True)[0]

        return SweepstakeCategory(
            id=SweepstakeCategoryIDEnum.FILTHIEST_TEAM,
            prize_money=10,
            team=worst_team_map["team"],
            user=await self.database_api.get_user_by_football_api_team_id(worst_team_map["team"].football_api_team_id),
            data=(
                f"Players given {worst_team_map['yellows']} yellow cards, "
                f"{worst_team_map['yellows_then_red']} yellows then reds and {worst_team_map['reds']} red cards"
            ),
        )

    async def get_team_with_biggest_loss(self) -> SweepstakeCategory:
        teams_results_map = {
            team.football_api_team_id: {
                "team": team,
                "losses": [],
            }
            for team in await self.database_api.get_teams()
        }

        for fixture in await self.database_api.get_completed_fixtures():
            if fixture.home_team_winner:
                teams_results_map[fixture.away_team_football_api_team_id]["losses"].append(fixture)
            if fixture.away_team_winner:
                teams_results_map[fixture.home_team_football_api_team_id]["losses"].append(fixture)

        worst_goal_difference = 0
        best_goals_totals = 0
        team_with_biggest_loss = None
        fixture_with_biggest_loss = None
        for team, results_map in teams_results_map.items():
            for fixture in results_map["losses"]:
                goal_difference = abs((fixture.home_team_goals or 0) - (fixture.away_team_goals or 0))
                goals_total = (fixture.home_team_goals or 0) + (fixture.away_team_goals or 0)
                if goal_difference >= worst_goal_difference and goals_total >= best_goals_totals:
                    worst_goal_difference = goal_difference
                    best_goals_totals = goals_total
                    team_with_biggest_loss = results_map["team"]
                    fixture_with_biggest_loss = fixture

        winning_team_name = (
            fixture_with_biggest_loss.home_team
            if fixture_with_biggest_loss.home_team_winner
            else fixture_with_biggest_loss.away_team
        )
        winning_team_goals = (
            fixture_with_biggest_loss.home_team_goals
            if fixture_with_biggest_loss.home_team_winner
            else fixture_with_biggest_loss.away_team_goals
        )
        losing_team_name = (
            fixture_with_biggest_loss.home_team
            if fixture_with_biggest_loss.away_team_winner
            else fixture_with_biggest_loss.away_team
        )
        losing_team_goals = (
            fixture_with_biggest_loss.home_team_goals
            if fixture_with_biggest_loss.away_team_winner
            else fixture_with_biggest_loss.away_team_goals
        )

        return SweepstakeCategory(
            id=SweepstakeCategoryIDEnum.TEAM_WITH_BIGGEST_LOSS,
            prize_money=5,
            team=team_with_biggest_loss,
            user=await self.database_api.get_user_by_football_api_team_id(team_with_biggest_loss.football_api_team_id),
            data=f"{winning_team_name} thrashed {losing_team_name} {winning_team_goals}-{losing_team_goals}",
        )

    async def get_youngest_goal_scorer(self) -> SweepstakeCategory:
        player = await self.database_api.get_youngest_goalscorer_player()
        return SweepstakeCategory(
            id=SweepstakeCategoryIDEnum.YOUNGEST_GOALSCORER,
            prize_money=5,
            team=await self.database_api.get_team_by_football_api_team_id(player.football_api_team_id),
            user=await self.database_api.get_user_by_football_api_team_id(player.football_api_team_id),
            data=f"{player.first_name} {player.last_name} born on {player.date_of_birth} is a goalscorer",
        )

    async def get_oldest_goal_scorer(self) -> SweepstakeCategory:
        player = await self.database_api.get_oldest_goalscorer_player()
        return SweepstakeCategory(
            id=SweepstakeCategoryIDEnum.OLDEST_GOALSCORER,
            prize_money=5,
            team=await self.database_api.get_team_by_football_api_team_id(player.football_api_team_id),
            user=await self.database_api.get_user_by_football_api_team_id(player.football_api_team_id),
            data=f"{player.first_name} {player.last_name} born on {player.date_of_birth} is a goalscorer",
        )

    async def get_fixture_context(self, football_api_fixture_id: int) -> FixtureContext:
        logger.info(f"getting fixture context: {football_api_fixture_id=}...")
        fixture = await self.database_api.get_fixture_by_football_api_fixture_id(football_api_fixture_id)
        fixture_context = FixtureContext(
            fixture=fixture,
            home_user=await self.database_api.get_user_by_football_api_team_id(fixture.home_team_football_api_team_id),
            away_user=await self.database_api.get_user_by_football_api_team_id(fixture.away_team_football_api_team_id),
            home_team=await self.database_api.get_team_by_football_api_team_id(fixture.home_team_football_api_team_id),
            away_team=await self.database_api.get_team_by_football_api_team_id(fixture.away_team_football_api_team_id),
        )
        return fixture_context

    async def get_date_context(self, date: datetime.date) -> DateContext:
        logger.info(f"getting date context: {date=}...")
        date_context = DateContext(
            date=date,
            fixture_contexts=[
                await self.get_fixture_context(fixture.football_api_fixture_id)
                for fixture in await self.database_api.get_fixtures_by_date(date)
            ],
        )
        return date_context

    async def get_user_context(self, telegram_api_user_id: int) -> UserContext:
        logger.info(f"getting date context: {telegram_api_user_id=}...")
        user_context = UserContext(
            user=await self.database_api.get_user_by_telegram_api_user_id(telegram_api_user_id),
            teams=await self.database_api.get_teams_by_telegram_api_user_id(telegram_api_user_id),
            fixture_contexts=[
                await self.get_fixture_context(football_api_fixture_id)
                for football_api_fixture_id in await self.database_api.get_football_api_fixture_ids_by_telegram_api_user_id(
                    telegram_api_user_id
                )
            ],
        )
        return user_context

    def run_forever(self) -> None:
        logger.info("running forever...")
        self.scheduler.start()
        logger.info("scheduler started")
        # self.telegram_api.run(self.on_startup())
        # self.telegram_api.run(self.setup_bot_commands())
        logger.info("running api")
        self.telegram_api.run()
        logger.info("finishing...")
