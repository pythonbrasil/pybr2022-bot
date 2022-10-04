from discord.ext.commands import Bot
from loguru import logger

from pybr2022 import config
from pybr2022.auth.cog import AuthenticationCog
from pybr2022.auth.eventbrite import EventBrite
from pybr2022.auth.index import AttendeesIndex


async def setup(bot: Bot):
    logger.info("Bot setup")
    eventbrite = EventBrite(config.EVENTBRITE_EVENT_ID, config.EVENTBRITE_TOKEN)
    attendees_index = AttendeesIndex(config.ATTENDEES_INDEX_CACHE)

    await bot.add_cog(
        AuthenticationCog(
            bot,
            eventbrite,
            attendees_index,
            config.DISCORD_SERVER_ID,
            config.DISCORD_ATTENTEE_ROLE_NAME,
        )
    )
