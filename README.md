# 🎮 Gaming Bot

A scalable Discord bot for word games, starting with Wordle.

---

## Project structure

```
wordle_bot/
├── main.py                  ← entry point
├── config.py                ← all settings (edit this)
├── utils.py                 ← shared helpers (channel guard, logging)
├── requirements.txt
├── .env                     ← your secrets (not committed)
├── .env.example             ← template
│
├── games/                   ← pure game logic, no Discord
│   └── wordle/
│       ├── words.py         ← word bank loader
│       ├── game.py          ← game state & evaluation
│       └── views.py         ← all Discord UI views
│
└── cogs/                    ← one file per game (slash command + listener)
    └── wordle.py
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure secrets
```bash
cp .env.example .env
# then edit .env and paste your bot token
```

### 3. Configure the bot
Open `config.py` and set:
- `ALLOWED_CATEGORY_ID` — the Discord category ID where game commands are allowed
- `ALLOWED_CHANNEL_PREFIX` — channels must start with this name (default: `"gaming lobby"`)
- `SYNC_GUILD_ONLY` / `DEV_GUILD_IDS` — for faster command sync during development

### 4. Run
```bash
python main.py
```

---

## Channel restriction

`/wordle` (and any future game command decorated with `@channel_guard()`) will
**only work** in channels that satisfy **both** conditions:

1. The channel is inside the category whose ID matches `ALLOWED_CATEGORY_ID`.
2. The channel name starts with `ALLOWED_CHANNEL_PREFIX` (case-insensitive).

If either check fails the user receives a silent ephemeral error.

---

## Adding a new game

1. Create `games/<game>/` with `game.py` (logic) and `views.py` (Discord UI).
2. Create `cogs/<game>.py` with a `commands.Cog` subclass and an `async def setup(bot)`.
3. Add `"cogs.<game>"` to `COGS_TO_LOAD` in `main.py`.
4. Decorate your slash command with `@channel_guard()` from `utils.py`.

That's it — no changes to any other file are needed.

---

## Word bank

The bot tries to load words from the **nltk** English corpus at startup (~235 k words).
If nltk is not installed or the download fails, a small built-in fallback list is used.

To pre-download the corpus manually:
```python
import nltk
nltk.download("words")
```
