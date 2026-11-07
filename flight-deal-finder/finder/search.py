"""Runs a search: expands dates, calls SerpApi (or cache), filters, prices and ranks."""
import hashlib

from . import airports, config, dates, pricing, ranking
from .serpapi_client import ApiError, fetch, is_cached

CABINS = {"economy": 1, "premium": 2, "business": 3, "first": 4}
# our "max stops" -> SerpApi 'stops' value
STOPS_PARAM = {"any": 0, "0": 1, "1": 2, "2": 3}


# ---------------- form -> criteria ----------------
def _num(v, cast=float):
    try:
        return cast(v) if str(v).strip() != "" else None
    except (TypeError, ValueError):
        return None


def _codes(v):
    return ",".join(c.strip().upper() for c in (v or "").replace(" ", ",").split(",") if c.strip())


def criteria_from_form(f):
    """f: a dict-like of form fields -> clean criteria dict (stored with history/alerts)."""
    def g(k, d=""):
        v = f.get(k)
        if v is None or v == "":
            v = d
        return v.strip() if isinstance(v, str) else v

    def n(k, default, cast=int):
        v = _num(g(k), cast)
        return default if v is None else v

    c = {
        "origin": g("origin", "PHX") or "PHX",
        "include_nearby": g("include_nearby") in ("on", "1", "true", True),
        "destination": g("destination"),
        "trip": g("trip", "round") or "round",
        "date_mode": g("date_mode", "exact") or "exact",
        "depart": g("depart"),
        "return": g("return"),
        "flex_days": _num(g("flex_days"), int) or 0,
        "month": g("month"),
        "weekend_pattern": g("weekend_pattern", "fri-sun") or "fri-sun",
        "max_stops": g("max_stops", "any") or "any",
        "max_hours": _num(g("max_hours")),
        "max_layover_hours": _num(g("max_layover_hours")),
        "min_layover_minutes": _num(g("min_layover_minutes"), int),
        "only_airlines": _codes(g("only_airlines")),
        "exclude_airlines": _codes(g("exclude_airlines")),
        "preferred_airlines": _codes(g("preferred_airlines")),
        "dep_start": _num(g("dep_start"), int), "dep_end": _num(g("dep_end"), int),
        "arr_start": _num(g("arr_start"), int), "arr_end": _num(g("arr_end"), int),
        "strict_times": g("strict_times") in ("on", "1", "true", True),
        "cabin": g("cabin", "economy") or "economy",
        "adults": _num(g("adults"), int) or 1,
        "carry_on": n("carry_on", 1),
        "checked": n("checked", 0),
        "w_price": n("w_price", 50),
        "w_time": n("w_time", 25),
        "w_stops": n("w_stops", 15),
        "w_fit": n("w_fit", 10),
        "fastest_under": _num(g("fastest_under")),
    }
    c["flex_days"] = max(0, min(3, c["flex_days"]))
    return c


def describe(c):
    dest = c["destination"] or "?"
    trip = "round trip" if c["trip"] == "round" else "one-way"
    if c["date_mode"] == "weekends":
        when = f"weekends in {c['month']} ({c['weekend_pattern']})"
    else:
        when = c["depart"] + (f" → {c['return']}" if c["trip"] == "round" and c["return"] else "")
        if c["date_mode"] == "flex" and c["flex_days"]:
            when += f" (±{c['flex_days']} days)"
    origin = c["origin"] + (" + nearby" if c["include_nearby"] else "")
    return f"{origin} → {dest}, {trip}, {when}"


# ---------------- criteria -> API params ----------------
def origin_codes(c):
    codes = airports.parse_airports(c["origin"]) or "PHX"
    return airports.with_nearby(codes) if c["include_nearby"] else codes


def windows(c):
    w = {k: c.get(k) for k in ("dep_start", "dep_end", "arr_start", "arr_end")}
    return w if any(v is not None for v in w.values()) else None


