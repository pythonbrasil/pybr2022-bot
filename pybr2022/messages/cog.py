from typing import Optional

import discord
from discord.ext import commands

from pybr2022.utils import render_template


class MessagesCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        guild: discord.Guild,
        welcome_channel: discord.TextChannel,
    ):
        self.bot = bot
        self._guild = guild
        self._welcome_channel = welcome_channel
        self._channels = None

    async def _get_channel(self, name: str) -> Optional[discord.TextChannel]:
        if not self._channels:
            self._channels = await self._guild.fetch_channels()

        return discord.utils.get(self._channels, name=name)

    @commands.command("boasvindas")
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, *args, **kwargs):
        message = render_template(
            "pybr2022/messages/templates/welcome.md", bot_id=self.bot.application_id
        )
        channel = await self._get_channel(self._welcome_channel)
        await channel.send(message, suppress_embeds=True)
