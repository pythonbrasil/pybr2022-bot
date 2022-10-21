from discord.ext.commands import Bot
from loguru import logger

from pybr2022 import config
from pybr2022.auth.cog import AuthenticationCog
from pybr2022.auth.eventbrite import EventBrite
from pybr2022.auth.index import AttendeesIndex
from pybr2022.messages.cog import MessagesCog
from pybr2022.talks.pretalx import Pretalx
from pybr2022.talks.cog import TalksCog


async def setup(bot: Bot):
    logger.info("Getting Discord server")
    guild = await bot.fetch_guild(config.DISCORD_SERVER_ID)

    logger.info("Setup EventBrite")
    eventbrite = EventBrite(config.EVENTBRITE_EVENT_ID, config.EVENTBRITE_TOKEN)

    logger.info("Setup AttendeesIndex")
    attendees_index = AttendeesIndex(
        config.ATTENDEES_CACHE_PATH, config.ATTENDEES_CACHE_ENABLED
    )

    logger.info("Setup TalksCog")
    pretalx = Pretalx(config.PRETALX_EVENT_SLUT, config.PRETALX_TOKEN)
    await bot.add_cog(TalksCog(bot, guild, pretalx))

    logger.info("Setup MessageCog")
    await bot.add_cog(MessagesCog(bot, guild, config.DISCORD_WELCOME_CHANNEL))

    logger.info("Setup AuthenticationCog")
    await bot.add_cog(
        AuthenticationCog(
            bot,
            guild,
            eventbrite,
            attendees_index,
            config.DISCORD_ATTENTEE_ROLE_NAME,
        )
    )
