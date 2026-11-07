"""Loads settings from the .env file. Nothing secret lives in the code."""
import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "flights.db"

load_dotenv(APP_DIR / ".env")


def _int(name, default):
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _bool(name, default):
    val = os.getenv(name, "").strip().lower()
    if not val:
        return default
    return val in ("1", "yes", "y", "true", "on")


def api_key():
    return os.getenv("SERPAPI_KEY", "").strip()


def demo_mode():
    """No key -> demo mode with fake flights, so the app can be tried right away."""
    return not api_key() or _bool("DEMO_MODE", False)


CACHE_HOURS = _int("CACHE_HOURS", 6)
CONFIRM_ABOVE_CREDITS = _int("CONFIRM_ABOVE_CREDITS", 3)
MAX_CREDITS_PER_SEARCH = _int("MAX_CREDITS_PER_SEARCH", 14)
UNITED_EXPLORER_CARD = _bool("UNITED_EXPLORER_CARD", True)
ALERT_CHECK_HOURS = _int("ALERT_CHECK_HOURS", 12)
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "").strip()
PORT = _int("PORT", 5055)


def save_api_key(key):
    """Write SERPAPI_KEY into the .env file (creating it if needed) and use it right away."""
    key = key.strip()
    env = APP_DIR / ".env"
    example = APP_DIR / ".env.example"
    lines = env.read_text().splitlines() if env.exists() else (
        example.read_text().splitlines() if example.exists() else [])
    for i, line in enumerate(lines):
        if line.strip().startswith("SERPAPI_KEY="):
            lines[i] = f"SERPAPI_KEY={key}"
            break
    else:
        lines.append(f"SERPAPI_KEY={key}")
    env.write_text("\n".join(lines) + "\n")
    os.environ["SERPAPI_KEY"] = key
