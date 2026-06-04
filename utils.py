"""
utils.py — Shared helpers used across all game cogs.

Includes:
  - channel_guard()  : decorator / check for the category + channel name restriction
  - setup_logging()  : configures the root logger
"""

import logging
import functools
from typing import Callable

import discord
from discord import app_commands

from config import Config


# ──────────────────────────────────────────────
#  Logging
# ──────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ──────────────────────────────────────────────
#  Channel guard
# ──────────────────────────────────────────────

def _channel_is_allowed(interaction: discord.Interaction) -> bool:
    """
    Returns True only if ALL conditions below are met:
      1. The command is used inside a guild text channel.
      2. The channel belongs to the configured category (if set).
      3. The channel name starts with ALLOWED_CHANNEL_PREFIX (case-insensitive).
    """
    channel = interaction.channel

    # Must be a guild text channel
    if not isinstance(channel, discord.TextChannel):
        return False

    # Category check
    if Config.ALLOWED_CATEGORY_ID is not None:
        if not channel.category_id in Config.ALLOWED_CATEGORY_ID:
            return False

    # Channel name prefix check
    prefix = Config.ALLOWED_CHANNEL_PREFIX.lower().strip()
    if prefix and not channel.name.lower().startswith(prefix):
        return False

    return True


# app_commands check — use as @channel_guard() on any slash command
def channel_guard() -> Callable:
    """
    Slash-command check that silently rejects usage outside allowed channels.

    Usage:
        @app_commands.command(...)
        @channel_guard()
        async def my_command(self, interaction): ...
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        if _channel_is_allowed(interaction):
            return True
        # Silently inform only the caller
        await interaction.response.send_message(
            "❌ This command can only be used in a **⚔️-maggod-lobby** channel "
            "inside the correct category.",
            ephemeral=True,
        )
        return False

    return app_commands.check(predicate)
