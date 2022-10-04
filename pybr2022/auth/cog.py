from typing import Optional

import discord
from discord.ext import commands, tasks
from loguru import logger

from .eventbrite import EventBrite
from .index import AttendeesIndex


def render_template(template_path: str, **kwargs):
    with open(template_path) as fp:
        text = fp.read().format(**kwargs)
        return text


class AuthenticationCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        event_brite_client: EventBrite,
        attendees_index: AttendeesIndex,
        server_id: str,
        attendee_role_name: str,
    ) -> None:
        self.bot = bot
        self.attendees_index = attendees_index
        self.eventbrite = event_brite_client
        self._server_id = server_id
        self._attendee_role_name = attendee_role_name
        self._server = None
        self._attendee_role = None
        self._start_tasks()

    def _start_tasks(self):
        self._load_attendees.start()

    @tasks.loop(minutes=5)
    async def _load_attendees(self):
        last_update = self.attendees_index.updated_at
        new_attendees = await self.eventbrite.list_attendees(last_update)
        for attendee in new_attendees:
            self.attendees_index.add(attendee)

    async def _get_server(self) -> discord.Guild:
        if not self._server:
            self._server = await self.bot.fetch_guild(self._server_id)

        return self._server

    def _is_private_message(self, message: discord.Message) -> bool:
        conditions = (
            not message.author.bot,
            message.channel.type == discord.ChannelType.private,
        )
        return all(conditions)

    async def _get_user_from_server(
        self, user: discord.Member
    ) -> Optional[discord.Member]:
        server = await self._get_server()
        return await server.fetch_member(user.id)

    async def _is_auth_needed(self, user: discord.Member) -> bool:
        return len(user.roles) == 1

    async def _get_attendee_role(self):
        if not self._attendee_role:
            server = await self._get_server()
            roles = await server.fetch_roles()
            self._attendee_role = discord.utils.get(
                roles, name=self._attendee_role_name
            )

        return self._attendee_role

    async def _set_attendee_role(self, member: discord.Member):
        attendee_role = await self._get_attendee_role()
        await member.add_roles(attendee_role)

    async def authenticate(self, message: discord.Message):
        if not self._is_private_message(message):
            return

        user = await self._get_user_from_server(message.author)
        if not user:
            await message.author.send("join server first")
            return

        if not await self._is_auth_needed(user):
            reply = render_template(
                "pybr2022/auth/templates/user_already_authenticated.md",
                user_id=message.author.id,
            )
            await message.author.send(reply)
            return

        if self.attendees_index.search(message.content):
            logger.info(
                f"User authenticated. author={message.author!r}, message={message.content!r}"
            )
            await self._set_attendee_role(user)
            reply = render_template("pybr2022/auth/templates/authenticated.md")
            await message.author.send(reply)
        else:
            logger.warning(
                f"Failed to authenticate user. author={message.author!r}, message={message.content!r}"
            )
            reply = render_template(
                "pybr2022/auth/templates/auth_failed.md",
                previous_message=message.content,
            )
            await message.author.send(reply)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.authenticate(message)
