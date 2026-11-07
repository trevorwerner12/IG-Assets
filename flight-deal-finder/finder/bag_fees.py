"""Estimated bag fees per airline, in US dollars, ONE direction, economy.

These are typical prepaid-online prices and they change often. If you know a
fee is different, just edit the number here and restart the app.

  carry_on : fee for a full-size carry-on (0 = included with a regular fare)
  bag1     : first checked bag
  bag2     : second checked bag (and each one after it)
"""

BAG_FEES = {
    # Full-service airlines (carry-on included except some basic economy fares)
    "United":       {"carry_on": 0,  "bag1": 35, "bag2": 45},
    "American":     {"carry_on": 0,  "bag1": 35, "bag2": 45},
    "Delta":        {"carry_on": 0,  "bag1": 35, "bag2": 45},
    "Alaska":       {"carry_on": 0,  "bag1": 35, "bag2": 45},
    "Southwest":    {"carry_on": 0,  "bag1": 35, "bag2": 45},
    "JetBlue":      {"carry_on": 0,  "bag1": 40, "bag2": 50},
    "Hawaiian":     {"carry_on": 0,  "bag1": 35, "bag2": 45},
    # Ultra-low-cost airlines (carry-on usually costs extra on the base fare)
    "Frontier":     {"carry_on": 60, "bag1": 55, "bag2": 65},
    "Spirit":       {"carry_on": 55, "bag1": 50, "bag2": 60},
    "Allegiant":    {"carry_on": 35, "bag1": 40, "bag2": 50},
    "Sun Country":  {"carry_on": 40, "bag1": 40, "bag2": 50},
    "Breeze":       {"carry_on": 35, "bag1": 40, "bag2": 50},
    "Avelo":        {"carry_on": 45, "bag1": 50, "bag2": 60},
}

# Used for any airline not listed above (e.g. foreign airlines)
DEFAULT_FEES = {"carry_on": 0, "bag1": 35, "bag2": 45}

# Extra charge if you bring a carry-on on a "no carry-on" basic economy fare
# (e.g. United Basic Economy): you pay the checked-bag fee at the gate plus this.
GATE_HANDLING_FEE = 25


def fees_for(airline_name):
    name = (airline_name or "").lower()
    for key, fees in BAG_FEES.items():
        if key.lower() in name:
            return key, fees
    return None, DEFAULT_FEES
