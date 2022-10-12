import re
from typing import Optional

import discord
from discord.ext import commands, tasks
from loguru import logger

from .eventbrite import EventBrite
from .index import AttendeesIndex

LOGGER_CHANNEL = "logs"
EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")


def render_template(template_path: str, **kwargs):
    with open(template_path) as fp:
        text = fp.read().format(**kwargs)
        return text


def find_email(message: str):
    result = EMAIL_REGEX.search(message)
    if result:
        return result.group()
    return None


class AuthenticationCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        guild: discord.Guild,
        event_brite_client: EventBrite,
        attendees_index: AttendeesIndex,
        attendee_role_name: str,
    ) -> None:
        self.bot = bot
        self.attendees_index = attendees_index
        self.eventbrite = event_brite_client
        self._attendee_role_name = attendee_role_name
        self._guild = guild
        self._attendee_role = None
        self._channels = None
        self._start_tasks()

    def _start_tasks(self):
        self._load_attendees.start()

    @tasks.loop(minutes=5)
    async def _load_attendees(self):
        last_update = self.attendees_index.updated_at
        new_attendees = await self.eventbrite.list_attendees(last_update)
        for attendee in new_attendees:
            self.attendees_index.add(attendee)

    def _is_private_message(self, message: discord.Message) -> bool:
        conditions = (
            not message.author.bot,
            message.channel.type == discord.ChannelType.private,
        )
        return all(conditions)

    async def _get_user_from_server(
        self, user: discord.Member
    ) -> Optional[discord.Member]:
        return await self._guild.fetch_member(user.id)

    async def _get_channel(self, name: str) -> Optional[discord.TextChannel]:
        if not self._channels:
            self._channels = await self._guild.fetch_channels()

        return discord.utils.get(self._channels, name=name)

    async def _is_auth_needed(self, user: discord.Member) -> bool:
        return len(user.roles) == 1

    async def _get_attendee_role(self):
        if not self._attendee_role:
            roles = await self._guild.fetch_roles()
            self._attendee_role = discord.utils.get(
                roles, name=self._attendee_role_name
            )

        return self._attendee_role

    async def _set_attendee_role(self, member: discord.Member):
        attendee_role = await self._get_attendee_role()
        await member.add_roles(attendee_role)

    async def _log_auth_failed(self, message: discord.Message):
        log_message = render_template(
            "pybr2022/auth/templates/log_user_not_found.md",
            user_id=message.author.id,
            query=message.content,
        )
        channel = await self._get_channel(LOGGER_CHANNEL)
        await channel.send(log_message)

    async def authenticate(self, message: discord.Message):
        if not self._is_private_message(message):
            return

        user = await self._get_user_from_server(message.author)
        if not user:
            reply = render_template(
                "pybr2022/auth/templates/user_not_in_server.md",
                user_id=message.author.id,
            )
            await message.author.send(reply)
            return

        if not await self._is_auth_needed(user):
            reply = render_template(
                "pybr2022/auth/templates/user_already_authenticated.md",
                user_id=message.author.id,
            )
            await message.author.send(reply)
            return

        email = find_email(message.content)
        if not email:
            logger.warning(
                f"Email not found in message. author={message.author!r}, message={message.content!r}"
            )
            reply = render_template(
                "pybr2022/auth/templates/email_missing.md",
                user_id=message.author.id,
            )
            await message.author.send(reply)
            await self._log_auth_failed(message)
            return

        if self.attendees_index.search(email):
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
            await self._log_auth_failed(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.authenticate(message)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def checkuser(
        self,
        context: commands.Context,
        email: str,
        *args,
    ):
        if self.attendees_index.search(email):
            await context.reply(f"Email `{email}` encontrado no Eventbrite")
        else:
            await context.reply(f"Email `{email}` **não** encontrado no Eventbrite")

    @commands.command("authinfo")
    @commands.has_permissions(manage_guild=True)
    async def info(
        self,
        context: commands.Context,
        *args,
    ):
        await context.reply(
            "Index:\n"
            f"- Size: `{len(self.attendees_index._index)}`\n"
            f"- Updated at: `{len(self.attendees_index.updated_at)}`"
        )
