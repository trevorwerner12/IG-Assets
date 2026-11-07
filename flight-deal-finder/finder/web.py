"""The local web page (Flask)."""
import calendar as pycal
import time
from datetime import date, datetime
from urllib.parse import parse_qsl

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from . import alerts, config, search, storage
from .serpapi_client import ApiError, account_info, forget_account_cache

app = Flask(__name__)
app.secret_key = "local-only-flight-finder"


# ---------------- helpers ----------------
@app.template_filter("money")
def money(v):
    return "—" if v is None else f"${v:,.0f}"


@app.template_filter("clock")
def clock(t):
    """'2026-03-05 14:30' -> '2:30 PM'"""
    try:
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
        return f"{dt.hour % 12 or 12}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"
    except (TypeError, ValueError):
        return t or "?"


@app.template_filter("nice_date")
def nice_date(d):
    try:
        dt = date.fromisoformat(d)
        return f"{dt.strftime('%a %b')} {dt.day}"
    except (TypeError, ValueError):
        return d or ""


@app.template_filter("ago")
def ago(ts):
    if not ts:
        return "never"
    mins = int((time.time() - ts) // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    if mins < 60 * 24:
        return f"{mins // 60} h ago"
    dt = datetime.fromtimestamp(ts)
    return f"{dt.strftime('%b')} {dt.day}"


@app.context_processor
def globals_():
    return {"demo": config.demo_mode(), "account": account_info(),
            "unseen": storage.unseen_events_count(), "cfg": config}


def calendar_grid(cal):
    """Turn [{depart, price...}] into month grids for the price calendar."""
    by_day = {x["depart"]: x for x in cal}
    prices = [x["price"] for x in cal if x.get("price")]
    lo, hi = (min(prices), max(prices)) if prices else (0, 0)
    months = sorted({d[:7] for d in by_day})
    out = []
    for m in months:
        y, mo = map(int, m.split("-"))
        weeks = []
        for week in pycal.Calendar(firstweekday=6).monthdatescalendar(y, mo):
            row = []
            for d in week:
                iso = d.isoformat()
                cell = {"day": d.day, "in_month": d.month == mo, "info": by_day.get(iso)}
                if cell["info"] and cell["info"].get("price") and hi > lo:
                    cell["heat"] = round((cell["info"]["price"] - lo) / (hi - lo), 2)
                elif cell["info"] and cell["info"].get("price"):
                    cell["heat"] = 0
                row.append(cell)
            weeks.append(row)
        out.append({"title": date(y, mo, 1).strftime("%B %Y"), "weeks": weeks})
    return out


def find_option(results, opt_id):
    for o in (results or {}).get("options") or []:
        if o["id"] == opt_id:
            return o
    abort(404)


def load(search_id):
    s = storage.get_search(search_id)
    if not s:
        abort(404)
    return s


# ---------------- pages ----------------
@app.get("/")
def index():
    prefill = {}
    if request.args.get("from"):
        s = storage.get_search(int(request.args["from"]))
        if s:
            prefill = s["criteria"]
    for k, v in request.args.items():
        if k != "from":
            prefill[k] = v
    return render_template("index.html", c=prefill, recent=storage.list_searches(8))


@app.post("/search")
def do_search():
    c = search.criteria_from_form(request.form)
    try:
        r = search.run(c, force_refresh=bool(request.form.get("refresh")),
                       confirmed=bool(request.form.get("confirmed")))
    except (ValueError, ApiError) as e:
        flash(str(e), "error")
        return render_template("index.html", c=c, recent=storage.list_searches(8))
    if r.get("needs_confirm"):
        return render_template("confirm.html", c=c, r=r, form=request.form)
    forget_account_cache()
    if r["kind"] == "explore":
        cheapest = r["destinations"][0]["price"] if r["destinations"] else None
    else:
        cheapest = r["picks"]["cheapest"]["all_in"] if r["options"] else None
    sid = storage.save_search(c, search.describe(c), cheapest, r)
    return redirect(url_for("results", search_id=sid))


@app.get("/results/<int:search_id>")
def results(search_id):
    s = load(search_id)
    r = s["results"]
    show_all = request.args.get("all") == "1"
    grid = calendar_grid(r.get("calendar") or []) if r.get("kind") == "flights" and len(r.get("calendar") or []) > 1 else []
    return render_template("results.html", s=s, c=s["criteria"], r=r, grid=grid, show_all=show_all)


@app.post("/results/<int:search_id>/rerank")
def rerank(search_id):
    """Change the weights / bag counts and re-rank WITHOUT using any API credits."""
    s = load(search_id)
    c = dict(s["criteria"])
    for k in ("w_price", "w_time", "w_stops", "w_fit", "carry_on", "checked"):
        try:
            c[k] = max(0, int(request.form.get(k, c[k])))
        except (TypeError, ValueError):
            pass
    try:
        c["fastest_under"] = float(request.form["fastest_under"]) if request.form.get("fastest_under") else None
    except ValueError:
        pass
    r = s["results"]
    opts = search.finish_options(r["options"], c, r.get("round_trip", False))
    r["options"] = opts
    r["picks"] = search.ranking.picks(opts, c["fastest_under"])
    for cell in r.get("calendar") or []:
        day = [o["all_in"] for o in opts if o["outbound_date"] == cell["depart"]]
        if day:
            cell["price"] = min(day)
    prices = [x["price"] for x in r.get("calendar") or [] if x.get("price")]
    for x in r.get("calendar") or []:
        x["cheapest"] = bool(x.get("price")) and x["price"] == min(prices)
    storage.update_search(search_id, c, search.describe(c), r["picks"]["cheapest"]["all_in"] if opts else None, r)
    flash("Re-ranked with your new weights (no credits used).", "ok")
    return redirect(url_for("results", search_id=search_id))


@app.post("/results/<int:search_id>/refresh")
def refresh(search_id):
    s = load(search_id)
    try:
        r = search.run(s["criteria"], force_refresh=True, confirmed=True)
    except (ValueError, ApiError) as e:
        flash(str(e), "error")
        return redirect(url_for("results", search_id=search_id))
    forget_account_cache()
    c = s["criteria"]
    cheapest = (r["picks"]["cheapest"]["all_in"] if r.get("options") else None) if r["kind"] == "flights" \
        else (r["destinations"][0]["price"] if r["destinations"] else None)
    sid = storage.save_search(c, search.describe(c), cheapest, r)
    return redirect(url_for("results", search_id=sid))


@app.get("/results/<int:search_id>/returns/<opt_id>")
def returns(search_id, opt_id):
    s = load(search_id)
    out = find_option(s["results"], opt_id)
    try:
        rets, info = search.returns_for(s["criteria"], out)
    except ApiError as e:
        flash(str(e), "error")
        return redirect(url_for("results", search_id=search_id))
    forget_account_cache()
    return render_template("returns.html", s=s, c=s["criteria"], out=out, rets=rets, info=info)


@app.get("/results/<int:search_id>/book/<opt_id>")
def book(search_id, opt_id):
    s = load(search_id)
    c = s["criteria"]
    out_id = request.args.get("out")
    if out_id:  # a return flight of a round trip
        out = find_option(s["results"], out_id)
        rets, _ = search.returns_for(c, out)
        opt = next((o for o in rets if o["id"] == opt_id), None) or abort(404)
    else:
        opt = find_option(s["results"], opt_id)
    if not opt.get("booking_token"):
        abort(400)
    try:
        links, info, gurl = search.booking_options(c, opt)
    except ApiError as e:
        flash(str(e), "error")
        return redirect(url_for("results", search_id=search_id))
    for l in links:
        l["fields"] = parse_qsl(l.get("post_data") or "")
    forget_account_cache()
    return render_template("book.html", s=s, opt=opt, links=links, info=info, gurl=gurl,
                           out=find_option(s["results"], out_id) if out_id else None)


@app.post("/setup/key")
def setup_key():
    key = request.form.get("key", "").strip()
    if len(key) < 20 or not key.isalnum():
        flash("That doesn't look like a SerpApi key (it's a long string of letters and numbers).", "error")
        return redirect(url_for("index"))
    config.save_api_key(key)
    forget_account_cache()
    info = account_info()
    if info and info.get("error"):
        flash(f"Saved, but SerpApi says: {info['error']}", "error")
    else:
        flash("API key saved to your .env file. You're now searching real flights!", "ok")
    return redirect(url_for("index"))


@app.get("/history")
def history():
    return render_template("history.html", searches=storage.list_searches(100))


@app.post("/history/<int:search_id>/delete")
def delete_history(search_id):
    storage.delete_search(search_id)
    return redirect(url_for("history"))


@app.post("/cache/clear")
def clear_cache():
    storage.cache_clear()
    flash("Cache cleared. Your next searches will fetch fresh prices (uses credits).", "ok")
    return redirect(request.referrer or url_for("index"))


# ---------------- price alerts ----------------
@app.get("/alerts")
def alerts_page():
    page = render_template("alerts.html", alerts=storage.list_alerts(), events=storage.list_events())
    storage.mark_events_seen()
    return page


@app.post("/alerts/new/<int:search_id>")
def new_alert(search_id):
    s = load(search_id)
    try:
        target = float(request.form["target"])
    except (KeyError, ValueError):
        flash("Please enter a target price.", "error")
        return redirect(url_for("results", search_id=search_id))
    storage.add_alert(s["summary"], s["criteria"], target)
    flash(f"Alert saved: I'll tell you when the all-in price drops below ${target:,.0f}.", "ok")
    return redirect(url_for("alerts_page"))


@app.post("/alerts/<int:alert_id>/<action>")
def alert_action(alert_id, action):
    if action == "delete":
        storage.delete_alert(alert_id)
    elif action == "pause":
        storage.update_alert(alert_id, active=0)
    elif action == "resume":
        storage.update_alert(alert_id, active=1)
    elif action == "check":
        a = next((x for x in storage.list_alerts() if x["id"] == alert_id), None)
        if a:
            msg = alerts.check_one(a)
            flash(msg, "ok")
            forget_account_cache()
    return redirect(url_for("alerts_page"))
