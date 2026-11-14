# Paste into the Composio REMOTE WORKBENCH (session "part"). Converts the raw 4K DJI originals of
# Ep. 1-4 (Drive, "<name> interview OG.mp4") into 1440x1080 30fps proxy pieces and PUTs them, in 3 MB
# chunks, to branch dji-transfer under f4p/ep{N}/q{JJ}.partKK. One piece per cell: the MCP call dies at
# 60 s and the sandbox VM pauses between calls, so background threads do not work.
import subprocess, requests, os, re, time, builtins, contextlib, io, base64, math
_p = builtins.print
subprocess.run("pip install -q imageio-ffmpeg >/dev/null 2>&1", shell=True)
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs("/home/user/f4p", exist_ok=True)
IDS = {"1": "1lZk0Iekrm1aIq4TUqsIlr7Im8Gx9r1kT", "2": "1w5sm1p4chotpGrvr02uVGpdQBqQspGCs",
       "3": "1tIaZ8Y4vNgNe7h1mqKoikSgoz6KO1W0n", "4": "1-3gjfLSeqM8mRC-pxwfctXGJ4av-x_s0"}
DUR = {"1": 58.94, "2": 55.36, "3": 46.48, "4": 30.72}
REPO = "/repos/trevorwerner12/IG-Assets"


def px(*a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return proxy_execute(*a, **k)


def ensure_og(ep):
    p = f"/home/user/f4p/og{ep}.mp4"
    if not os.path.exists(p) or os.path.getsize(p) < 1e8:
        u = f"https://drive.usercontent.google.com/download?id={IDS[ep]}&export=download&confirm=t"
        with requests.get(u, stream=True, timeout=120) as r, open(p, "wb") as f:
            for c in r.iter_content(8 << 20): f.write(c)
    return p


def done_pieces(ep):
    r, e = px("GET", f"{REPO}/contents/f4p/ep{ep}", "github", query_params={"ref": "dji-transfer"})
    return {re.sub(r"\.part\d+$", "", x["name"]) for x in (r or [])} if isinstance(r, list) else set()


def do_piece(ep, j, dur=4):
    t = time.time(); src = ensure_og(ep); out = f"/home/user/f4p/q{ep}_{j:02d}.mp4"
    cmd = (f"{FF} -v error -y -threads 1 -filter_threads 1 -ss {j*dur} -t {dur} -i {src} "
           f"-map 0:v:0 -map 0:a:0 -vf fps=30,scale=1440:1080 -frames:v {dur*30} -threads 1 "
           f"-c:v libx264 -preset veryfast -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 {out}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode: return f"ENC FAIL {ep} {j} {r.stderr[-300:]}"
    data = open(out, "rb").read(); CH = 3 << 20
    for k, off in enumerate(range(0, len(data), CH)):
        path = f"f4p/ep{ep}/q{j:02d}.part{k:02d}"
        for tr in range(3):
            res, err = px("PUT", f"{REPO}/contents/{path}", "github",
                          body={"message": f"xfer {path}", "content": base64.b64encode(data[off:off+CH]).decode(),
                                "branch": "dji-transfer"})
            if not err: break
            time.sleep(2)
        if err: return f"PUT FAIL {path} {str(err)[:200]}"
    os.remove(out)
    return f"ep{ep} piece {j} total {time.time()-t:.0f}s"


# Ep. 4 is complete (5 s pieces q00-q06). Ep. 1-3 use 4 s pieces. Build the queue from what is missing:
QUEUE = []
for ep in "123":
    have = done_pieces(ep)
    QUEUE += [(ep, j) for j in range(math.ceil(DUR[ep] / 4)) if f"q{j:02d}" not in have]
_p("remaining pieces:", len(QUEUE), QUEUE[:3])


def nxt():
    ep, j = QUEUE[0]; r = do_piece(ep, j)
    if "FAIL" not in r: QUEUE.pop(0)
    _p(r, "| left", len(QUEUE))
