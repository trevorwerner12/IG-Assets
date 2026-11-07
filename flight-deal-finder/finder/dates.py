"""Turns the date choices on the form into a list of (depart, return) pairs."""
from datetime import date, timedelta

WEEKEND_PATTERNS = {
    # name: (departure weekday, nights)   Monday=0 ... Sunday=6
    "fri-sun": (4, 2),
    "thu-sun": (3, 3),
    "fri-mon": (4, 3),
    "sat-sun": (5, 1),
}


def _parse(d):
    return d if isinstance(d, date) else date.fromisoformat(d)


def date_pairs(mode, depart=None, ret=None, flex_days=0, month=None,
               weekend_pattern="fri-sun", round_trip=True, today=None):
    """Return a list of (depart_date, return_date_or_None) as ISO strings.

    mode: 'exact' | 'flex' | 'weekends'
    """
    today = today or date.today()
    pairs = []
    if mode in ("exact", "flex"):
        if not depart:
            raise ValueError("Please pick a departure date.")
        d0 = _parse(depart)
        r0 = _parse(ret) if (round_trip and ret) else None
        if round_trip and r0 is None:
            raise ValueError("Please pick a return date (or choose one-way).")
        if r0 and r0 < d0:
            raise ValueError("Return date is before the departure date.")
        n = int(flex_days or 0) if mode == "flex" else 0
        for shift in range(-n, n + 1):
            d = d0 + timedelta(days=shift)
            r = (r0 + timedelta(days=shift)) if r0 else None
            pairs.append((d, r))
    elif mode == "weekends":
        if not month:
            raise ValueError("Please pick a month for weekend search.")
        year, mon = (int(x) for x in month.split("-"))
        weekday, nights = WEEKEND_PATTERNS.get(weekend_pattern, WEEKEND_PATTERNS["fri-sun"])
        d = date(year, mon, 1)
        while d.month == mon:
            if d.weekday() == weekday:
                pairs.append((d, d + timedelta(days=nights) if round_trip else None))
            d += timedelta(days=1)
    else:
        raise ValueError(f"Unknown date mode: {mode}")

    pairs = [(d, r) for d, r in pairs if d >= today]
    if not pairs:
        raise ValueError("All of those dates are in the past.")
    return [(d.isoformat(), r.isoformat() if r else None) for d, r in pairs]
