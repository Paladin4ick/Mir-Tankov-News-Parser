import os

import disnake
from disnake.ext.commands import Bot

from dotenv import load_dotenv

from source.utils import setup_logger

load_dotenv()
setup_logger()


bot = Bot(
    command_prefix="&",
    intents=disnake.Intents.all(),
    help_command=None
)


bot.load_extension("cogs.news_publication")

bot.run(os.getenv("DISCORD_TOKEN"))
