import json, os, time, base64, requests, builtins
_p = builtins.print
B = "/mnt/files/f4f_trials"
REPO = "/repos/trevorwerner12/IG-Assets"
BR = "claude/file-access-question-oa157h"
ST = B + "/posted.json"
os.makedirs(B, exist_ok=True)
def _gh_file(path):
    r, err = proxy_execute("GET", f"{REPO}/contents/{path}", "github", query_params={"ref": BR})
    if err: raise RuntimeError(err)
    b, err = proxy_execute("GET", f"{REPO}/git/blobs/{r['sha']}", "github")
    if err: raise RuntimeError(err)
    return base64.b64decode(b["content"])
def _plan():
    return json.loads(_gh_file("trial-reels/plan.json"))
def _st():
    if os.path.exists(ST): return json.load(open(ST))
    return {}
def _save(s):
    json.dump(s, open(ST, "w"), indent=1)
def _already_live(cap):
    # guard against double posting if local state was wiped: match caption among recent media
    r, err = proxy_execute("GET", "/me/media", "instagram", query_params={"fields": "id,caption,permalink,is_shared_to_feed,timestamp", "limit": 40})
    for m in (r or {}).get("data", []):
        if (m.get("caption") or "").strip() == cap.strip():
            return m
    return None
def publish(video, day, max_wait=120):
    key = f"{video}_d{day}"
    s = _st(); e = s.get(key, {})
    if e.get("media_id"):
        return f"{key} already posted {e.get('permalink')}"
    t0 = time.time()
    if not e.get("cid"):
        cap = _plan()["caps"][video][day - 1]
        m = _already_live(cap)
        if m:
            s[key] = {"media_id": m["id"], "permalink": m.get("permalink"), "is_shared_to_feed": m.get("is_shared_to_feed")}; _save(s)
            return f"{key} already posted {m.get('permalink')}"
        data = _gh_file(f"trial-reels/{key}.mp4")
        os.makedirs("/home/user/pub", exist_ok=True)
        lp = f"/home/user/pub/{key}.mp4"
        open(lp, "wb").write(data)
        up, err = upload_local_file(lp)
        if err: return f"{key} upload err {err}"
        u = (up.get("data") or up).get("s3_url")
        u = requests.get(u, allow_redirects=True, stream=True, timeout=60).url
        res, err = proxy_execute("POST", "/me/media", "instagram", body={"media_type": "REELS", "video_url": u, "caption": cap,
                                 "trial_params": {"graduation_strategy": "MANUAL"}})
        if err or not (res or {}).get("id"): return f"{key} container err {err} {res}"
        e = {"cid": res["id"], "size": len(data)}; s[key] = e; _save(s)
    cid = e["cid"]
    while time.time() - t0 < max_wait:
        res, err = proxy_execute("GET", f"/{cid}", "instagram", query_params={"fields": "status_code,status"})
        sc = (res or {}).get("status_code")
        if sc == "FINISHED": break
        if sc == "ERROR":
            s[key] = {}; _save(s); return f"{key} IG processing ERROR {res}"
        time.sleep(6)
    else:
        return f"{key} still processing (cid {cid}); call publish again"
    res, err = proxy_execute("POST", "/me/media_publish", "instagram", body={"creation_id": cid})
    if err or not (res or {}).get("id"): return f"{key} publish err {err} {res}"
    mid = res["id"]
    r2, _ = proxy_execute("GET", f"/{mid}", "instagram", query_params={"fields": "permalink,is_shared_to_feed,timestamp"})
    e.update({"media_id": mid, "permalink": (r2 or {}).get("permalink"), "is_shared_to_feed": (r2 or {}).get("is_shared_to_feed"),
              "timestamp": (r2 or {}).get("timestamp")})
    s[key] = e; _save(s)
    return f"{key} POSTED {e['permalink']} shared_to_feed={e['is_shared_to_feed']}"
