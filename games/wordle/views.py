"""
games/wordle/views.py — All Discord UI views for the Wordle game.

View hierarchy:
  WordleMenuView      (entry point: "choose a game")
    └─ WordleInfoView (rules + word-length buttons)
         └─ WordleGameView (live game embed + message listener)
              └─ (game ends → final embed, view removed)
"""

import logging
from typing import Optional

import discord

from config import Config
from games.wordle.game import WordleGame, render_guess_row, render_alphabet

logger = logging.getLogger(__name__)

# Registry: channel_id → WordleGameView  (max one game per channel)
ACTIVE_GAMES: dict[int, "WordleGameView"] = {}


# ──────────────────────────────────────────────
#  Shared components
# ──────────────────────────────────────────────

class _OwnedView(discord.ui.View):
    """Base view that stores owner_id and a reference to the sent message."""

    def __init__(self, owner_id: int, timeout: int):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.message: Optional[discord.Message] = None

    def _not_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id != self.owner_id

    async def _deny(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "❌ Only the person who started this game can press buttons.",
            ephemeral=True,
        )

    async def _timeout_edit(self, extra: str = "") -> None:
        for child in self.children:
            child.disabled = True
        embed = discord.Embed(
            title="⏱️ Session timed out.",
            description=extra or "Start a new game with `/wordle`.",
            color=discord.Color.red(),
        )
        try:
            if self.message:
                await self.message.edit(embed=embed, view=self)
        except Exception:
            pass


class LeaveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Leave", style=discord.ButtonStyle.danger, row=4)

    async def callback(self, interaction: discord.Interaction):
        view: _OwnedView = self.view
        if view._not_owner(interaction):
            await view._deny(interaction)
            return

        # Clean up any live game in this channel
        gv = ACTIVE_GAMES.pop(interaction.channel_id, None)
        if gv:
            gv.stop()

        for child in view.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(title="👋 Game closed.", color=discord.Color.red()),
            view=view,
        )
        view.stop()


# ──────────────────────────────────────────────
#  Embed builders
# ──────────────────────────────────────────────

def _menu_embed() -> discord.Embed:
    return discord.Embed(
        title="🎮  Gaming Hub",
        description=(
            "Welcome! Choose a game to play.\n\n"
            "🔤 **Wordle** — Guess the hidden word letter by letter."
        ),
        color=discord.Color.blurple(),
    )


def _info_embed() -> discord.Embed:
    return discord.Embed(
        title="🔤  Wordle — How to play",
        description=(
            "Type a word in the chat to guess the hidden word.\n\n"
            "🟩 **Green** — correct letter, correct position.\n"
            "🟨 **Yellow** — correct letter, wrong position.\n"
            "⬛ **Grey** — letter not in the word.\n\n"
            "You have **unlimited** guesses. Good luck!\n\n"
            "**Choose a word length to begin:**"
        ),
        color=discord.Color.blurple(),
    )


# ──────────────────────────────────────────────
#  View 1 — Main menu
# ──────────────────────────────────────────────

class WordleMenuView(_OwnedView):
    def __init__(self, owner_id: int):
        super().__init__(owner_id, timeout=Config.WORDLE_MENU_TIMEOUT)
        self.add_item(LeaveButton())

    @discord.ui.button(label="🔤 Wordle", style=discord.ButtonStyle.primary, row=0)
    async def wordle_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self._not_owner(interaction):
            await self._deny(interaction)
            return
        view = WordleInfoView(self.owner_id)
        await interaction.response.edit_message(embed=_info_embed(), view=view)
        view.message = await interaction.original_response()

    async def on_timeout(self):
        await self._timeout_edit()


# ──────────────────────────────────────────────
#  View 2 — Rules + length picker
# ──────────────────────────────────────────────

