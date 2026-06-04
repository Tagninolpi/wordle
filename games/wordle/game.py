"""
games/wordle/game.py — Pure game logic, no Discord dependencies.

Spacing rule
------------
Discord collapses multiple regular spaces outside code blocks.
Wrapping field values in ``` preserves every space exactly.

Inside a monospace code block:
  - emoji  = 2 columns wide
  - letter = 1 column wide
  - space  = 1 column wide

So 1 space between letters = 2 cols per cell = aligned under one emoji.
LETTER_GAP below adds extra spaces on top of that mandatory 1.
Change LETTER_GAP to tune the visual spacing.
"""

import time
from games.wordle.words import pick_word

# ── Emoji constants ────────────────────────────────────────────
GREY   = "⬛"
YELLOW = "🟨"
GREEN  = "🟩"
UNSEEN = "⬜"

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# ── Spacing ────────────────────────────────────────────────────
# Extra spaces added on top of the 1 mandatory space between letters.
# 0 → "B R A V E"  (1 space, may feel tight)
# 1 → "B  R  A  V  E"  (2 spaces, aligns with emoji width)  ← default
# 2 → "B   R   A   V   E"  (3 spaces, wider)
LETTER_GAP: int = 1


# ── Evaluation ─────────────────────────────────────────────────

def evaluate_guess(guess: str, target: str) -> list[str]:
    result       = [GREY] * len(guess)
    target_chars = list(target)
    guess_chars  = list(guess)

    for i, (g, t) in enumerate(zip(guess_chars, target_chars)):
        if g == t:
            result[i]       = GREEN
            target_chars[i] = None
            guess_chars[i]  = None

    for i, g in enumerate(guess_chars):
        if g is None:
            continue
        if g in target_chars:
            result[i] = YELLOW
            target_chars[target_chars.index(g)] = None

    return result


# ── Render helpers ─────────────────────────────────────────────

def _sep() -> str:
    """Cell separator: 1 mandatory space + LETTER_GAP extras."""
    return " " * LETTER_GAP


def _sq_row(colors: list[str]) -> str:
    return "".join(colors)


def _let_row(word: str) -> str:
    return _sep().join(ch.upper() for ch in word)


def _code(text: str) -> str:
    """Wrap in a code block so Discord preserves all spaces."""
    return f"```\n{text}\n```"


def render_guess_row(guess: str, colors: list[str]) -> str:
    return _sq_row(colors) + "\n" + _let_row(guess)


def render_grid(guesses: list) -> str:
    if not guesses:
        return "_No guesses yet — type a word in the chat!_"
    body = "\n\n".join(render_guess_row(g, c) for g, c in guesses)
    return _code(body)


def render_alphabet(letter_states: dict[str, str]) -> str:
    """Packed [square][letter] cells, no spaces, 13 per line."""
    def cell(ch: str) -> str:
        s = letter_states.get(ch, "unknown")
        sq = GREEN if s == "green" else YELLOW if s == "yellow" else GREY if s == "grey" else UNSEEN
        return sq + ch.upper()
    chunks = [ALPHABET[:13], ALPHABET[13:]]
    return "\n".join("".join(cell(c) for c in chunk) for chunk in chunks)


# ── Game state ─────────────────────────────────────────────────

class WordleGame:
    def __init__(self, player_id: int, word_length: int):
        self.player_id      = player_id
        self.word           = pick_word(word_length)
        self.word_length    = word_length
        self.guesses:       list[tuple[str, list[str]]] = []
        self.letter_states: dict[str, str] = {}
        self.start_time     = time.time()
        self.won            = False
        self.attempts       = 0

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

    def build_embed(self, action_msg: str) -> "discord.Embed":
        import discord
        embed = discord.Embed(title="🔤  Wordle", color=discord.Color.blurple())
        embed.description = f"**{action_msg}**"

        embed.add_field(name="Guesses",   value=render_grid(self.guesses),              inline=False)
        embed.add_field(name="Alphabet",  value=render_alphabet(self.letter_states),    inline=False)
        embed.set_footer(text=f"Attempts: {self.attempts}  •  Word length: {self.word_length}")
        return embed