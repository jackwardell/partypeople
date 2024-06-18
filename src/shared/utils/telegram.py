def telegram_tag(telegram_api_user_id: int, name: str) -> str:
    return f"<a href=tg://user?id={telegram_api_user_id}>{name}</a>"
