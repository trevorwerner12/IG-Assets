"""Airport helpers: nearby airports and city -> airport groups."""

NEARBY = {
    "PHX": ["AZA", "TUS"],
}

# Type a city name in the destination box and it expands to these airports.
CITY_AIRPORTS = {
    "new york": "JFK,LGA,EWR",
    "nyc": "JFK,LGA,EWR",
    "los angeles": "LAX,BUR,LGB,SNA,ONT",
    "la": "LAX,BUR,LGB,SNA,ONT",
    "san francisco": "SFO,OAK,SJC",
    "bay area": "SFO,OAK,SJC",
    "chicago": "ORD,MDW",
    "washington": "DCA,IAD,BWI",
    "dc": "DCA,IAD,BWI",
    "houston": "IAH,HOU",
    "dallas": "DFW,DAL",
    "miami": "MIA,FLL",
    "south florida": "MIA,FLL,PBI",
    "orlando": "MCO,SFB",
    "boston": "BOS",
    "seattle": "SEA",
    "denver": "DEN",
    "las vegas": "LAS",
    "san diego": "SAN",
    "portland": "PDX",
    "atlanta": "ATL",
    "nashville": "BNA",
    "austin": "AUS",
    "honolulu": "HNL",
    "hawaii": "HNL,OGG,KOA,LIH",
    "london": "LHR,LGW,STN,LTN",
    "paris": "CDG,ORY",
    "tokyo": "HND,NRT",
    "cancun": "CUN",
    "mexico city": "MEX",
}

ANYWHERE_WORDS = {"anywhere", "any", "everywhere", "*"}


def parse_airports(text):
    """'phx, tus' -> 'PHX,TUS'. City names expand to their airports."""
    text = (text or "").strip()
    if not text:
        return ""
    if text.lower() in CITY_AIRPORTS:
        return CITY_AIRPORTS[text.lower()]
    codes = []
    for part in text.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if part.lower() in CITY_AIRPORTS:
            codes.extend(CITY_AIRPORTS[part.lower()].split(","))
        else:
            codes.append(part.upper())
    seen = []
    for c in codes:
        if c not in seen:
            seen.append(c)
    return ",".join(seen)


def with_nearby(origin_codes):
    codes = origin_codes.split(",") if origin_codes else []
    for c in list(codes):
        for n in NEARBY.get(c, []):
            if n not in codes:
                codes.append(n)
    return ",".join(codes)


def is_anywhere(text):
    return (text or "").strip().lower() in ANYWHERE_WORDS
