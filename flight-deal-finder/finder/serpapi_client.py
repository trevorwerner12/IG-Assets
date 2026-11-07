"""Talks to SerpApi. Every response is cached so repeat searches are free."""
import hashlib
import json
import time

import requests

from . import config, demo, storage

SEARCH_URL = "https://serpapi.com/search.json"
ACCOUNT_URL = "https://serpapi.com/account.json"

NO_RESULTS_HINTS = ("hasn't returned any results", "no results")


class ApiError(Exception):
    """kind: 'limit' | 'key' | 'network' | 'other'"""

    def __init__(self, message, kind="other"):
        super().__init__(message)
        self.kind = kind


def cache_key(params):
    clean = {k: v for k, v in sorted(params.items()) if k != "api_key" and v not in (None, "")}
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()


def is_cached(params, max_age_hours=None):
    if config.demo_mode():
        return True  # demo searches are free
    hours = config.CACHE_HOURS if max_age_hours is None else max_age_hours
    return storage.cache_get(cache_key(params), hours) is not None


def _friendly(message, status):
    m = (message or "").lower()
    if status == 429 or "run out of searches" in m or "rate limit" in m or "hourly" in m \
            or "exceeded" in m or "plan" in m and "searches" in m:
        return ApiError(
            "You've hit your SerpApi search limit. " + (message or "") +
            " Your saved/cached results still work. Wait for the limit to reset "
            "(free plan: 250/month and 50/hour) or upgrade at serpapi.com/pricing.", "limit")
    if status in (401, 403) or "invalid api key" in m or "api key" in m:
        return ApiError("SerpApi says your API key isn't valid. Check SERPAPI_KEY in the .env file "
                        "(copy it again from serpapi.com/manage-api-key) and restart the app.", "key")
    return ApiError(f"SerpApi error: {message or 'HTTP ' + str(status)}", "other")


def fetch(params, use_cache=True, max_age_hours=None):
    """Returns (data, info) where info = {'cached': bool, 'age_min': int}."""
    if config.demo_mode():
        return demo.fake_response(params), {"cached": False, "age_min": 0, "demo": True}

    key = cache_key(params)
    hours = config.CACHE_HOURS if max_age_hours is None else max_age_hours
    if use_cache:
        hit = storage.cache_get(key, hours)
        if hit:
            data, age = hit
            return data, {"cached": True, "age_min": int(age // 60)}

    try:
        resp = requests.get(SEARCH_URL, params={**params, "api_key": config.api_key()}, timeout=60)
    except requests.RequestException as e:
        raise ApiError(f"Couldn't reach SerpApi (check your internet connection): {e}", "network")
    try:
        data = resp.json()
    except ValueError:
        data = {}
    err = data.get("error")
    if err and any(h in err.lower() for h in NO_RESULTS_HINTS):
        data = {"search_metadata": data.get("search_metadata", {}), "no_results": True}
        storage.cache_put(key, data)
        return data, {"cached": False, "age_min": 0}
    if resp.status_code != 200 or err:
        raise _friendly(err, resp.status_code)
    storage.cache_put(key, data)
    return data, {"cached": False, "age_min": 0}


_account_cache = {"t": 0, "data": None}


def account_info():
    """Searches left this month (this call is free). Returns dict or None."""
    if config.demo_mode():
        return None
    if time.time() - _account_cache["t"] < 300 and _account_cache["data"]:
        return _account_cache["data"]
    try:
        r = requests.get(ACCOUNT_URL, params={"api_key": config.api_key()}, timeout=15)
        data = r.json()
    except (requests.RequestException, ValueError):
        return None
    if data.get("error"):
        return {"error": data["error"]}
    info = {
        "left": data.get("total_searches_left", data.get("plan_searches_left")),
        "per_month": data.get("searches_per_month"),
        "used": data.get("this_month_usage"),
        "hour_limit": data.get("account_rate_limit_per_hour"),
        "plan": data.get("plan_name"),
    }
    _account_cache.update(t=time.time(), data=info)
    return info


def forget_account_cache():
    _account_cache.update(t=0, data=None)
