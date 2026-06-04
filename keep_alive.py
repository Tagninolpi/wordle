"""
keep_alive.py — Starts a tiny Flask web server on port 8080.

Render (free tier) spins down services after inactivity.
Point an external pinger (e.g. UptimeRobot) at your Render URL
and it will hit GET / every 5 minutes, keeping the bot alive.
"""

import threading
import logging
from flask import Flask

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)   # silence Flask request logs

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Bot is alive ✅</h1>", 200

@app.route("/health")
def health():
    return {"status": "ok"}, 200

def keep_alive():
    """Call this once from main.py before bot.start()."""
    t = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True)
    t.start()
