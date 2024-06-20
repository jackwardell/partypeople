from __future__ import annotations

from pyrogram import Client
from pyrogram.types import BotCommand
from pyrogram.types import Message
from pyrogram.types import User

from src.config import get_config


def get_telegram_api() -> TelegramAPI:
    return TelegramAPI()


class TelegramAPI(Client):
    def __init__(self) -> None:
        super().__init__(
            name="party_people_zyning_bot",
            api_id=get_config().TELEGRAM_API_ID,
            api_hash=get_config().TELEGRAM_API_HASH,
            bot_token=get_config().TELEGRAM_BOT_TOKEN,
        )

    async def get_chat_users(self) -> list[User]:
        members = []
        async with self as app:
            async for member in app.get_chat_members(get_config().TELEGRAM_CHAT_ID):
                members.append(member.user)
        return members

    async def send_chat_message(self, message: str) -> Message:
        return await self.send_message(get_config().TELEGRAM_CHAT_ID, message)

    async def add_bot_commands(self, bot_commands: list[BotCommand]) -> None:
        async with self as app:
            await app.set_bot_commands(bot_commands)
