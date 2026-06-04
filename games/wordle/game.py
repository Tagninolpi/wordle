"""
games/wordle/game.py — Pure game logic, no Discord dependencies.
"""

import time
from games.wordle.words import pick_word

# ── Emoji constants ────────────────────────────────────────────
GREY   = "⬛"   # not in word
YELLOW = "🟨"   # in word, wrong position
GREEN  = "🟩"   # correct position

LETTER_GREY  = "⬜"  # guessed, not in word  (alphabet row)
LETTER_WHITE = "▪️"  # not yet guessed

ALPHABET = "abcdefghijklmnopqrstuvwxyz"


# ── Evaluation ─────────────────────────────────────────────────

def evaluate_guess(guess: str, target: str) -> list[str]:
    """Return a list of emoji, one per letter."""
    result       = [GREY] * len(guess)
    target_chars = list(target)
    guess_chars  = list(guess)

    # Pass 1 — greens
    for i, (g, t) in enumerate(zip(guess_chars, target_chars)):
        if g == t:
            result[i]       = GREEN
            target_chars[i] = None
            guess_chars[i]  = None

    # Pass 2 — yellows
    for i, g in enumerate(guess_chars):
        if g is None:
            continue
        if g in target_chars:
            result[i] = YELLOW
            target_chars[target_chars.index(g)] = None

    return result


# ── Render helpers ─────────────────────────────────────────────

def render_guess_row(guess: str, colors: list[str]) -> str:
    """🟩⬛🟨⬛🟩  B R A V E"""
    squares = "".join(colors)
    spaced  = " ".join(guess.upper())
    return f"{squares}  {spaced}"


def render_alphabet(letter_states: dict[str, str]) -> str:
    """Two-row coloured alphabet block."""
    def row(letters: str) -> str:
        parts = []
        for ch in letters:
            state = letter_states.get(ch, "unknown")
            if state == "green":
                icon = GREEN
            elif state == "yellow":
                icon = YELLOW
            elif state == "grey":
                icon = LETTER_GREY
            else:
                icon = LETTER_WHITE
            parts.append(f"{icon}{ch.upper()}")
        return "  ".join(parts)

    return row(ALPHABET[:13]) + "\n" + row(ALPHABET[13:])


# ── Game state ─────────────────────────────────────────────────

class WordleGame:
    def __init__(self, player_id: int, word_length: int):
        self.player_id     = player_id
        self.word          = pick_word(word_length)
        self.word_length   = word_length
        self.guesses:      list[tuple[str, list[str]]] = []
        self.letter_states: dict[str, str] = {}
        self.start_time    = time.time()
        self.won           = False
        self.attempts      = 0

    def submit_guess(self, guess: str) -> list[str]:
        colors = evaluate_guess(guess, self.word)
        self.guesses.append((guess, colors))
        self.attempts += 1

        for letter, color in zip(guess, colors):
            current = self.letter_states.get(letter)
            if color == GREEN:
                self.letter_states[letter] = "green"
            elif color == YELLOW and current != "green":
                self.letter_states[letter] = "yellow"
            elif color == GREY and current is None:
                self.letter_states[letter] = "grey"

        if guess == self.word:
            self.won = True
        return colors

    def elapsed(self) -> str:
        secs = int(time.time() - self.start_time)
        m, s = divmod(secs, 60)
        return f"{m}m {s}s" if m else f"{s}s"

    def build_embed(self, action_msg: str) -> "discord.Embed":  # type hint only
        import discord
        embed = discord.Embed(title="🔤  Wordle", color=discord.Color.blurple())
        embed.description = f"**{action_msg}**"

        if self.guesses:
            lines = "\n".join(render_guess_row(g, c) for g, c in self.guesses)
            embed.add_field(name="Guesses", value=f"```\n{lines}\n```", inline=False)
        else:
            embed.add_field(name="Guesses", value="_No guesses yet._", inline=False)

        embed.add_field(
            name="Letters",
            value=render_alphabet(self.letter_states),
            inline=False,
        )
        embed.set_footer(
            text=f"Attempts: {self.attempts}  •  Word length: {self.word_length}"
        )
        return embed
