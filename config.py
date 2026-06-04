"""
config.py — Central configuration for the Gaming Bot.
Edit the values below to match your server.
Secrets (token) live in .env, everything else lives here.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Discord ──────────────────────────────────────────────────────────────
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

    # ── Channel restrictions ─────────────────────────────────────────────────
    # Only allow game commands inside this category (set to None to disable check)
    ALLOWED_CATEGORY_ID: int | None = 123456789012345678   # <-- replace with your category ID

    # Channels must start with this prefix (case-insensitive) to be allowed
    ALLOWED_CHANNEL_PREFIX: str = "gaming lobby"

    # ── Bot behaviour ────────────────────────────────────────────────────────
    COMMAND_PREFIX: str = "!"          # used for legacy prefix commands if ever needed
    SYNC_COMMANDS: bool = True         # sync slash commands on startup
    SYNC_GUILD_ONLY: bool = False      # True = sync to specific guilds only (faster for dev)

    # If SYNC_GUILD_ONLY is True, add your dev guild IDs here
    DEV_GUILD_IDS: list[int] = []      # e.g. [123456789012345678]

    # ── Wordle game settings ─────────────────────────────────────────────────
    WORDLE_MENU_TIMEOUT:    int = 120   # seconds before menu times out
    WORDLE_GAME_TIMEOUT:    int = 600   # seconds before a live game times out

    @classmethod
    def validate(cls):
        if not cls.DISCORD_TOKEN:
            raise ValueError(
                "DISCORD_TOKEN is not set. "
                "Create a .env file from .env.example and fill in your token."
            )
