import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from finder import config, demo, search, serpapi_client, storage


class TempDB(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [
            mock.patch.object(config, "DATA_DIR", Path(self.tmp.name)),
            mock.patch.object(config, "DB_PATH", Path(self.tmp.name) / "t.db"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()


def form(**kw):
    f = {"origin": "PHX", "destination": "DEN", "trip": "round", "date_mode": "exact",
         "depart": "2030-03-05", "return": "2030-03-08", "carry_on": "1", "checked": "1"}
    f.update(kw)
    return f


class FakeResp:
    def __init__(self, status, data):
        self.status_code, self._data = status, data

    def json(self):
        return self._data


class LiveClient(TempDB):
    """Simulates the real SerpApi (a key is set) with a fake HTTP layer."""

    def setUp(self):
        super().setUp()
        self.env = mock.patch.dict(os.environ, {"SERPAPI_KEY": "test-key", "DEMO_MODE": ""})
        self.env.start()
        self.calls = []

    def tearDown(self):
        self.env.stop()
        super().tearDown()

    def fake_get(self, url, params, timeout):
        self.calls.append(params)
        assert params["api_key"] == "test-key"
        return FakeResp(200, demo.fake_response({k: v for k, v in params.items() if k != "api_key"}))

    def test_cache_saves_credits(self):
        c = search.criteria_from_form(form())
        with mock.patch("requests.get", self.fake_get):
            r1 = search.run(c)
            r2 = search.run(c)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(r1["credits_used"], 1)
        self.assertEqual(r2["credits_used"], 0)
        self.assertEqual(r2["cached_dates"], 1)
        self.assertEqual(search.plan(c)[2], 0)  # nothing left to spend

    def test_api_key_never_in_cache_key(self):
        p = {"engine": "google_flights", "x": 1}
        self.assertEqual(serpapi_client.cache_key(p), serpapi_client.cache_key({**p, "api_key": "zzz"}))

    def test_limit_error_is_clear(self):
        bad = lambda *a, **k: FakeResp(429, {"error": "Your account has run out of searches."})
        with mock.patch("requests.get", bad):
            with self.assertRaises(serpapi_client.ApiError) as cm:
                search.run(search.criteria_from_form(form()))
        self.assertEqual(cm.exception.kind, "limit")
        self.assertIn("search limit", str(cm.exception))

    def test_bad_key_error(self):
        bad = lambda *a, **k: FakeResp(401, {"error": "Invalid API key. Your API key should be here"})
        with mock.patch("requests.get", bad):
            with self.assertRaises(serpapi_client.ApiError) as cm:
                serpapi_client.fetch({"engine": "google_flights"})
        self.assertEqual(cm.exception.kind, "key")

    def test_no_results_is_not_an_error(self):
        none = lambda *a, **k: FakeResp(200, {"error": "Google Flights hasn't returned any results for this query."})
        with mock.patch("requests.get", none):
            r = search.run(search.criteria_from_form(form()))
        self.assertEqual(r["options"], [])

    def test_flex_needs_confirmation(self):
        c = search.criteria_from_form(form(date_mode="flex", flex_days="3"))
        with mock.patch("requests.get", self.fake_get):
            r = search.run(c)
            self.assertTrue(r["needs_confirm"])
            self.assertEqual(r["credits"], 7)
            self.assertEqual(self.calls, [])
            r = search.run(c, confirmed=True)
        self.assertEqual(len(r["calendar"]), 7)
        self.assertEqual(sum(1 for x in r["calendar"] if x["cheapest"]) >= 1, True)


class DemoSearch(TempDB):
    def setUp(self):
        super().setUp()
        self.env = mock.patch.dict(os.environ, {"SERPAPI_KEY": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        super().tearDown()

    def test_params(self):
        c = search.criteria_from_form(form(include_nearby="on", max_stops="1", only_airlines="ua, aa",
                                           max_layover_hours="3", dep_start="6", dep_end="12",
                                           strict_times="on", cabin="business"))
        p = search.base_params(c, "2030-03-05", "2030-03-08")
        self.assertEqual(p["departure_id"], "PHX,AZA,TUS")
        self.assertEqual(p["stops"], 2)
        self.assertEqual(p["include_airlines"], "UA,AA")
        self.assertEqual(p["layover_duration"], "30,180")
        self.assertEqual(p["outbound_times"], "6,12")
        self.assertEqual(p["travel_class"], 3)
        self.assertEqual(p["type"], 1)

    def test_full_round_trip_flow(self):
        c = search.criteria_from_form(form(max_stops="1"))
        r = search.run(c)
        self.assertTrue(r["options"])
        for o in r["options"]:
            self.assertLessEqual(o["stops"], 1)
            self.assertGreaterEqual(o["all_in"], o["price"])
            self.assertTrue(o["departure_token"])
        scores = [o["score"] for o in r["options"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(r["picks"]["cheapest"])
        rets, _ = search.returns_for(c, r["options"][0])
        self.assertTrue(rets and rets[0]["booking_token"])
        links, _, _ = search.booking_options(c, rets[0])
        self.assertTrue(links[0]["url"])

    def test_one_way_and_weekends(self):
        c = search.criteria_from_form(form(trip="oneway", date_mode="weekends", month="2030-03"))
        r = search.run(c, confirmed=True)
        self.assertEqual(len(r["calendar"]), 5)  # Fridays in March 2030: 1,8,15,22,29
        self.assertTrue(all(o["booking_token"] for o in r["options"]))

    def test_anywhere(self):
        r = search.run(search.criteria_from_form(form(destination="anywhere")))
        self.assertEqual(r["kind"], "explore")
        prices = [d["price"] for d in r["destinations"]]
        self.assertEqual(prices, sorted(prices))

    def test_validation(self):
        with self.assertRaises(ValueError):
            search.run(search.criteria_from_form(form(only_airlines="UA", exclude_airlines="NK")))
        with self.assertRaises(ValueError):
            search.run(search.criteria_from_form(form(destination="")))

    def test_history_storage(self):
        c = search.criteria_from_form(form())
        sid = storage.save_search(c, search.describe(c), 199, {"options": []})
        self.assertEqual(storage.get_search(sid)["criteria"]["destination"], "DEN")
        self.assertEqual(len(storage.list_searches()), 1)


if __name__ == "__main__":
    unittest.main()
