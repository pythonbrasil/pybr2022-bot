from discord import Intents

from pybr2022 import config
from pybr2022.bot import Bot

bot = Bot(command_prefix="pybr!", intents=Intents.all())

if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
