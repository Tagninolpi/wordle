"""
cogs/wordle.py — Slash command + message listener for the Wordle game.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils import channel_guard
from games.wordle.views import ACTIVE_GAMES, WordleMenuView, _menu_embed

logger = logging.getLogger(__name__)


class WordleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /wordle ──────────────────────────────────────────────────

    @app_commands.command(name="wordle", description="Play Wordle and other word games!")
    @channel_guard()
    async def wordle(self, interaction: discord.Interaction):
        view = WordleMenuView(interaction.user.id)
        await interaction.response.send_message(embed=_menu_embed(), view=view)
        view.message = await interaction.original_response()

    # ── Message listener ─────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        game_view = ACTIVE_GAMES.get(message.channel.id)
        if game_view is None:
            return

        # Not the active player → delete silently
        if message.author.id != game_view.owner_id:
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            return

        await game_view.handle_message(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(WordleCog(bot))
