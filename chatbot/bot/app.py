"""Twilio webhook server for SMS and WhatsApp.

Twilio POSTs each incoming message to /sms. We answer with empty TwiML right
away (Twilio times out after 15s) and send the real reply through the Twilio
REST API from a background task.
"""

import logging
import os
from typing import Protocol

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from twilio.request_validator import RequestValidator

from .config import Settings
from .responder import Responder
from .store import ConversationStore

log = logging.getLogger(__name__)

EMPTY_TWIML = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
# Twilio handles these itself on SMS (Advanced Opt-Out); the bot stays silent.
OPT_OUT_KEYWORDS = {
    "stop", "stopall", "unsubscribe", "cancel", "end", "quit",
    "start", "unstop", "yes", "help", "info",
}
MAX_SMS_CHARS = 1500


class Sender(Protocol):
    def send(self, from_: str, to: str, body: str) -> None: ...


class TwilioSender:
    def __init__(self, settings: Settings):
        from twilio.rest import Client

        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    def send(self, from_: str, to: str, body: str) -> None:
        self.client.messages.create(from_=from_, to=to, body=body)


class DryRunSender:
    def send(self, from_: str, to: str, body: str) -> None:
        log.info("[dry run] %s -> %s: %s", from_, to, body)


def create_app(
    settings: Settings | None = None,
    responder: Responder | None = None,
    sender: Sender | None = None,
    store: ConversationStore | None = None,
) -> FastAPI:
    settings = settings or Settings()
    responder = responder or Responder(settings)
    sender = sender or (DryRunSender() if settings.dry_run else TwilioSender(settings))
    store = store or ConversationStore(settings.db_path)
    validator = RequestValidator(settings.twilio_auth_token)

    app = FastAPI(title="Text auto-responder")

    def handle(contact: str, bot_number: str, text: str) -> None:
        store.add(contact, "user", text)
        result = responder.respond(store.history(contact, settings.history_turns))
        body = result.reply.strip()[:MAX_SMS_CHARS]
        try:
            sender.send(bot_number, contact, body)
        except Exception:
            log.exception("Failed to send reply to %s", contact)
            return
        store.add(contact, "assistant", body)

        if result.needs_owner and settings.owner_phone:
            owner = settings.owner_phone
            # Notify on the same channel the business number uses.
            if bot_number.startswith("whatsapp:") and not owner.startswith("whatsapp:"):
                owner = f"whatsapp:{owner}"
            note = f"Follow up with {contact}: {result.owner_note}\nThey said: {text[:300]}"
            try:
                sender.send(bot_number, owner, note[:MAX_SMS_CHARS])
            except Exception:
                log.exception("Failed to notify owner")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.post("/sms")
    async def sms(request: Request, background: BackgroundTasks) -> Response:
        form = dict(await request.form())

        if settings.validate_signature:
            url = settings.public_webhook_url or str(request.url)
            signature = request.headers.get("X-Twilio-Signature", "")
            if not validator.validate(url, form, signature):
                raise HTTPException(status_code=403, detail="Invalid Twilio signature")

        contact = form.get("From", "")
        bot_number = form.get("To", "")
        text = (form.get("Body") or "").strip()
        message_sid = form.get("MessageSid", "")

        if not contact or not bot_number:
            raise HTTPException(status_code=400, detail="Missing From/To")
        if message_sid and not store.mark_seen(message_sid):
            return _twiml()  # Twilio retry of a message we already handled
        if _strip_channel(contact) == _strip_channel(settings.owner_phone):
            return _twiml()  # the owner texting the bot number
        if text.lower() in OPT_OUT_KEYWORDS:
            return _twiml()
        if not text:
            if int(form.get("NumMedia", "0") or 0) == 0:
                return _twiml()
            text = "[sent a photo or attachment]"

        background.add_task(handle, contact, bot_number, text)
        return _twiml()

    return app


def _twiml() -> Response:
    return Response(content=EMPTY_TWIML, media_type="application/xml")


def _strip_channel(number: str) -> str:
    return number.removeprefix("whatsapp:").strip()


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(create_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
