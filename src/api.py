import datetime

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from src.adapters.telegram_api.api import TelegramAPI
from src.app import App
from src.app import BotSlashCommand
from src.shared.db.api import EntryNotFound
from src.shared.utils.insults import get_insult
from src.shared.utils.telegram import telegram_tag
from src.shared.utils.time import get_utc_now

app = App()


@app.schedule("0 * * * *")
async def update_fixtures() -> None:
    await app.ingest_fixtures()


@app.schedule("30 * * * *")
async def update_players() -> None:
    await app.ingest_players()


@app.schedule("0 10 * * *")
async def morning_message() -> None:
    date_context = await app.get_date_context(get_utc_now())
    await app.telegram_api.send_chat_message("Good morning party people, here are the today's matches 👇")
    await app.telegram_api.send_chat_message(date_context.morning_message)


@app.schedule("0 22 * * *")
async def evening_message() -> None:
    date_context = await app.get_date_context(get_utc_now())
    await app.telegram_api.send_chat_message("Good evening party people, here are the today's results 👇")
    await app.telegram_api.send_chat_message(date_context.evening_message)


@app.on_command(BotSlashCommand.INSULT, description="get a random insult, or tag someone to insult them")
async def insult(_: TelegramAPI, message: Message) -> None:
    if len(message.command) > 1 and len(message.entities) > 1:
        if message.entities[1].type == MessageEntityType.TEXT_MENTION:
            await message.reply(
                f"{telegram_tag(message.entities[1].user.id, message.entities[1].user.first_name)} "
                f"you are a {get_insult()}"
            )
            return

    await message.reply(get_insult())


@app.on_command(BotSlashCommand.MY_TEAMS, description="see your teams")
async def my_teams(_: TelegramAPI, message: Message) -> None:
    user_context = await app.get_user_context(message.from_user.id)
    await message.reply(user_context.teams_message)


@app.on_command(BotSlashCommand.MY_MATCHES, description="see your upcoming matches")
async def my_matches(_: TelegramAPI, message: Message) -> None:
    user_context = await app.get_user_context(message.from_user.id)
    await message.reply(user_context.matches_message)


@app.on_command(BotSlashCommand.MATCHES_TODAY, description="see all matches today")
async def matches_today(_: TelegramAPI, message: Message) -> None:
    date_context = await app.get_date_context(get_utc_now().date())
    await message.reply(date_context.message)


@app.on_command(BotSlashCommand.MATCHES_TOMORROW, description="see all matches tomorrow")
async def matches_tomorrow(_: TelegramAPI, message: Message) -> None:
    date_context = await app.get_date_context(get_utc_now().date() + datetime.timedelta(days=1))
    await message.reply(date_context.message)


@app.on_command(BotSlashCommand.CATEGORIES, description="see sweepstake categories")
async def categories(_: TelegramAPI, message: Message) -> None:
    sweepstake_context = await app.get_sweepstake_context()
    await message.reply(sweepstake_context.message)


@app.on_command(BotSlashCommand.WHO_HAS, description="see who has what team")
async def who_has(_: TelegramAPI, message: Message) -> None:
    try:
        team_name = message.command[1].title()
        user = await app.database_api.get_user_by_team_name(team_name)
        await message.reply(f"{user.telegram_tag} has {team_name}")
    except IndexError:
        await message.reply("Please provide a team name (and spell it properly)")
    except EntryNotFound:
        await message.reply(f"Nobody has {team_name}")


if __name__ == "__main__":
    app.run_forever()
