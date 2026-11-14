"""Fuel 4 Performance trial-reel variants.

usage: python3 render.py base EP          # assemble 1440p proxy pieces -> blurred 1080x1920 base (eps 1-4)
       python3 render.py var EP V [EP V]  # render variant V of episode EP into f4p-trials/out/
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

R = "/home/user/IG-Assets"
SP = os.environ.get("F4P_WORK", "/tmp/f4p_work")  # scratch space for proxies, bases and overlay PNGs
os.makedirs(SP, exist_ok=True)
D = os.path.join(R, "f4p-trials")
PLAN = json.load(open(os.path.join(D, "plan.json")))
TR = json.load(open(os.path.join(D, "transcripts.json")))["tr"]
ANTON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Anton.ttf")
W, H = 1080, 1920
SRC = {"5": f"{R}/dji-reel/jensen_full_interview_reel.mp4",
       "6": f"{R}/kulasingam-reel/kulasingam_interview_reel.mp4",
       "7": f"{R}/squires-reel/squires_interview_reel.mp4"}
BLUR = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=30:3,eq=brightness=-0.10[bg];"
        "[b]scale=1080:810:flags=lanczos[fg];[bg][fg]overlay=0:555,eq=saturation=1.06:contrast=1.03,unsharp=5:5:0.3")
# whisper mishearings that can show up in burned-in captions
FIX = {"candice": "Kansas", "canosier": "Kansas City", "rockford": "Roccaforte", "valls": "Vols", "canyac": "Caniac",
       "livy": "Livvy", "kula": "Kula", "singham": "singam", "c4": "C4", "p4": "P4"}


def run(args):
    subprocess.run(args, check=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def gfx_png(name, cx, maxw, maxh, path, baseline=495):
    from PIL import ImageFilter
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.open(os.path.join(D, "gfx", name + ".png")).convert("RGBA")
    k = min(maxw / g.width, maxh / g.height); g = g.resize((int(g.width * k), int(g.height * k)), Image.LANCZOS)
    x, y = cx - g.width // 2, baseline - g.height
    sh = Image.new("RGBA", g.size, (0, 0, 0, 0)); sh.putalpha(g.getchannel("A").point(lambda v: int(v * 0.45)))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x + 8, y + 12)); img.alpha_composite(g, (x, y))
    img.save(path); return path


def base(ep):
    """blurred 1080x1920 version of the episode, with its food graphics (eps 1-4) burned in"""
    if ep in SRC:
        return SRC[ep]
    plain = base_plain(ep)
    spec = PLAN.get("gfx", {}).get(ep)
    if not spec:
        return plain
    out = os.path.join(SP, f"f4p_gfx_ep{ep}.mp4")
    if os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(os.path.join(D, "plan.json")):
        return out
    T = dur(plain); args = ["ffmpeg", "-v", "error", "-y", "-i", plain]; fc = []
    for k, (name, a, b, cx, mw, mh) in enumerate(spec):
        args += ["-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", gfx_png(name, cx, mw, mh, os.path.join(SP, f"f4p_g{ep}_{k}.png"))]
        fc.append(f"[{k+1}:v]format=rgba,fade=t=in:st={a}:d=0.18:alpha=1,fade=t=out:st={b-0.18:.2f}:d=0.18:alpha=1[g{k}]")
        fc.append(f"[{'0:v' if k == 0 else f'b{k}'}][g{k}]overlay=0:0:enable='between(t,{a},{b})'[b{k+1}]")
    fc.append(f"[b{len(spec)}]format=yuv420p[v]")
    run(args + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow",
                "-crf", "17", "-c:a", "copy", "-movflags", "+faststart", out])
    return out


def base_plain(ep):
    out = os.path.join(SP, f"f4p_base_ep{ep}.mp4")
    if os.path.exists(out):
        return out
    d = os.path.join(SP, f"f4p_ep{ep}"); os.makedirs(d, exist_ok=True)
    run(["git", "-C", R, "fetch", "-q", "origin", "dji-transfer"])
    names = subprocess.run(["git", "-C", R, "ls-tree", "--name-only", "origin/dji-transfer", f"f4p/ep{ep}/"],
                           capture_output=True, text=True).stdout.split()
    pieces = sorted({re.sub(r"\.part\d+$", "", n) for n in names})
    with open(f"{d}/list.txt", "w") as L:
        for pc in pieces:
            fp = f"{d}/{os.path.basename(pc)}.mp4"
            with open(fp, "wb") as f:
                for part in sorted(n for n in names if n.startswith(pc + ".part")):
                    f.write(subprocess.run(["git", "-C", R, "cat-file", "blob", f"origin/dji-transfer:{part}"],
                                           capture_output=True, check=True).stdout)
            L.write(f"file '{fp}'\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{d}/list.txt",
         "-filter_complex", BLUR + ",format=yuv420p[v]", "-map", "[v]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    return out


def text_png(lines, path, size=74, y0=1425, gap=88):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(ANTON, size)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y0 + i * gap), ln, font=f, fill=(255, 255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 255))
    im.save(path); return path


PHRASES = {  # per-episode transcript corrections: lowercase word run -> replacement words
    "5": [(["chocolate", "meal", "looks"], ["chocolate", "milk's"]), (["stomachs", "that"], ["stomach,", "so"])],
    "6": [(["between-inning-snack?"], ["between-inning", "snack?"]), (["between-inning-snack"], ["between-inning", "snack"])],
    "7": [(["usually", "in", "espresso"], ["usually", "an", "espresso"])],
    "2": [(["trying", "to", "cheat"], ["try", "not", "to", "cheat"]), (["canes"], ["Cane's"])],
    "3": [(["to", "win", "food"], ["to", "have", "food"])],
}
# stretches where the audio is too muddy for whisper: (start, end, replacement words), source seconds
RANGES = {
    "1": [(42.2, 46.2, ["and", "hits", "the", "home", "runs.", "He", "gets", "Chipotle", "a", "lot", "before", "the", "game."])],
}


def phrase_fix(ep, words):
    for a, b, rep in RANGES.get(ep, []):
        keep = [w for w in words if not (a <= w[0] < b)]
        step = (b - a) / len(rep)
        words = sorted(keep + [[a + k * step, a + (k + 1) * step, r] for k, r in enumerate(rep)], key=lambda w: w[0])
    norm = lambda w: re.sub(r"[.,!?]$", "", w.lower())
    for pat, rep in PHRASES.get(ep, []):
        i = 0
        while i <= len(words) - len(pat):
            if [norm(x[2]) for x in words[i:i + len(pat)]] == [norm(x) for x in pat]:
                s, e = words[i][0], words[i + len(pat) - 1][1]
                step = (e - s) / len(rep)
                words[i:i + len(pat)] = [[s + k * step, s + (k + 1) * step, r] for k, r in enumerate(rep)]
            i += 1
    return words


def caption_groups(ep, t0, t1):
    words = []
    for s, e, w in TR[ep]:
        s, e = s + PLAN["eps"][ep]["shift"], e + PLAN["eps"][ep]["shift"]
        if s < t0 - 0.05 or s >= t1: continue
        w = w.strip()
        key = re.sub(r"[^a-z0-9]", "", w.lower())
        if key in FIX: w = re.sub(re.escape(w.strip(".,?!")), FIX[key], w, flags=re.I) if w.strip(".,?!") else w
        if words and w[:1] in "-'":  # whisper splits "go-to", "mid-inning", "o'clock" into two tokens
            words[-1][1] = e; words[-1][2] += w; continue
        if re.sub(r"[^a-z]", "", w.lower()) in ("um", "uh"): continue
        words.append([s, e, w])
    words = phrase_fix(ep, words)
    groups, cur = [], []
    for s, e, w in words:
        cur.append((s, e, w))
        txt = " ".join(x[2] for x in cur)
        if len(cur) >= 3 or len(txt) >= 16 or w.endswith((".", "?", "!", ",")):
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        a = g[0][0]; b = min(g[-1][1] + 0.35, groups[i + 1][0][0] if i + 1 < len(groups) else t1)
        out.append((a, b, re.sub(r"[.,]$", "", " ".join(x[2] for x in g)).upper()))
    return out


def variant(ep, v):
    cfg, E = PLAN["variants"][v], PLAN["eps"][ep]
    src = base(ep); total = dur(src)
    t0 = E["cut"] if cfg["cold"] else 0.0
    sp = cfg["speed"]
    out_dir = os.path.join(D, "out"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"ep{ep}_v{v}.mp4")
    if os.path.exists(out) and not os.environ.get("F4P_FORCE"):
        return out
    ov = []  # (png, start, end) in OUTPUT time
    T = (total - t0) / sp
    if cfg["hook"]:
        ov.append((text_png(E["hook"], os.path.join(SP, f"f4p_hook{ep}.png")), 0, T))
    if cfg["caps"]:
        # all caption cards go in as ONE image-sequence input (concat demuxer), not one input per card:
        # ~100 looped full-frame RGBA inputs got the renders OOM-killed
        cy = 1655 if cfg["hook"] else 1560
        blank = os.path.join(SP, "f4p_blank.png")
        if not os.path.exists(blank): Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
        lst, t = [], 0.0
        for k, (a, b, txt) in enumerate(caption_groups(ep, t0, total)):
            a, b = max((a - t0) / sp, t), (b - t0) / sp
            if b <= a: continue
            if a > t: lst += [f"file '{blank}'", f"duration {a - t:.3f}"]
            p = text_png([txt], os.path.join(SP, f"f4p_cap{ep}_{v}_{k:03d}.png"), size=82, y0=cy, gap=0)
            lst += [f"file '{p}'", f"duration {b - a:.3f}"]; t = b
        lst += [f"file '{blank}'", f"duration {max(T - t, 0.1):.3f}", f"file '{blank}'"]
        cl = os.path.join(SP, f"f4p_caps_{ep}_{v}.txt"); open(cl, "w").write("\n".join(lst) + "\n")
        ov.append(("CONCAT:" + cl, 0, T))
    vf = f"[0:v]trim=start={t0},setpts=(PTS-STARTPTS)/{sp},fps=30"
    if cfg["punch"]: vf += ",eq=saturation=1.15:contrast=1.06"
    vf += "[v0]"
    af = f"[0:a]atrim=start={t0},asetpts=PTS-STARTPTS,atempo={sp}[a]"
    args = ["ffmpeg", "-v", "error", "-y", "-i", src]
    fc = [vf, af]
    for k, (p, a, b) in enumerate(ov):
        if p.startswith("CONCAT:"):
            args += ["-f", "concat", "-safe", "0", "-i", p[7:]]
            fc.append(f"[{k+1}:v]fps=30,format=rgba[c{k}]")
            fc.append(f"[v{k}][c{k}]overlay=0:0:eof_action=pass[v{k+1}]")
            continue
        args += ["-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", p]
        fc.append(f"[v{k}][{k+1}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{k+1}]")
    fc.append(f"[v{len(ov)}]format=yuv420p[v]")
    args += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-t", f"{T:.3f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "8M", "-bufsize", "16M", "-profile:v", "high",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out + ".tmp.mp4"]
    run(args); os.replace(out + ".tmp.mp4", out)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "base":
        print(base(sys.argv[2]))
    elif sys.argv[1] == "caps":
        for g in caption_groups(sys.argv[2], PLAN["eps"][sys.argv[2]]["cut"], 999): print(f"{g[0]:6.2f} {g[2]}")
    else:
        a = sys.argv[2:]
        for ep, v in zip(a[::2], a[1::2]):
            p = variant(ep, v); print("done", p, round(dur(p), 2))