def base_params(c, outbound, ret):
    round_trip = c["trip"] == "round"
    p = {
        "engine": "google_flights",
        "departure_id": origin_codes(c),
        "arrival_id": airports.parse_airports(c["destination"]),
        "outbound_date": outbound,
        "type": 1 if round_trip else 2,
        "travel_class": CABINS.get(c["cabin"], 1),
        "adults": c["adults"],
        "stops": STOPS_PARAM.get(str(c["max_stops"]), 0),
        "currency": "USD", "hl": "en", "gl": "us",
    }
    if round_trip:
        p["return_date"] = ret
    if c["only_airlines"]:
        p["include_airlines"] = c["only_airlines"]
    elif c["exclude_airlines"]:
        p["exclude_airlines"] = c["exclude_airlines"]
    if c["max_hours"]:
        p["max_duration"] = int(c["max_hours"] * 60)
    if c["max_layover_hours"] or c["min_layover_minutes"]:
        lo = c["min_layover_minutes"] or 30
        hi = int(c["max_layover_hours"] * 60) if c["max_layover_hours"] else 24 * 60
        p["layover_duration"] = f"{lo},{hi}"
    if c["strict_times"] and windows(c):
        ds = c["dep_start"] if c["dep_start"] is not None else 0
        de = c["dep_end"] if c["dep_end"] is not None else 23
        times = f"{ds},{de}"
        if c["arr_start"] is not None or c["arr_end"] is not None:
            a1 = c["arr_start"] if c["arr_start"] is not None else 0
            a2 = c["arr_end"] if c["arr_end"] is not None else 23
            times += f",{a1},{a2}"
        p["outbound_times"] = times
    return p


def validate(c):
    if c["only_airlines"] and c["exclude_airlines"]:
        raise ValueError("Use either 'Only these airlines' or 'Exclude airlines', not both.")
    if not c["destination"]:
        raise ValueError("Please enter a destination (airport code, city, or 'anywhere').")
    if not airports.is_anywhere(c["destination"]) and not airports.parse_airports(c["destination"]):
        raise ValueError("Couldn't understand the destination.")


def date_list(c):
    return dates.date_pairs(c["date_mode"], c["depart"], c["return"], c["flex_days"],
                            c["month"], c["weekend_pattern"], round_trip=c["trip"] == "round")


# ---------------- normalize SerpApi results ----------------
def _hhmm(minutes):
    if not minutes:
        return "?"
    return f"{minutes // 60}h {minutes % 60:02d}m"


def normalize_group(g, outbound, ret, search_url):
    legs = g.get("flights") or []
    if not legs:
        return None
    first, last = legs[0], legs[-1]
    fn = first.get("flight_number") or ""
    code = fn.split(" ")[0] if " " in fn else ""
    airline_names = []
    for leg in legs:
        if leg.get("airline") and leg["airline"] not in airline_names:
            airline_names.append(leg["airline"])
    layovers = [{"airport": l.get("id") or l.get("name"), "minutes": l.get("duration") or 0,
                 "overnight": bool(l.get("overnight"))} for l in (g.get("layovers") or [])]
    key = "|".join(leg.get("flight_number", "") for leg in legs) + f"|{outbound}|{ret}"
    return {
        "id": hashlib.md5(key.encode()).hexdigest()[:10],
        "airline": airline_names[0] if airline_names else "?",
        "airlines": " + ".join(airline_names),
        "airline_code": code,
        "airline_logo": g.get("airline_logo") or first.get("airline_logo"),
        "flight_numbers": ", ".join(leg.get("flight_number", "") for leg in legs),
        "origin": (first.get("departure_airport") or {}).get("id"),
        "destination": (last.get("arrival_airport") or {}).get("id"),
        "dep_time": (first.get("departure_airport") or {}).get("time"),
        "arr_time": (last.get("arrival_airport") or {}).get("time"),
        "stops": len(legs) - 1,
        "layovers": layovers,
        "total_minutes": g.get("total_duration") or sum(leg.get("duration") or 0 for leg in legs),
        "price": g.get("price"),
        "extensions": g.get("extensions") or [],
        "legs": [{"from": (l.get("departure_airport") or {}).get("id"),
                  "to": (l.get("arrival_airport") or {}).get("id"),
                  "dep": (l.get("departure_airport") or {}).get("time"),
                  "arr": (l.get("arrival_airport") or {}).get("time"),
                  "airline": l.get("airline"), "flight_number": l.get("flight_number"),
                  "travel_class": l.get("travel_class"), "extensions": l.get("extensions") or [],
                  "often_delayed": bool(l.get("often_delayed_by_over_30_min")),
                  "airplane": l.get("airplane")} for l in legs],
        "outbound_date": outbound,
        "return_date": ret,
        "departure_token": g.get("departure_token"),
        "booking_token": g.get("booking_token"),
        "search_url": search_url,
    }


