"""Chat with the bot in your terminal, no Twilio needed.

    python -m bot.cli
"""

from .config import Settings
from .responder import Responder
from .store import ConversationStore


def main() -> None:
    settings = Settings()
    responder = Responder(settings)
    store = ConversationStore(":memory:")
    contact = "cli"
    print("Text the bot (Ctrl+C to quit).\n")
    try:
        while True:
            text = input("you> ").strip()
            if not text:
                continue
            store.add(contact, "user", text)
            result = responder.respond(store.history(contact, settings.history_turns))
            store.add(contact, "assistant", result.reply)
            print(f"bot> {result.reply}")
            if result.needs_owner:
                print(f"     [needs owner: {result.owner_note}]")
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
