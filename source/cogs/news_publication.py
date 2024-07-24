import disnake
from disnake.ext import commands, tasks
from disnake import errors as disnake_errors

from aiohttp import ClientSession

from loguru import logger

from source.utils import NewsParser
from source.config import ConfigBot

config = ConfigBot()


class NewsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.parser = NewsParser()
        self.fetch_news_task = self.fetch_news.start()

    @tasks.loop(minutes=config.NEWS_CHECK_TIMEOUT)
    async def fetch_news(self):
        try:
            async with ClientSession() as session:
                latest_news = await self.parser.get_latest_news(session)
                channel = self.bot.get_channel(config.CHANNEL_ID)

                if latest_news:
                    if latest_news["link"] != self.parser.last_published_news_link:
                        self.parser.last_published_news_link = latest_news["link"]
                        content = await self.parser.get_news_content(session, latest_news["link"])

                        embed_text = disnake.Embed(color=config.EMBED_COLOR)
                        embed_text.set_image("https://i.imgur.com/zSwcRBK.png")
                        embed_text.description = (
                            f"# {latest_news['title']}\n{content}\n"
                            f"### Читать весь пост [тут]({latest_news['link']})"
                        )

                        embed_image = disnake.Embed(color=config.EMBED_COLOR)
                        embed_image.set_image(latest_news["image"])

                        await channel.send(embeds=[embed_image, embed_text])

        except (TypeError, ValueError) as e:
            logger.error(f"TYPE/VALUE ERROR: {e}")
        except disnake_errors as e:
            logger.error(f"DISNAKE ERROR: {e}")

    @fetch_news.before_loop
    async def before_fetch_news(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.success(f"{self.bot.user} is ready")


def setup(bot):
    bot.add_cog(NewsCog(bot))
