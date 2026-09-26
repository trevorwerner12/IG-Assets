"""Settings, read from environment variables (see .env.example)."""

import os
from dataclasses import dataclass, field
from pathlib import Path

PERSONA_PATH = Path(__file__).with_name("persona.md")


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    model: str = field(default_factory=lambda: os.environ.get("BOT_MODEL", "claude-opus-5"))
    effort: str = field(default_factory=lambda: os.environ.get("BOT_EFFORT", "low"))
    history_turns: int = field(default_factory=lambda: int(os.environ.get("BOT_HISTORY_TURNS", "20")))
    db_path: str = field(default_factory=lambda: os.environ.get("BOT_DB_PATH", "conversations.db"))

    twilio_account_sid: str = field(default_factory=lambda: os.environ.get("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: os.environ.get("TWILIO_AUTH_TOKEN", ""))
    # Public URL Twilio posts to; needed to verify signatures behind a proxy/tunnel.
    public_webhook_url: str = field(default_factory=lambda: os.environ.get("PUBLIC_WEBHOOK_URL", ""))
    validate_signature: bool = field(default_factory=lambda: _bool("TWILIO_VALIDATE_SIGNATURE", True))

    # Owner's own phone: gets a text whenever a conversation needs a human.
    owner_phone: str = field(default_factory=lambda: os.environ.get("OWNER_PHONE", ""))
    # Log replies instead of sending them.
    dry_run: bool = field(default_factory=lambda: _bool("DRY_RUN"))

    persona: str = field(default_factory=lambda: PERSONA_PATH.read_text(encoding="utf-8"))