class WordleInfoView(_OwnedView):
    def __init__(self, owner_id: int):
        super().__init__(owner_id, timeout=Config.WORDLE_MENU_TIMEOUT)
        self.add_item(LeaveButton())

    # ── Length buttons ──────────────────────

    async def _start(self, interaction: discord.Interaction, length: int):
        if self._not_owner(interaction):
            await self._deny(interaction)
            return

        if interaction.channel_id in ACTIVE_GAMES:
            await interaction.response.send_message(
                "⚠️ There is already an active Wordle game in this channel!",
                ephemeral=True,
            )
            return

        game = WordleGame(self.owner_id, length)
        view = WordleGameView(self.owner_id, game, interaction.channel)
        embed = game.build_embed(f"Guess the **{length}-letter** word!")
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        ACTIVE_GAMES[interaction.channel_id] = view

    @discord.ui.button(label="3 letters", style=discord.ButtonStyle.secondary, row=0)
    async def btn3(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._start(interaction, 3)

    @discord.ui.button(label="4 letters", style=discord.ButtonStyle.secondary, row=0)
    async def btn4(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._start(interaction, 4)

    @discord.ui.button(label="5 letters", style=discord.ButtonStyle.secondary, row=0)
    async def btn5(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._start(interaction, 5)

    @discord.ui.button(label="6 letters", style=discord.ButtonStyle.secondary, row=0)
    async def btn6(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._start(interaction, 6)

    # ── Navigation ──────────────────────────

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self._not_owner(interaction):
            await self._deny(interaction)
            return
        view = WordleMenuView(self.owner_id)
        await interaction.response.edit_message(embed=_menu_embed(), view=view)
        view.message = await interaction.original_response()

    async def on_timeout(self):
        await self._timeout_edit()


# ──────────────────────────────────────────────
#  View 3 — Live game
# ──────────────────────────────────────────────

class WordleGameView(_OwnedView):
    def __init__(self, owner_id: int, game: WordleGame, channel: discord.TextChannel):
        super().__init__(owner_id, timeout=Config.WORDLE_GAME_TIMEOUT)
        self.game    = game
        self.channel = channel
        self.add_item(LeaveButton())

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=3)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self._not_owner(interaction):
            await self._deny(interaction)
            return
        ACTIVE_GAMES.pop(interaction.channel_id, None)
        self.stop()
        view = WordleInfoView(self.owner_id)
        await interaction.response.edit_message(embed=_info_embed(), view=view)
        view.message = await interaction.original_response()

    # ── Called by the cog's on_message ──────

    async def handle_message(self, message: discord.Message) -> None:
        """Process an incoming guess message."""
        guess = message.content.strip().lower()

        # Always try to delete the message
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        if not guess.isalpha():
            await self._update_action("❌  Only letters please!")
            return

        if len(guess) != self.game.word_length:
            await self._update_action(
                f"❌  **{guess.upper()}** is not {self.game.word_length} letters long — try again!"
            )
            return

        # Valid guess
        self.game.submit_guess(guess)

        if self.game.won:
            await self._finish()
        else:
            await self._update_action(
                f"Keep going! Guess the **{self.game.word_length}-letter** word."
            )

    async def _update_action(self, action_msg: str) -> None:
        embed = self.game.build_embed(action_msg)
        try:
            if self.message:
                await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass

    async def _finish(self) -> None:
        """Win condition: post final embed, remove view."""
        ACTIVE_GAMES.pop(self.channel.id, None)
        self.stop()

        game = self.game
        guess_lines = "\n".join(render_guess_row(g, c) for g, c in game.guesses)
        plural      = "s" if game.attempts != 1 else ""

        embed = discord.Embed(
            title="🎉  Congratulations!",
            description=(
                f"<@{game.player_id}> guessed **{game.word.upper()}** in "
                f"**{game.attempts}** attempt{plural}!\n\n"
                f"⏱️ Time: **{game.elapsed()}**"
            ),
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Guess history",
            value=f"```\n{guess_lines}\n```",
            inline=False,
        )
        embed.add_field(
            name="Letters",
            value=render_alphabet(game.letter_states),
            inline=False,
        )

        try:
            if self.message:
                await self.message.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass

    async def on_timeout(self):
        ACTIVE_GAMES.pop(self.channel.id, None)
        await self._timeout_edit(
            f"The word was **{self.game.word.upper()}**."
        )
