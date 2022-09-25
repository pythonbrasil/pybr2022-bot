import discord
from discord.ext import commands

from .eventbrite import EventBrite
from .index import AttendeesIndex


class AuthenticationCog(commands.Cog):
    def __init__(
        self, bot: commands.Bot, event_id: str, eventbrite_api_token: str
    ) -> None:
        self.bot = bot
        self.attendees_index = AttendeesIndex()
        self.eventbrite = EventBrite(event_id, eventbrite_api_token)

    async def _load_attendees(self):
        last_update = self.attendees_index.updated_at
        new_attendees = await self.eventbrite.list_attendees(last_update)
        for attendee in new_attendees:
            self.attendees_index.add(attendee)
