# Text auto-responder (SMS / WhatsApp)

Answers incoming texts in the voice of a 49-year-old part owner of an oil
business, using Claude. Messages arrive through a Twilio webhook, and the same
server handles both SMS and WhatsApp. When something needs the real owner
(quotes, billing, complaints, emergencies, anything it doesn't know), it texts
the owner a one-line summary.

## How it works

```
texter ──SMS/WhatsApp──> Twilio ──POST /sms──> bot/app.py
                                                 │  verify X-Twilio-Signature
                                                 │  skip retries, STOP/HELP, owner's own texts
                                                 ▼
                                   bot/responder.py (Claude, structured reply)
                                                 │  {reply, needs_owner, owner_note}
                                                 ▼
                         Twilio REST API ──> texter   (+ owner alert if needs_owner)
```

- `bot/persona.md` holds who he is, the business facts, his voice and when to hand off. **Fill in the `[bracketed]` fields.** The bot won't invent anything left in brackets.
- `bot/store.py` keeps per-number history in SQLite, so replies have context across restarts.
- Guardrails are in `RULES` in `bot/responder.py`: it keeps replies short, never asks for money or payment details, never takes on a romantic role, says it's his automated assistant if someone sincerely asks, and sends emergencies to 911.

## Setup

```bash
cd chatbot
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill it in, then: set -a; . ./.env; set +a
```

Try it in the terminal first (needs only `ANTHROPIC_API_KEY`):

```bash
python -m bot.cli
```

Run the server:

```bash
python -m bot.app            # listens on :8000
ngrok http 8000              # or deploy anywhere with a public HTTPS URL
```

In the Twilio console, set **A message comes in → Webhook → HTTP POST** to
`https://<your-host>/sms` on:
- **SMS:** Phone Numbers → your number → Messaging.
- **WhatsApp:** Messaging → Senders → WhatsApp senders (or the Sandbox settings for testing).

Set `PUBLIC_WEBHOOK_URL` to that exact URL so signature checks pass behind the tunnel or proxy.
Use `DRY_RUN=true` to log replies instead of sending them.

## Notes

- Twilio's Advanced Opt-Out handles STOP/START/HELP on SMS; the bot stays silent on those words.
- WhatsApp only allows free-form replies within 24 hours of the customer's last message. That's fine here, since the bot only ever replies.
- Default model is `claude-opus-5` at `low` effort, which is quick enough for texting. Change it with `BOT_MODEL` / `BOT_EFFORT`.

## Tests

```bash
python -m pytest
```
