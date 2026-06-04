"""
games/wordle/words.py — Word bank for the Wordle game.

Tries to load words from the nltk 'words' corpus.
Falls back to a small built-in list if nltk is unavailable.
Call load_word_bank() once at startup; then use pick_word(length).
"""

import random
import logging

logger = logging.getLogger(__name__)

_BANK: dict[int, list[str]] = {}
_VALID: set[str] = set()   # fast O(1) membership check for guess validation


def load_word_bank() -> None:
    """Populate _BANK and _VALID. Call once during bot startup."""
    global _BANK, _VALID
    _BANK = _try_nltk() or _fallback()
    _VALID = {w for words in _BANK.values() for w in words}
    for length, words in _BANK.items():
        logger.info(f"Word bank: {len(words)} words of length {length}")
    logger.info(f"Valid guess set: {len(_VALID)} total words")


def pick_word(length: int) -> str:
    words = _BANK.get(length)
    if not words:
        words = _fallback()[length]
    return random.choice(words).lower()


def is_valid_word(word: str) -> bool:
    """Return True if the word exists in the loaded word bank."""
    return word.lower() in _VALID


# ──────────────────────────────────────────────

def _try_nltk() -> dict[int, list[str]] | None:
    try:
        import nltk  # type: ignore
        try:
            from nltk.corpus import words as nltk_words  # type: ignore
            all_words = nltk_words.words()
        except LookupError:
            nltk.download("words", quiet=True)
            from nltk.corpus import words as nltk_words  # type: ignore
            all_words = nltk_words.words()

        bank: dict[int, list[str]] = {}
        for length in (3, 4, 5, 6):
            pool = [w.lower() for w in all_words if len(w) == length and w.isalpha()]
            bank[length] = random.sample(pool, min(len(pool), 5000))
        return bank
    except Exception as exc:
        logger.warning(f"nltk unavailable ({exc}), using built-in word list.")
        return None


def _fallback() -> dict[int, list[str]]:
    return {
        3: ["cat", "dog", "sun", "run", "hat", "big", "cup", "map", "fog", "nut",
            "jar", "axe", "box", "key", "leg", "net", "oak", "pin", "ray", "sea"],
        4: ["bark", "calm", "dart", "earn", "fade", "gale", "harp", "iris", "jade",
            "kite", "lamp", "maze", "nail", "opal", "pace", "rain", "sage", "tale",
            "urge", "vane", "wave", "yarn", "zeal", "bold", "cave", "dusk", "echo"],
        5: ["brave", "champ", "delta", "ember", "flare", "gleam", "haste", "ivory",
            "joust", "knack", "latch", "mirth", "noble", "onset", "pivot", "quirk",
            "rally", "shank", "trove", "vigor", "waltz", "yearn", "abbey", "blaze",
            "crisp", "dwarf", "envoy", "frost", "grail", "hound"],
        6: ["ablaze", "blight", "crafty", "dagger", "fabled", "gambit", "hustle",
            "intact", "jangle", "knight", "latent", "mystic", "narrow", "parlor",
            "quartz", "rafter", "saddle", "thrive", "unbolt", "vassal", "warden",
            "bridge", "cannon", "donkey", "Empire", "falcon", "gravel", "harbor"],
    }