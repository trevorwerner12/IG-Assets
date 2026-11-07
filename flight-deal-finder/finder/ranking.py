"""Scores each flight 0-100 on value, using weights you choose."""

DEFAULT_WEIGHTS = {"price": 50, "time": 25, "stops": 15, "fit": 10}
STOP_SCORES = {0: 1.0, 1: 0.6, 2: 0.25}
PREFERRED_BONUS = 5
HOURS_PENALTY = 0.25  # fit score lost per hour outside your time window


def _hour(t):
    """'2026-03-05 14:30' -> 14.5"""
    try:
        hh, mm = t.split(" ")[-1].split(":")[:2]
        return int(hh) + int(mm) / 60
    except (AttributeError, ValueError):
        return None


def _distance(h, start, end):
    if h is None or start is None or end is None:
        return 0
    if start <= end:
        if start <= h <= end:
            return 0
        return min(abs(h - start), abs(h - end))
    # window wraps past midnight, e.g. 22 -> 6
    if h >= start or h <= end:
        return 0
    return min(abs(h - start), abs(h - end))


def time_fit(opt, windows):
    """1.0 = inside your departure/arrival windows; drops for each hour outside."""
    if not windows:
        return 1.0
    off = _distance(_hour(opt.get("dep_time")), windows.get("dep_start"), windows.get("dep_end"))
    off += _distance(_hour(opt.get("arr_time")), windows.get("arr_start"), windows.get("arr_end"))
    return max(0.0, 1.0 - HOURS_PENALTY * off)


def score_all(options, weights=None, windows=None, preferred=()):
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    total_w = sum(max(0, float(v)) for v in weights.values()) or 1
    priced = [o for o in options if o.get("all_in")]
    if not priced:
        return []
    min_price = min(o["all_in"] for o in priced)
    min_time = min((o["total_minutes"] for o in priced if o.get("total_minutes")), default=1)
    preferred = {p.strip().upper() for p in preferred if p.strip()}

    for o in priced:
        parts = {
            "price": min_price / o["all_in"],
            "time": (min_time / o["total_minutes"]) if o.get("total_minutes") else 0.5,
            "stops": STOP_SCORES.get(o.get("stops", 0), 0.0),
            "fit": time_fit(o, windows),
        }
        s = sum(parts[k] * max(0, float(weights[k])) for k in parts) / total_w * 100
        o["is_preferred"] = bool(preferred and (
            (o.get("airline_code") or "").upper() in preferred
            or any(p.lower() in (o.get("airline") or "").lower() for p in preferred)
        ))
        if o["is_preferred"]:
            s += PREFERRED_BONUS
        o["score"] = round(min(100.0, s), 1)
        o["fit"] = round(parts["fit"], 2)
    priced.sort(key=lambda o: (-o["score"], o["all_in"]))
    return priced


def picks(ranked, fastest_under=None):
    if not ranked:
        return {}
    cheapest = min(ranked, key=lambda o: (o["all_in"], o.get("total_minutes") or 1e9))
    limit = fastest_under or round(cheapest["all_in"] * 1.25)
    under = [o for o in ranked if o["all_in"] <= limit and o.get("total_minutes")]
    fastest = min(under, key=lambda o: (o["total_minutes"], o["all_in"])) if under else None
    return {"best": ranked[0], "cheapest": cheapest, "fastest": fastest, "fastest_limit": limit}
