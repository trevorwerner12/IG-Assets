"""Price alerts: re-run saved searches and notify when the all-in price drops below target."""
import threading
import time

import requests

from . import config, search, storage
from .serpapi_client import ApiError


def notify(title, message):
    """In-app notice always; phone/desktop push via ntfy.sh if NTFY_TOPIC is set."""
    if config.NTFY_TOPIC:
        try:
            requests.post(f"https://ntfy.sh/{config.NTFY_TOPIC}", data=message.encode(),
                          headers={"Title": title, "Tags": "airplane"}, timeout=15)
        except requests.RequestException:
            pass


def check_one(alert):
    """Runs one alert (fresh prices). Returns a short status message."""
    c = alert["criteria"]
    try:
        # Reuse results up to 1 hour old (so checking right after a search is free).
        r = search.run(c, confirmed=True, max_age_hours=1)
    except (ValueError, ApiError) as e:
        expired = "in the past" in str(e)
        storage.update_alert(alert["id"], last_checked=time.time(),
                             last_error="Trip dates have passed — alert paused." if expired else str(e),
                             **({"active": 0} if expired else {}))
        return f"Couldn't check '{alert['name']}': {e}"

    if r["kind"] == "explore":
        price = r["destinations"][0]["price"] if r["destinations"] else None
        where = r["destinations"][0]["name"] if r["destinations"] else ""
    else:
        best = r["picks"].get("cheapest") if r["options"] else None
        price = best["all_in"] if best else None
        where = f"{best['airlines']} on {best['outbound_date']}" if best else ""
    storage.update_alert(alert["id"], last_checked=time.time(), last_price=price, last_error=None)

    if price is not None and price < alert["target"]:
        msg = (f"{alert['name']}: all-in price is now ${price:,.0f} "
               f"(your target ${alert['target']:,.0f}) — {where}")
        # Don't repeat the same notice unless the price dropped further.
        if alert.get("last_price") is None or price < alert["last_price"] or not alert.get("triggered_at"):
            storage.add_event(alert["id"], price, msg)
            storage.update_alert(alert["id"], triggered_at=time.time())
            notify("✈️ Flight price drop!", msg)
        return "Price drop! " + msg
    if price is None:
        return f"'{alert['name']}': no flights found right now."
    return f"'{alert['name']}': cheapest all-in is ${price:,.0f} (target ${alert['target']:,.0f}). No alert yet."


def check_due(force=False):
    """Check every active alert that hasn't been checked in ALERT_CHECK_HOURS."""
    results = []
    for a in storage.list_alerts(active_only=True):
        due = force or not a["last_checked"] or time.time() - a["last_checked"] > config.ALERT_CHECK_HOURS * 3600
        if due:
            results.append(check_one(a))
    return results


def start_background_checker():
    """While the app is open, check alerts every few minutes for ones that are due."""
    def loop():
        while True:
            try:
                check_due()
            except Exception as e:  # never crash the web page because of an alert
                print("Alert check problem:", e)
            time.sleep(15 * 60)

    threading.Thread(target=loop, daemon=True).start()


if __name__ == "__main__":
    # Lets you run the checks from a scheduler:  python -m finder.alerts
    for line in check_due(force=True) or ["No active alerts."]:
        print(line)
