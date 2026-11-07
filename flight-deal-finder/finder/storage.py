"""Small SQLite database (a single file in data/flights.db) for cache, history and alerts."""
import json
import sqlite3
import time
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY, created REAL, response TEXT
);
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL, criteria TEXT,
    summary TEXT, cheapest REAL, results TEXT
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL, name TEXT, criteria TEXT,
    target REAL, active INTEGER DEFAULT 1, last_checked REAL, last_price REAL,
    last_error TEXT, triggered_at REAL
);
CREATE TABLE IF NOT EXISTS alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id INTEGER, created REAL,
    price REAL, message TEXT, seen INTEGER DEFAULT 0
);
"""


@contextmanager
def connect():
    """Open the database, save changes when done, and always close it."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        with conn:
            yield conn
    finally:
        conn.close()


# ---------- cache ----------
def cache_get(key, max_age_hours):
    with connect() as c:
        row = c.execute("SELECT created, response FROM cache WHERE key=?", (key,)).fetchone()
    if not row:
        return None
    age = time.time() - row["created"]
    if max_age_hours is not None and age > max_age_hours * 3600:
        return None
    return json.loads(row["response"]), age


def cache_put(key, data):
    with connect() as c:
        c.execute("INSERT OR REPLACE INTO cache (key, created, response) VALUES (?,?,?)",
                  (key, time.time(), json.dumps(data)))


def cache_clear():
    with connect() as c:
        c.execute("DELETE FROM cache")


# ---------- search history ----------
def save_search(criteria, summary, cheapest, results):
    with connect() as c:
        cur = c.execute(
            "INSERT INTO searches (created, criteria, summary, cheapest, results) VALUES (?,?,?,?,?)",
            (time.time(), json.dumps(criteria), summary, cheapest, json.dumps(results)))
        return cur.lastrowid


def update_search(search_id, criteria, summary, cheapest, results):
    with connect() as c:
        c.execute("UPDATE searches SET criteria=?, summary=?, cheapest=?, results=? WHERE id=?",
                  (json.dumps(criteria), summary, cheapest, json.dumps(results), search_id))


def get_search(search_id):
    with connect() as c:
        row = c.execute("SELECT * FROM searches WHERE id=?", (search_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["criteria"] = json.loads(d["criteria"])
    d["results"] = json.loads(d["results"]) if d["results"] else None
    return d


def list_searches(limit=50):
    with connect() as c:
        rows = c.execute("SELECT id, created, criteria, summary, cheapest FROM searches "
                         "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["criteria"] = json.loads(d["criteria"])
        out.append(d)
    return out


def delete_search(search_id):
    with connect() as c:
        c.execute("DELETE FROM searches WHERE id=?", (search_id,))


# ---------- alerts ----------
def add_alert(name, criteria, target):
    with connect() as c:
        cur = c.execute("INSERT INTO alerts (created, name, criteria, target) VALUES (?,?,?,?)",
                        (time.time(), name, json.dumps(criteria), target))
        return cur.lastrowid


def list_alerts(active_only=False):
    q = "SELECT * FROM alerts" + (" WHERE active=1" if active_only else "") + " ORDER BY id DESC"
    with connect() as c:
        rows = c.execute(q).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["criteria"] = json.loads(d["criteria"])
        out.append(d)
    return out


def update_alert(alert_id, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    with connect() as c:
        c.execute(f"UPDATE alerts SET {cols} WHERE id=?", (*fields.values(), alert_id))


def delete_alert(alert_id):
    with connect() as c:
        c.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
        c.execute("DELETE FROM alert_events WHERE alert_id=?", (alert_id,))


def add_event(alert_id, price, message):
    with connect() as c:
        c.execute("INSERT INTO alert_events (alert_id, created, price, message) VALUES (?,?,?,?)",
                  (alert_id, time.time(), price, message))


def list_events(limit=30):
    with connect() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM alert_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]


def unseen_events_count():
    with connect() as c:
        return c.execute("SELECT COUNT(*) FROM alert_events WHERE seen=0").fetchone()[0]


def mark_events_seen():
    with connect() as c:
        c.execute("UPDATE alert_events SET seen=1")
