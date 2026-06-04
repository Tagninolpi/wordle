"""
dev.py — Local development runner.

Differences from main.py:
  - keep_alive (Flask) is NOT started (no need locally)
  - SYNC_GUILD_ONLY is forced True so slash commands appear instantly
    in your test server instead of waiting up to 1 hour for global sync.
  - Reads DEV_GUILD_IDS from config.py (add your test server ID there).
"""

import asyncio
import logging

import discord
from discord.ext import commands

from config import Config
from utils import setup_logging
from games.wordle.words import load_word_bank

setup_logging(logging.DEBUG)   # verbose output while developing
logger = logging.getLogger(__name__)

COGS_TO_LOAD: list[str] = [
    "cogs.wordle",
]


class GamingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True

        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

    async def setup_hook(self):
        logger.info("DEV MODE — bot starting up...")

        load_word_bank()

        for cog in COGS_TO_LOAD:
            try:
                await self.load_extension(cog)
                logger.info(f"  Loaded cog: {cog}")
            except Exception as exc:
                logger.error(f"  Failed to load cog {cog}: {exc}")

        # Always sync to guild only in dev — commands show up in <5 seconds
        if not Config.DEV_GUILD_IDS:
            logger.warning(
                "DEV_GUILD_IDS is empty in config.py! "
                "Add your test server ID so slash commands sync instantly."
            )
            await self.tree.sync()   # fallback to global (slow)
        else:
            for guild_id in Config.DEV_GUILD_IDS:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"  Synced commands to dev guild {guild_id}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (id: {self.user.id})")
        logger.info(f"Active in {len(self.guilds)} guild(s)")
        logger.info("DEV MODE active — no keep_alive server running")
        await self.change_presence(
            activity=discord.Game(name="[DEV] Wordle | /wordle")
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error: {error}")


async def main():
    Config.validate()
    bot = GamingBot()
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())