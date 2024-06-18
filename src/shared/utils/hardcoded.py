import json
from pathlib import Path

with open(Path(__file__).parent / "hardcoded.json") as f:
    TELEGRAM_USER_ID_TO_FOOTBALL_API_TEAM_IDS = {int(i): j for i, j in json.load(f)}