def options_from(data, outbound, ret):
    url = (data.get("search_metadata") or {}).get("google_flights_url")
    out = []
    for g in (data.get("best_flights") or []) + (data.get("other_flights") or []):
        o = normalize_group(g, outbound, ret, url)
        if o and o["price"] is not None:
            out.append(o)
    return out


def local_filter(options, c):
    """Double-check the filters ourselves (the API is sometimes loose)."""
    out = []
    max_stops = None if c["max_stops"] == "any" else int(c["max_stops"])
    only = set(c["only_airlines"].split(",")) if c["only_airlines"] else None
    excl = set(c["exclude_airlines"].split(",")) if c["exclude_airlines"] else set()
    w = windows(c) if c["strict_times"] else None
    for o in options:
        if max_stops is not None and o["stops"] > max_stops:
            continue
        if c["max_hours"] and o["total_minutes"] > c["max_hours"] * 60:
            continue
        lays = [l["minutes"] for l in o["layovers"]]
        if lays and c["max_layover_hours"] and max(lays) > c["max_layover_hours"] * 60:
            continue
        if lays and c["min_layover_minutes"] and min(lays) < c["min_layover_minutes"]:
            continue
        codes = {(leg.get("flight_number") or " ").split(" ")[0] for leg in o["legs"]}
        if only and not codes & only:
            continue
        if excl and codes & excl:
            continue
        if w and ranking.time_fit(o, w) < 1.0:
            continue
        out.append(o)
    return out


def finish_options(options, c, round_trip):
    for o in options:
        pricing.all_in(o, c["carry_on"], c["checked"], round_trip, config.UNITED_EXPLORER_CARD)
        o["duration_text"] = _hhmm(o["total_minutes"])
    weights = {"price": c["w_price"], "time": c["w_time"], "stops": c["w_stops"], "fit": c["w_fit"]}
    return ranking.score_all(options, weights, windows(c), c["preferred_airlines"].split(","))


# ---------------- main entry points ----------------
def plan(c):
    """How many API credits would this search use? (cached dates are free)"""
    validate(c)
    pairs = date_list(c)
    if airports.is_anywhere(c["destination"]):
        params = [explore_params(c, d, r) for d, r in pairs]
    else:
        params = [base_params(c, d, r) for d, r in pairs]
    need = sum(0 if is_cached(p) else 1 for p in params)
    return pairs, params, need


def run(c, force_refresh=False, confirmed=False):
    pairs, params_list, need = plan(c)
    if force_refresh:
        need = len(params_list)
    if need > config.MAX_CREDITS_PER_SEARCH:
        raise ValueError(f"This search needs {need} API credits, more than your limit of "
                         f"{config.MAX_CREDITS_PER_SEARCH}. Narrow the dates (fewer flexible days).")
    if need > config.CONFIRM_ABOVE_CREDITS and not confirmed:
        return {"needs_confirm": True, "credits": need, "dates": len(pairs)}

    if airports.is_anywhere(c["destination"]):
        return run_explore(c, pairs, params_list, force_refresh)

    round_trip = c["trip"] == "round"
    all_opts, calendar, insights, errors = [], [], {}, []
    used = cached = 0
    stopped = None
    for (d, r), p in zip(pairs, params_list):
        if stopped:
            calendar.append({"depart": d, "return": r, "price": None, "note": "not checked"})
            continue
        try:
            data, info = fetch(p, use_cache=not force_refresh)
        except ApiError as e:
            if e.kind in ("limit", "key", "network"):
                stopped = str(e)
            else:
                errors.append(f"{d}: {e}")
            calendar.append({"depart": d, "return": r, "price": None, "note": "error"})
            continue
        cached += 1 if info.get("cached") else 0
        used += 0 if info.get("cached") or info.get("demo") else 1
        opts = local_filter(options_from(data, d, r), c)
        opts = finish_options(opts, c, round_trip)
        all_opts.extend(opts)
        pi = data.get("price_insights") or {}
        if pi:
            insights[d] = pi
        calendar.append({"depart": d, "return": r,
                         "price": min((o["all_in"] for o in opts), default=None),
                         "level": pi.get("price_level"), "note": "" if opts else "no flights"})

    if stopped and not all_opts:
        raise ApiError(stopped, "limit")
    ranked = finish_options(all_opts, c, round_trip)  # re-score across all dates together
    prices = [x["price"] for x in calendar if x["price"]]
    for x in calendar:
        x["cheapest"] = bool(x["price"]) and x["price"] == min(prices)
    return {
        "kind": "flights",
        "options": ranked,
        "picks": ranking.picks(ranked, c["fastest_under"]),
        "calendar": calendar,
        "insights": insights,
        "credits_used": used, "cached_dates": cached,
        "errors": errors, "stopped": stopped,
        "round_trip": round_trip,
        "demo": config.demo_mode(),
    }


