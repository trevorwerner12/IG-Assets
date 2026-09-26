from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from bot.app import create_app
from bot.config import Settings
from bot.responder import Reply, _merge_consecutive
from bot.store import ConversationStore

URL = "https://bot.example.com/sms"
TOKEN = "test-auth-token"
BOT = "+15550000000"
USER = "+15551112222"
OWNER = "+15559998888"


class FakeResponder:
    def __init__(self, reply: Reply):
        self.reply = reply
        self.calls: list[list[dict]] = []

    def respond(self, history):
        self.calls.append(history)
        return self.reply


class FakeSender:
    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    def send(self, from_, to, body):
        self.sent.append((from_, to, body))


def make(reply=None, validate=True):
    settings = Settings(
        twilio_auth_token=TOKEN,
        public_webhook_url=URL,
        validate_signature=validate,
        owner_phone=OWNER,
        persona="test persona",
    )
    responder = FakeResponder(reply or Reply(reply="Hi there", needs_owner=False, owner_note=""))
    sender = FakeSender()
    store = ConversationStore(":memory:")
    client = TestClient(create_app(settings, responder, sender, store))
    return client, responder, sender, store


def post(client, form, sign=True):
    headers = {}
    if sign:
        headers["X-Twilio-Signature"] = RequestValidator(TOKEN).compute_signature(URL, form)
    return client.post("/sms", data=form, headers=headers)


def msg(body, sid="SM1", frm=USER, to=BOT):
    return {"From": frm, "To": to, "Body": body, "MessageSid": sid, "NumMedia": "0"}


def test_replies_and_stores_history():
    client, responder, sender, store = make()
    r = post(client, msg("Do you deliver to Springfield?"))
    assert r.status_code == 200
    assert "<Response>" in r.text
    assert sender.sent == [(BOT, USER, "Hi there")]
    assert responder.calls[0] == [{"role": "user", "content": "Do you deliver to Springfield?"}]
    assert [m["role"] for m in store.history(USER, 10)] == ["user", "assistant"]


def test_rejects_bad_signature():
    client, _, sender, _ = make()
    r = client.post("/sms", data=msg("hi"), headers={"X-Twilio-Signature": "nope"})
    assert r.status_code == 403
    assert sender.sent == []


def test_ignores_twilio_retries():
    client, responder, sender, _ = make()
    post(client, msg("hi", sid="SMdup"))
    post(client, msg("hi", sid="SMdup"))
    assert len(responder.calls) == 1
    assert len(sender.sent) == 1


def test_stays_silent_on_opt_out_keywords():
    client, responder, sender, _ = make()
    post(client, msg("STOP"))
    assert responder.calls == [] and sender.sent == []


def test_ignores_owner_texting_bot():
    client, responder, _, _ = make()
    post(client, msg("test", frm=OWNER))
    assert responder.calls == []


def test_notifies_owner_on_handoff():
    reply = Reply(reply="He'll call you back shortly.", needs_owner=True, owner_note="Wants a quote")
    client, _, sender, _ = make(reply)
    post(client, msg("How much for 200 gallons?"))
    assert sender.sent[0] == (BOT, USER, "He'll call you back shortly.")
    assert sender.sent[1][1] == OWNER
    assert "Wants a quote" in sender.sent[1][2]


def test_whatsapp_numbers_round_trip():
    client, _, sender, _ = make()
    post(client, msg("hello", frm=f"whatsapp:{USER}", to=f"whatsapp:{BOT}"))
    assert sender.sent == [(f"whatsapp:{BOT}", f"whatsapp:{USER}", "Hi there")]


def test_media_only_message():
    client, responder, _, _ = make()
    form = msg("")
    form["NumMedia"] = "1"
    post(client, form)
    assert responder.calls[0][-1]["content"] == "[sent a photo or attachment]"


def test_merge_consecutive_user_texts():
    merged = _merge_consecutive([
        {"role": "user", "content": "hey"},
        {"role": "user", "content": "you there?"},
        {"role": "assistant", "content": "Yep"},
    ])
    assert merged == [
        {"role": "user", "content": "hey\nyou there?"},
        {"role": "assistant", "content": "Yep"},
    ]
