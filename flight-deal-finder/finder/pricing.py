"""All-in price = ticket price + estimated bag fees for your bags."""
from . import bag_fees

NO_CARRY_ON_HINTS = (
    "carry-on bag not included",
    "carry-on not included",
    "no carry-on",
    "carry-on bag for a fee",
    "carry-on for a fee",
    "personal item only",
)


def _all_text(opt):
    parts = list(opt.get("extensions") or [])
    for leg in opt.get("legs") or []:
        parts.extend(leg.get("extensions") or [])
        parts.append(leg.get("travel_class") or "")
    return " | ".join(p for p in parts if p).lower()


def analyze_fare(opt):
    text = _all_text(opt)
    basic = "basic economy" in text
    no_carry = any(h in text for h in NO_CARRY_ON_HINTS)
    return basic, no_carry


def all_in(opt, carry_on=1, checked=0, round_trip=False, united_card=True, outbound=None):
    """Adds 'all_in', 'bag_cost', 'bag_note' and 'flags' to the option dict.

    outbound: for a chosen return flight, the outbound flight — each direction is
    then charged its own airline's bag fees.
    """
    if outbound is not None:
        out = all_in(dict(outbound), carry_on, checked, False, united_card)
        all_in(opt, carry_on, checked, False, united_card)
        opt["bag_cost"] += out["bag_cost"]
        opt["all_in"] = opt["price"] + opt["bag_cost"] if opt.get("price") is not None else None
        opt["bag_note"] = f"outbound ({out['airline']}): {out['bag_note']}; return ({opt['airline']}): {opt['bag_note']}"
        for f in out["flags"]:
            if f not in opt["flags"]:
                opt["flags"].append(f)
        return opt
    key, fees = bag_fees.fees_for(opt.get("airline"))
    basic, no_carry = analyze_fare(opt)
    directions = 2 if round_trip else 1
    notes, flags = [], []

    per_dir = 0
    if carry_on:
        if fees["carry_on"]:
            per_dir += fees["carry_on"] * carry_on
            notes.append(f"carry-on ${fees['carry_on']}")
            flags.append("Carry-on costs extra")
        elif no_carry:
            gate = fees["bag1"] + bag_fees.GATE_HANDLING_FEE
            per_dir += gate * carry_on
            notes.append(f"carry-on must be gate-checked ~${gate}")
            flags.append("No carry-on allowed")
    for i in range(int(checked or 0)):
        fee = fees["bag1"] if i == 0 else fees["bag2"]
        if i == 0 and united_card and key == "United":
            notes.append("1st bag free (United card)")
            flags.append("United card: 1st bag free")
            continue
        per_dir += fee
        notes.append(f"bag {i + 1} ${fee}")

    if basic:
        flags.insert(0, "Basic economy")
    if key is None and (carry_on or checked):
        flags.append("Bag fees guessed (unknown airline)")
    if any(l.get("overnight") for l in opt.get("layovers") or []):
        flags.append("Overnight layover")
    if any(leg.get("often_delayed") for leg in opt.get("legs") or []):
        flags.append("Often delayed 30+ min")

    bag_cost = per_dir * directions
    price = opt.get("price")
    opt["bag_cost"] = bag_cost
    opt["bag_note"] = (", ".join(notes) + (" — each way" if round_trip and notes else "")) or "no bag fees"
    opt["all_in"] = (price + bag_cost) if price is not None else None
    opt["basic_economy"] = basic
    opt["flags"] = flags
    return opt