def explore_params(c, d, r):
    p = {"engine": "google_travel_explore", "departure_id": origin_codes(c),
         "outbound_date": d, "type": 1 if c["trip"] == "round" else 2,
         "travel_class": CABINS.get(c["cabin"], 1), "adults": c["adults"],
         "stops": STOPS_PARAM.get(str(c["max_stops"]), 0), "currency": "USD", "hl": "en", "gl": "us"}
    if c["trip"] == "round" and r:
        p["return_date"] = r
    return p


def run_explore(c, pairs, params_list, force_refresh):
    dests, used, stopped = {}, 0, None
    for (d, r), p in zip(pairs, params_list):
        try:
            data, info = fetch(p, use_cache=not force_refresh)
        except ApiError as e:
            stopped = str(e)
            break
        used += 0 if info.get("cached") or info.get("demo") else 1
        for x in data.get("destinations") or []:
            code = (x.get("destination_airport") or {}).get("code") or x.get("destination_airport_code")
            price = x.get("flight_price") or x.get("price")
            if not code or not price:
                continue
            item = {"name": x.get("name"), "country": x.get("country"), "code": code,
                    "price": price, "depart": x.get("start_date") or d, "return": x.get("end_date") or r,
                    "airline": x.get("airline"), "stops": x.get("number_of_stops"),
                    "duration_text": _hhmm(x.get("flight_duration")),
                    "thumbnail": x.get("thumbnail")}
            if code not in dests or price < dests[code]["price"]:
                dests[code] = item
    if stopped and not dests:
        raise ApiError(stopped, "limit")
    return {"kind": "explore", "destinations": sorted(dests.values(), key=lambda x: x["price"]),
            "credits_used": used, "stopped": stopped, "demo": config.demo_mode()}


def returns_for(c, outbound_opt, force_refresh=False):
    """Round trips: fetch return flights for a chosen outbound flight (1 credit, cached)."""
    p = base_params(c, outbound_opt["outbound_date"], outbound_opt["return_date"])
    p.pop("outbound_times", None)
    p["departure_token"] = outbound_opt["departure_token"]
    data, info = fetch(p, use_cache=not force_refresh)
    opts = options_from(data, outbound_opt["outbound_date"], outbound_opt["return_date"])
    for o in opts:
        o["id"] = "r" + o["id"]
    c2 = {**c, "strict_times": False, "dep_start": None, "dep_end": None, "arr_start": None, "arr_end": None}
    opts = finish_options(local_filter(opts, c2), c2, True)
    return opts, info


def booking_options(c, opt):
    """Get the 'book with' links for a flight with a booking_token (1 credit, cached)."""
    p = base_params(c, opt["outbound_date"], opt["return_date"])
    p.pop("outbound_times", None)
    p["booking_token"] = opt["booking_token"]
    data, info = fetch(p)
    out = []
    for b in data.get("booking_options") or []:
        parts = [b["together"]] if b.get("together") else [x for x in (b.get("departing"), b.get("returning")) if x]
        for part in parts:
            req = part.get("booking_request") or {}
            out.append({"book_with": part.get("book_with"), "price": part.get("price"),
                        "title": part.get("option_title"), "url": req.get("url"),
                        "post_data": req.get("post_data"),
                        "separate": not b.get("together"),
                        "baggage": part.get("baggage_prices") or []})
    return out, info, (data.get("search_metadata") or {}).get("google_flights_url")
