import asyncio
from datetime import datetime,timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks
from loguru import logger

from pybr2022 import config
from pybr2022.utils import render_template
from .pretalx import Pretalx
from .models import Talk


DISCORD_ROOMS = {
    "aruanã": config.DISCORD_ROOM_ARUANA,
    "tucunare": config.DISCORD_ROOM_TUCUNARE,
    "jaraqui": config.DISCORD_ROOM_JARAQUI,
    "keynote": config.DISCORD_ROOM_KEYNOTE,
}


class TalksCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        guild: discord.Guild,
        pretalx_client: Pretalx,
    ) -> None:
        self.bot = bot
        self.pretalx = pretalx_client
        self._guild = guild
        self._attendee_role = None

    def _filter_talks_next_hour(self, talks: list[Talk]) -> list[Talk]:
        return [
            talk for talk in talks
            if talk.start_in_30_min
        ]

    def _filter_talks_per_type(self, talks: list[Talk]) -> list[Talk]:
        return [
            talk for talk in talks
            if talk.type.lower() in ["palestra", "palestra relâmpago", "keynote"]
        ]

    def _next_talk_message(self, talk: Talk) -> str:
        params = {
            "title": talk.title,
            "pretalx_link": talk.pretalx,
            "youtube_link": talk.youtube,
        }
        if talk.is_keynote:
            template = "pybr2022/talks/templates/next_talk_keynote.md"
        else:
            template = "pybr2022/talks/templates/next_talk.md"
            params["speaker"] = talk.speaker

        return render_template(template, **params)

    async def _publish_talks_in_channels(self, talks: list[Talk], test_channel=None):
        for talk in talks:
            room_id = DISCORD_ROOMS.get(talk.room.lower())
            logger.info(f"Publishing next schedule. room={room_id}")
            channel = await self._guild.fetch_channel(room_id)

            message = self._next_talk_message(talk)
            await channel.send(message, suppress_embeds=True)

    @commands.command("palestras")
    @commands.has_permissions(manage_guild=True)
    async def talks(
        self,
        context: commands.Context,
        *args,
    ):
        channel = context.message.channel if args else None
        talks = await self.pretalx.talks()
        talks = self._filter_talks_per_type(talks)
        talks = self._filter_talks_next_hour(talks)
        await self._publish_talks_in_channels(talks, channel)