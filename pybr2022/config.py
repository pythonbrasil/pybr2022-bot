from pathlib import Path

from decouple import config

DISCORD_TOKEN = config("DISCORD_TOKEN")
DISCORD_SERVER_ID = config("DISCORD_SERVER_ID")
DISCORD_ATTENTEE_ROLE_NAME = config("DISCORD_ATTENTEE_ROLE_NAME")

EVENTBRITE_TOKEN = config("EVENTBRITE_TOKEN")
EVENTBRITE_EVENT_ID = config("EVENTBRITE_EVENT_ID")

ATTENDEES_INDEX_CACHE = config(
    "ATTENDEES_INDEX_CACHE", default="/tmp/cache.json", cast=Path
)
