"""Fake SerpApi responses (same shape as the real ones) for DEMO mode and tests.

Used automatically when no SERPAPI_KEY is set, so you can try the app for free.
"""
import hashlib
import random
from datetime import datetime, timedelta

AIRLINES = [
    # name, code, base price factor, hub-ish nonstop chance
    ("American", "AA", 1.00, 0.6),
    ("Southwest", "WN", 0.90, 0.6),
    ("United", "UA", 1.05, 0.3),
    ("Delta", "DL", 1.10, 0.3),
    ("Alaska", "AS", 1.00, 0.3),
    ("Frontier", "F9", 0.55, 0.4),
    ("Spirit", "NK", 0.55, 0.3),
    ("Sun Country", "SY", 0.70, 0.3),
]
HUBS = ["DEN", "DFW", "ORD", "SLC", "LAS", "ATL", "SEA", "IAH"]
EXPLORE = [("Denver", "DEN", "United States"), ("Seattle", "SEA", "United States"),
           ("Chicago", "ORD", "United States"), ("San Diego", "SAN", "United States"),
           ("New York", "JFK", "United States"), ("Cancún", "CUN", "Mexico"),
           ("Honolulu", "HNL", "United States"), ("Nashville", "BNA", "United States"),
           ("Portland", "PDX", "United States"), ("Boston", "BOS", "United States")]


def _rng(params):
    seed = hashlib.md5(repr(sorted(params.items())).encode()).hexdigest()
    return random.Random(int(seed[:8], 16))


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


def _group(rng, origin, dest, day, cabin, round_trip, token_kind, idx):
    name, code, factor, nonstop = rng.choice(AIRLINES)
    stops = 0 if rng.random() < nonstop else (1 if rng.random() < 0.8 else 2)
    dep = datetime.fromisoformat(day) + timedelta(hours=rng.randint(5, 21), minutes=rng.choice([0, 15, 30, 45]))
    legs, layovers = [], []
    cur, here = dep, origin
    airports_chain = [origin] + rng.sample(HUBS, stops) + [dest]
    total = 0
    for i in range(stops + 1):
        dur = rng.randint(70, 260)
        arr = cur + timedelta(minutes=dur)
        legs.append({
            "departure_airport": {"name": airports_chain[i] + " Airport", "id": airports_chain[i], "time": _fmt(cur)},
            "arrival_airport": {"name": airports_chain[i + 1] + " Airport", "id": airports_chain[i + 1], "time": _fmt(arr)},
            "duration": dur, "airplane": rng.choice(["Boeing 737", "Airbus A320", "Airbus A321"]),
            "airline": name, "travel_class": cabin, "flight_number": f"{code} {rng.randint(100, 2999)}",
            "extensions": ["Average legroom (31 in)", "Wi-Fi for a fee"],
            "often_delayed_by_over_30_min": rng.random() < 0.1,
        })
        total += dur
        if i < stops:
            lay = rng.randint(40, 420)
            layovers.append({"duration": lay, "name": airports_chain[i + 1] + " Airport",
                             "id": airports_chain[i + 1], "overnight": lay > 360})
            total += lay
            arr = arr + timedelta(minutes=lay)
        cur = arr
    price = int((150 + rng.randint(0, 250)) * factor * (2 if round_trip else 1) * (1 + 0.15 * stops * -1 + 0.2))
    if cabin != "Economy":
        price *= 3
    ext = []
    if rng.random() < 0.3 and name in ("United", "American", "Delta"):
        ext = ["Basic economy", "Carry-on bag not included"] if name == "United" else ["Basic economy"]
        price = int(price * 0.85)
        for leg in legs:
            leg["travel_class"] = "Economy"
    g = {"flights": legs, "layovers": layovers or None, "total_duration": total, "price": price,
         "type": "Round trip" if round_trip else "One way", "airline_logo": "", "extensions": ext}
    if not layovers:
        g.pop("layovers")
    g[token_kind] = f"demo-{token_kind}-{idx}-{code}"
    return g


def fake_response(params):
    rng = _rng(params)
    engine = params.get("engine")
    url = "https://www.google.com/travel/flights"
    meta = {"status": "Success", "google_flights_url": url}

    if engine == "google_travel_explore":
        dests = []
        for city, code, country in rng.sample(EXPLORE, 8):
            dests.append({"name": city, "country": country, "destination_airport": {"code": code},
                          "flight_price": rng.randint(89, 640), "start_date": params.get("outbound_date"),
                          "end_date": params.get("return_date"), "airline": rng.choice(AIRLINES)[0],
                          "number_of_stops": rng.choice([0, 0, 1]), "flight_duration": rng.randint(70, 400)})
        return {"search_metadata": meta, "destinations": dests}

    if params.get("booking_token"):
        return {"search_metadata": meta, "booking_options": [
            {"together": {"book_with": "Airline website", "price": rng.randint(150, 500),
                          "booking_request": {"url": "https://www.google.com/travel/clk/f",
                                              "post_data": "u=demo"},
                          "option_title": "Main cabin"}},
            {"together": {"book_with": "Expedia", "price": rng.randint(150, 500),
                          "booking_request": {"url": "https://www.google.com/travel/clk/f",
                                              "post_data": "u=demo2"}}},
        ]}

    cabin = {"1": "Economy", "2": "Premium economy", "3": "Business", "4": "First"}.get(str(params.get("travel_class", 1)), "Economy")
    round_trip = str(params.get("type", "1")) == "1"
    if params.get("departure_token"):
        origin, dest, day = params["arrival_id"].split(",")[0], params["departure_id"].split(",")[0], params["return_date"]
        token_kind = "booking_token"
    else:
        origin, dest, day = params["departure_id"].split(",")[0], params["arrival_id"].split(",")[0], params["outbound_date"]
        token_kind = "departure_token" if round_trip else "booking_token"
    groups = [_group(rng, origin, dest, day, cabin, round_trip, token_kind, i) for i in range(rng.randint(8, 14))]
    groups.sort(key=lambda g: g["price"])
    low = groups[0]["price"]
    return {
        "search_metadata": meta,
        "best_flights": groups[:3],
        "other_flights": groups[3:],
        "price_insights": {"lowest_price": low, "price_level": rng.choice(["low", "typical", "high"]),
                           "typical_price_range": [int(low * 0.9), int(low * 1.4)]},
    }
