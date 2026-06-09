"""
games/wordle/words.py — Word bank loaded from words.json at startup.

Place words.json in the same directory as this file.
Format: {"3": ["aah", ...], "4": [...], "5": [...], "6": [...]}
"""

import json
import random
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BANK: dict[int, list[str]] = {}
_VALID: frozenset[str] = frozenset()

# Path to the JSON file — same folder as this module
_JSON_PATH = Path(__file__).parent / "words.json"


def load_word_bank() -> None:
    """Load words from words.json. Call once at bot startup."""
    global _BANK, _VALID

    if not _JSON_PATH.exists():
        raise FileNotFoundError(
            f"Word list not found at {_JSON_PATH}. "
            "Make sure words.json is in games/wordle/"
        )

    with open(_JSON_PATH, encoding="utf-8") as f:
        raw: dict[str, list[str]] = json.load(f)

    _BANK = {int(k): [w.lower() for w in v] for k, v in raw.items()}
    _VALID = frozenset(w for words in _BANK.values() for w in words)

    for length, words in sorted(_BANK.items()):
        logger.info(f"Word bank: {len(words)} words of length {length}")
    logger.info(f"Valid guess set: {len(_VALID)} total words")


def pick_word(length: int) -> str:
    words = _BANK.get(length)
    if not words:
        raise RuntimeError(f"No words of length {length} in words.json")
    return random.choice(words)


def is_valid_word(word: str) -> bool:
    return word.lower() in _VALID