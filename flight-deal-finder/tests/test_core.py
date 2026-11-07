import unittest
from datetime import date

from finder import airports, dates, pricing, ranking


def opt(airline="United", price=200, minutes=120, stops=0, dep="2026-03-06 08:00",
        arr="2026-03-06 10:00", ext=(), code="UA", **kw):
    o = {"airline": airline, "airline_code": code, "price": price, "total_minutes": minutes,
         "stops": stops, "dep_time": dep, "arr_time": arr, "extensions": list(ext),
         "legs": [], "layovers": []}
    o.update(kw)
    return o


class Airports(unittest.TestCase):
    def test_parse_and_city(self):
        self.assertEqual(airports.parse_airports("phx, tus"), "PHX,TUS")
        self.assertEqual(airports.parse_airports("Chicago"), "ORD,MDW")
        self.assertEqual(airports.parse_airports("chicago, DEN"), "ORD,MDW,DEN")

    def test_nearby(self):
        self.assertEqual(airports.with_nearby("PHX"), "PHX,AZA,TUS")
        self.assertTrue(airports.is_anywhere("Anywhere"))


class Dates(unittest.TestCase):
    today = date(2026, 1, 1)

    def test_exact_round_trip(self):
        p = dates.date_pairs("exact", "2026-03-05", "2026-03-08", today=self.today)
        self.assertEqual(p, [("2026-03-05", "2026-03-08")])

    def test_flex_keeps_trip_length(self):
        p = dates.date_pairs("flex", "2026-03-05", "2026-03-08", flex_days=3, today=self.today)
        self.assertEqual(len(p), 7)
        self.assertEqual(p[0], ("2026-03-02", "2026-03-05"))
        self.assertEqual(p[-1], ("2026-03-08", "2026-03-11"))

    def test_weekends_in_march(self):
        p = dates.date_pairs("weekends", month="2026-03", today=self.today)
        # Fridays in March 2026: 6, 13, 20, 27
        self.assertEqual([d for d, _ in p], ["2026-03-06", "2026-03-13", "2026-03-20", "2026-03-27"])
        self.assertEqual(p[0][1], "2026-03-08")

    def test_one_way_and_errors(self):
        p = dates.date_pairs("exact", "2026-03-05", round_trip=False, today=self.today)
        self.assertEqual(p, [("2026-03-05", None)])
        with self.assertRaises(ValueError):
            dates.date_pairs("exact", "2026-03-05", today=self.today)  # missing return
        with self.assertRaises(ValueError):
            dates.date_pairs("exact", "2025-03-05", round_trip=False, today=self.today)


class Pricing(unittest.TestCase):
    def test_united_card_first_bag_free(self):
        o = pricing.all_in(opt("United"), carry_on=1, checked=1, united_card=True)
        self.assertEqual(o["all_in"], 200)
        self.assertIn("United card: 1st bag free", o["flags"])
        o2 = pricing.all_in(opt("United"), carry_on=1, checked=1, united_card=False)
        self.assertEqual(o2["all_in"], 235)

    def test_second_bag_and_round_trip(self):
        o = pricing.all_in(opt("Delta", code="DL"), carry_on=1, checked=2, round_trip=True)
        self.assertEqual(o["bag_cost"], (35 + 45) * 2)

    def test_ulcc_carry_on(self):
        o = pricing.all_in(opt("Spirit", code="NK", price=79), carry_on=1, checked=0)
        self.assertEqual(o["all_in"], 79 + 55)
        self.assertIn("Carry-on costs extra", o["flags"])

    def test_basic_economy_no_carry_on_flagged(self):
        o = pricing.all_in(opt("United", ext=["Basic economy", "Carry-on bag not included"]),
                           carry_on=1, checked=0)
        self.assertTrue(o["basic_economy"])
        self.assertIn("Basic economy", o["flags"])
        self.assertIn("No carry-on allowed", o["flags"])
        self.assertEqual(o["all_in"], 200 + 35 + 25)

    def test_mixed_airlines_round_trip(self):
        out = opt("Southwest", code="WN")
        ret = pricing.all_in(opt("Frontier", code="F9", price=300), carry_on=1, checked=1, outbound=out)
        # Southwest out: carry-on free + bag $35;  Frontier back: carry-on $60 + bag $55
        self.assertEqual(ret["bag_cost"], 35 + 60 + 55)
        self.assertEqual(ret["all_in"], 300 + 150)

    def test_no_bags_no_fees(self):
        o = pricing.all_in(opt("Frontier", code="F9", price=50), carry_on=0, checked=0)
        self.assertEqual(o["all_in"], 50)


class Ranking(unittest.TestCase):
    def test_cheap_vs_fast(self):
        cheap = pricing.all_in(opt("Spirit", price=90, minutes=400, stops=1, code="NK"), carry_on=0)
        fast = pricing.all_in(opt("Delta", price=180, minutes=120, stops=0, code="DL"), carry_on=0)
        ranked = ranking.score_all([cheap, fast], weights={"price": 100, "time": 0, "stops": 0, "fit": 0})
        self.assertIs(ranked[0], cheap)
        ranked = ranking.score_all([cheap, fast], weights={"price": 20, "time": 50, "stops": 30, "fit": 0})
        self.assertIs(ranked[0], fast)

    def test_time_window_fit(self):
        w = {"dep_start": 7, "dep_end": 11, "arr_start": None, "arr_end": None}
        self.assertEqual(ranking.time_fit(opt(dep="2026-03-06 09:00"), w), 1.0)
        self.assertEqual(ranking.time_fit(opt(dep="2026-03-06 13:00"), w), 0.5)
        self.assertEqual(ranking.time_fit(opt(dep="2026-03-06 23:00"), {"dep_start": 22, "dep_end": 6}), 1.0)

    def test_picks_and_preferred(self):
        a = pricing.all_in(opt("Spirit", price=90, minutes=400, code="NK"), carry_on=0)
        b = pricing.all_in(opt("Delta", price=110, minutes=150, code="DL"), carry_on=0)
        c = pricing.all_in(opt("American", price=300, minutes=100, code="AA"), carry_on=0)
        ranked = ranking.score_all([a, b, c], preferred=["DL"])
        self.assertTrue(b["is_preferred"])
        p = ranking.picks(ranked, fastest_under=200)
        self.assertIs(p["cheapest"], a)
        self.assertIs(p["fastest"], b)
        self.assertIs(ranking.picks(ranked, fastest_under=400)["fastest"], c)


if __name__ == "__main__":
    unittest.main()
