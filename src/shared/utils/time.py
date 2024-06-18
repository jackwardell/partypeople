import datetime


def get_utc_now() -> datetime.datetime:
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


def date_to_str(date: datetime.date) -> str:
    if date == get_utc_now().date():
        return "Today"
    elif date == get_utc_now().date() + datetime.timedelta(days=1):
        return "Tomorrow"
    else:
        return date.strftime("%a %b %d")
