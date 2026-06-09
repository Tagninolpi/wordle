"""
main.py — Entry point for the Gaming Bot.

Run modes:
  Production (Render):  python main.py
  Local dev:            DEV=1 python main.py

DEV=1 differences:
  - Flask keep-alive server is NOT started
  - Slash commands sync to DEV_GUILD_IDS only (instant, no global wait)
  - Bot status shows [DEV] prefix
  - DEBUG-level logging

To add a new game in the future:
  1. Create  games/<your_game>/  with game.py, views.py, words.json (if needed)
  2. Create  cogs/<your_game>.py  with a Cog + setup()
  3. Add the cog string to COGS_TO_LOAD below
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

from config import Config
from utils import setup_logging
from games.wordle.words import load_word_bank

# ── Dev mode flag ─────────────────────────────────────────────────────────────
DEV = os.getenv("DEV", "0") == "1"

setup_logging(logging.DEBUG if DEV else logging.INFO)
logger = logging.getLogger(__name__)

# ── Add new game cogs here ────────────────────────────────────────────────────
COGS_TO_LOAD: list[str] = [
    "cogs.wordle",
    # "cogs.hangman",
    # "cogs.trivia",
]
# ─────────────────────────────────────────────────────────────────────────────


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
        mode = "DEV" if DEV else "PROD"
        logger.info(f"Bot starting up [{mode}]...")

        load_word_bank()

        for cog in COGS_TO_LOAD:
            try:
                await self.load_extension(cog)
                logger.info(f"  Loaded cog: {cog}")
            except Exception as exc:
                logger.error(f"  Failed to load cog {cog}: {exc}")

        if Config.SYNC_COMMANDS:
            if DEV:
                # Guild-only sync — shows up in Discord within seconds
                if not Config.DEV_GUILD_IDS:
                    logger.warning(
                        "DEV=1 but DEV_GUILD_IDS is empty in config.py. "
                        "Falling back to global sync (slow)."
                    )
                    await self.tree.sync()
                    logger.info("  Synced commands globally (fallback)")
                else:
                    for guild_id in Config.DEV_GUILD_IDS:
                        guild = discord.Object(id=guild_id)
                        self.tree.copy_global_to(guild=guild)
                        await self.tree.sync(guild=guild)
                        logger.info(f"  Synced commands to dev guild {guild_id}")
            else:
                await self.tree.sync()
                logger.info("  Synced commands globally")

    async def on_ready(self):
        prefix = "[DEV] " if DEV else ""
        logger.info(f"Logged in as {self.user} (id: {self.user.id})")
        logger.info(f"Active in {len(self.guilds)} guild(s)")
        await self.change_presence(
            activity=discord.Game(name=f"{prefix}Wordle | /wordle")
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error: {error}")


async def main():
    Config.validate()

    if not DEV:
        from keep_alive import keep_alive
        keep_alive()
        logger.info("Keep-alive server started")
    else:
        logger.info("DEV mode — keep-alive server skipped")

    bot = GamingBot()
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())