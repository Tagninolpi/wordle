"""
main.py — Entry point for the Gaming Bot.

To add a new game in the future:
  1. Create  games/<your_game>/  with game.py, views.py, words.py (if needed)
  2. Create  cogs/<your_game>.py  with a Cog + setup()
  3. Add the cog string to COGS_TO_LOAD below — that is it.
"""

import asyncio
import logging

import discord
from discord.ext import commands

from config import Config
from utils import setup_logging
from games.wordle.words import load_word_bank
from keep_alive import keep_alive

setup_logging()
logger = logging.getLogger(__name__)

# ── Add new game cogs here ────────────────────────────────────────
COGS_TO_LOAD: list[str] = [
    "cogs.wordle",
    # "cogs.hangman",
    # "cogs.trivia",
]
# ─────────────────────────────────────────────────────────────────


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
        logger.info("Bot starting up...")

        load_word_bank()

        for cog in COGS_TO_LOAD:
            try:
                await self.load_extension(cog)
                logger.info(f"  Loaded cog: {cog}")
            except Exception as exc:
                logger.error(f"  Failed to load cog {cog}: {exc}")

        if Config.SYNC_COMMANDS:
            if Config.SYNC_GUILD_ONLY and Config.DEV_GUILD_IDS:
                for guild_id in Config.DEV_GUILD_IDS:
                    guild = discord.Object(id=guild_id)
                    self.tree.copy_global_to(guild=guild)
                    await self.tree.sync(guild=guild)
                    logger.info(f"  Synced commands to guild {guild_id}")
            else:
                await self.tree.sync()
                logger.info("  Synced commands globally")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (id: {self.user.id})")
        logger.info(f"Active in {len(self.guilds)} guild(s)")
        await self.change_presence(activity=discord.Game(name="Wordle | /wordle"))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error: {error}")


async def main():
    Config.validate()
    keep_alive()   # start Flask keep-alive server before the bot

    bot = GamingBot()
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
