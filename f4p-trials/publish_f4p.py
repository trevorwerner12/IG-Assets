# Fuel 4 Performance trial-reel publisher. Runs in the Composio REMOTE WORKBENCH (preloaded helpers:
# proxy_execute, upload_local_file). Bootstrap in a cell:
#   r,_ = proxy_execute("GET", "/repos/trevorwerner12/IG-Assets/contents/f4p-trials/publish_f4p.py", "github",
#                       query_params={"ref": "claude/file-access-question-oa157h"})
#   import base64; exec(base64.b64decode(r["content"]).decode())
#   slots_for("2026-11-14")          -> [(ep, v), ...] for that Arizona date
#   publish_slot(ep, v, max_wait=20) -> re-call until it returns POSTED / already posted
import json, os, re, time, base64, datetime, requests, builtins, contextlib, io
_p = builtins.print
REPO = "/repos/trevorwerner12/IG-Assets"
BR = "claude/file-access-question-oa157h"


def _px(*a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return proxy_execute(*a, **k)


def _gh(path):
    r, err = _px("GET", f"{REPO}/contents/{path}", "github", query_params={"ref": BR})
    if err: raise RuntimeError(err)
    b, err = _px("GET", f"{REPO}/git/blobs/{r['sha']}", "github")
    if err: raise RuntimeError(err)
    return base64.b64decode(b["content"])


PLAN = json.loads(_gh("f4p-trials/plan.json"))
ORIG = json.loads(_gh("f4p-trials/transcripts.json"))["caps"]

OPENERS = {
    "1": "{hook} 🎙️",
    "2": "Ever wonder what pro athletes actually eat? 👀",
    "3": "Pro athlete fuel, explained in under a minute ⚾️",
    "4": "Would you eat this before a game? ⬇️",
    "5": "Fuel 4 Performance: {name} 🎙️",
    "6": "Rate this athlete's fuel 1-10 ⬇️",
}


def caption(ep, v):
    E = PLAN["eps"][ep]
    body = ORIG[ep].split("\n", 1)[1].strip()                     # drop the "Ep. N Name" title line
    body = re.sub(r"\n*Follow so you don.t miss.*$", "", body, flags=re.S).strip()
    hook = " ".join(E["hook"]).capitalize().replace("sec ", "SEC ")
    first = OPENERS[v].format(hook=hook, name=E["name"])
    return f"{first}\n\n{body}\n\nFollow @fueled_4_fitness for more pro athlete fuel 🎙️⚾️"


def slots_for(az_date):
    d = (datetime.date.fromisoformat(az_date) - datetime.date.fromisoformat(PLAN["start_date"])).days
    n, order = PLAN["per_day"], PLAN["order"]
    out = []
    for k in range(n):
        i = d * n + k
        if 0 <= i < 6 * len(order):
            out.append((order[i % len(order)], str(i // len(order) + 1)))
    return out


def _already_live(cap):
    r, _ = _px("GET", "/me/media", "instagram", query_params={"fields": "id,caption,permalink,is_shared_to_feed", "limit": 50})
    for m in (r or {}).get("data", []):
        if (m.get("caption") or "").strip() == cap.strip():
            return m


STATE = {}


def publish_slot(ep, v, max_wait=20):
    key = f"ep{ep}_v{v}"; e = STATE.get(key, {}); t0 = time.time()
    if e.get("media_id"): return f"{key} already posted {e.get('permalink')}"
    cap = caption(ep, v)
    if not e.get("cid"):
        m = _already_live(cap)
        if m:
            STATE[key] = {"media_id": m["id"], "permalink": m.get("permalink")}
            return f"{key} already posted {m.get('permalink')}"
        data = _gh(f"f4p-trials/out/{key}.mp4")
        os.makedirs("/home/user/pub", exist_ok=True); lp = f"/home/user/pub/{key}.mp4"
        open(lp, "wb").write(data)
        with contextlib.redirect_stdout(io.StringIO()):
            up, err = upload_local_file(lp)
        if err: return f"{key} upload err {err}"
        u = requests.get((up.get("data") or up)["s3_url"], allow_redirects=True, stream=True, timeout=60).url
        res, err = _px("POST", "/me/media", "instagram", body={"media_type": "REELS", "video_url": u, "caption": cap,
                       "trial_params": {"graduation_strategy": "MANUAL"}})
        if err or not (res or {}).get("id"): return f"{key} container err {err} {res}"
        e = STATE[key] = {"cid": res["id"]}
    while time.time() - t0 < max_wait:
        res, _ = _px("GET", f"/{e['cid']}", "instagram", query_params={"fields": "status_code"})
        sc = (res or {}).get("status_code")
        if sc == "FINISHED": break
        if sc == "ERROR": STATE[key] = {}; return f"{key} IG processing ERROR {res}"
        time.sleep(5)
    else:
        return f"{key} still processing; call publish_slot again"
    res, err = _px("POST", "/me/media_publish", "instagram", body={"creation_id": e["cid"]})
    if err or not (res or {}).get("id"): return f"{key} publish err {err} {res}"
    r2, _ = _px("GET", f"/{res['id']}", "instagram", query_params={"fields": "permalink,is_shared_to_feed"})
    e.update({"media_id": res["id"], **(r2 or {})})
    return f"{key} POSTED {e.get('permalink')} shared_to_feed={e.get('is_shared_to_feed')}"
