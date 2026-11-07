import os
import re
from unittest import mock

from finder import alerts, search, storage
from finder.web import app
from tests.test_search import TempDB, form


class WebPages(TempDB):
    def setUp(self):
        super().setUp()
        self.env = mock.patch.dict(os.environ, {"SERPAPI_KEY": ""})
        self.env.start()
        self.client = app.test_client()

    def tearDown(self):
        self.env.stop()
        super().tearDown()

    def search(self, **kw):
        r = self.client.post("/search", data=form(**kw))
        self.assertEqual(r.status_code, 302, r.data[:500])
        return r.headers["Location"]

    def test_full_flow(self):
        self.assertIn(b"DEMO MODE", self.client.get("/").data)
        loc = self.search(checked="1")
        page = self.client.get(loc).data.decode()
        self.assertIn("Best value", page)
        self.assertIn("Cheapest overall", page)
        opt = re.search(r"/returns/([0-9a-f]+)", page).group(1)
        rpage = self.client.get(f"{loc}/returns/{opt}").data.decode()
        ret = re.search(r"/book/(r[0-9a-f]+)\?out=([0-9a-f]+)", rpage)
        bpage = self.client.get(f"{loc}/book/{ret.group(1)}?out={ret.group(2)}").data.decode()
        self.assertIn("Where to book", bpage)
        self.assertIn('class="booking"', bpage)

        # re-rank keeps the same search id
        r = self.client.post(f"{loc}/rerank", data={"w_price": "0", "w_time": "100", "w_stops": "0",
                                                    "w_fit": "0", "carry_on": "1", "checked": "2"})
        self.assertEqual(r.headers["Location"], loc)
        sid = int(loc.rsplit("/", 1)[1])
        s = storage.get_search(sid)
        self.assertEqual(s["criteria"]["checked"], 2)
        mins = [o["total_minutes"] for o in s["results"]["options"]]
        self.assertEqual(mins[0], min(mins))  # time-only weights -> fastest first

        # alert
        r = self.client.post(f"/alerts/new/{sid}", data={"target": "99999"})
        self.assertEqual(r.status_code, 302)
        a = storage.list_alerts()[0]
        msg = alerts.check_one(a)
        self.assertIn("Price drop", msg)
        self.assertIn(b"Price drops", self.client.get("/alerts").data)
        self.assertEqual(storage.unseen_events_count(), 0)
        self.assertIn(b"Past searches", self.client.get("/history").data)

    def test_error_shown(self):
        r = self.client.post("/search", data=form(only_airlines="UA", exclude_airlines="NK"))
        self.assertIn(b"not both", r.data)

    def test_one_way_book_and_anywhere(self):
        loc = self.search(trip="oneway")
        page = self.client.get(loc).data.decode()
        opt = re.search(r"/book/([0-9a-f]+)", page).group(1)
        self.assertEqual(self.client.get(f"{loc}/book/{opt}").status_code, 200)
        loc = self.search(destination="anywhere")
        self.assertIn(b"Cheapest places to go", self.client.get(loc).data)

    def test_expired_alert_pauses(self):
        c = search.criteria_from_form(form(depart="2020-01-01", **{"return": "2020-01-05"}))
        aid = storage.add_alert("old trip", c, 100)
        alerts.check_one(storage.list_alerts()[0])
        a = storage.list_alerts()[0]
        self.assertEqual(a["id"], aid)
        self.assertEqual(a["active"], 0)


class KeySetup(TempDB):
    def test_save_key_writes_env(self):
        import tempfile
        from pathlib import Path
        from finder import config
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(config, "APP_DIR", Path(d)), \
                mock.patch.dict(os.environ, {"SERPAPI_KEY": ""}), \
                mock.patch("finder.web.account_info", return_value={"left": 250}):
            (Path(d) / ".env.example").write_text("# comment\nSERPAPI_KEY=\nPORT=5055\n")
            c = app.test_client()
            r = c.post("/setup/key", data={"key": "short"})
            self.assertFalse((Path(d) / ".env").exists())
            r = c.post("/setup/key", data={"key": "a" * 64})
            text = (Path(d) / ".env").read_text()
            self.assertIn("SERPAPI_KEY=" + "a" * 64, text)
            self.assertIn("PORT=5055", text)
            self.assertFalse(config.demo_mode())
