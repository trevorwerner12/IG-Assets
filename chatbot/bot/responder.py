"""Turns an incoming text into a reply with Claude."""

import logging

import anthropic
from pydantic import BaseModel, Field

from .config import Settings

log = logging.getLogger(__name__)

FALLBACK_REPLY = "Thanks for the message. I'll get back to you shortly."

RULES = """\
You are an automated text-message assistant replying on behalf of the business
owner described in the persona below, in his voice. You are texting over
SMS / WhatsApp.

Rules:
- Keep each reply short (under 480 characters), plain text, no markdown.
- Only state facts about the owner and the business that appear in the persona.
  Fields still in [brackets] are unknown: don't invent names, prices,
  addresses, hours or commitments. Hand off instead.
- If someone sincerely asks whether they're talking to a real person, a bot or
  an AI, be honest: say this is his automated assistant and that he reads the
  messages and follows up personally.
- Never ask anyone for money, gift cards, crypto, bank or card details,
  passwords or verification codes, and never pitch investments. Payment
  questions go to the owner.
- Don't flirt, arrange personal meetups, or take on a romantic role.
- For an emergency (fire, gas or oil leak, injury), tell them to call 911 first.
- Set needs_owner to true whenever the persona's hand-off rules apply or you
  are unsure, and put a one-line summary for the owner in owner_note.
"""


class Reply(BaseModel):
    reply: str = Field(description="The text message to send back.")
    needs_owner: bool = Field(description="True if the real owner should follow up personally.")
    owner_note: str = Field(description="One-line summary for the owner, or empty string.")


class Responder:
    def __init__(self, settings: Settings, client: anthropic.Anthropic | None = None):
        self.settings = settings
        self.client = client or anthropic.Anthropic()
        # Stable prefix (rules + persona) first so prompt caching can reuse it.
        self.system = [
            {
                "type": "text",
                "text": f"{RULES}\n<persona>\n{settings.persona}\n</persona>",
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def respond(self, history: list[dict]) -> Reply:
        """`history` is the conversation so far, ending with the new user message."""
        try:
            response = self.client.beta.messages.parse(
                model=self.settings.model,
                max_tokens=4096,
                system=self.system,
                messages=_merge_consecutive(history),
                output_config={"effort": self.settings.effort},
                output_format=Reply,
                # Re-run on Anthropic's recommended fallback model if a request is declined.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError:
            log.warning("Rate limited by Claude API")
            return _handoff("Bot was rate limited; reply manually.")
        except anthropic.APIStatusError as e:
            log.error("Claude API error %s: %s", e.status_code, e.message)
            return _handoff(f"Bot hit an API error ({e.status_code}); reply manually.")
        except anthropic.APIConnectionError:
            log.error("Could not reach Claude API")
            return _handoff("Bot couldn't reach the Claude API; reply manually.")

        if response.stop_reason == "refusal":
            return _handoff("Bot declined to answer this message; reply manually.")
        if response.parsed_output is None:
            return _handoff(f"Bot produced no usable reply (stop_reason={response.stop_reason}).")
        return response.parsed_output


def _handoff(note: str) -> Reply:
    return Reply(reply=FALLBACK_REPLY, needs_owner=True, owner_note=note)


def _merge_consecutive(history: list[dict]) -> list[dict]:
    """Join back-to-back messages from the same side (e.g. two texts in a row)."""
    merged: list[dict] = []
    for msg in history:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1] = {"role": msg["role"], "content": merged[-1]["content"] + "\n" + msg["content"]}
        else:
            merged.append(dict(msg))
    return merged
