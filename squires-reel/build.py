import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont
S = "/tmp/claude-0/-home-user-IG-Assets/e11bd912-964a-50d4-be49-ff9fba913f95/scratchpad"
G = os.path.join(S, "sgfx"); W, H = 1080, 1920
V = os.path.join(S, "squires/sq_1440.mp4")
OUT = "/home/user/IG-Assets/squires-reel/squires_interview_reel.mp4"
ANTON = os.path.join(S, "fonts/Anton.ttf")
DUR, FPS = 82.7, 30

def layer(name, cx, cy, maxw, maxh):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.open(f"{G}/{name}.png").convert("RGBA")
    k = min(maxw / g.width, maxh / g.height); g = g.resize((int(g.width * k), int(g.height * k)), Image.LANCZOS)
    x, y = cx - g.width // 2, cy - g.height // 2
    sh = Image.new("RGBA", g.size, (0, 0, 0, 0)); sh.putalpha(g.getchannel("A").point(lambda v: int(v * 0.45)))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x + 8, y + 12)); img.alpha_composite(g, (x, y))
    p = f"{G}/L_{name}.png"; img.save(p); return p

# products on the left half of the top band
CX, CY = 280, 285
L = [
    (22.50, 32.00, layer("espresso", CX, CY, 400, 440)),   # "cup of coffee ... espresso"
    (37.70, 44.60, layer("c4", CX, CY, 400, 460)),         # "rip a C4"
    (52.60, 60.00, layer("p4", CX, CY, 420, 440)),         # "full scoop of P4"
]

# caffeine counter on the right half: (ramp start, ramp end, new total, pop label)
STEPS = [(26.2, 27.8, 120, "+120 MG"), (39.5, 40.6, 320, "+200 MG"), (57.5, 58.7, 470, "+150 MG")]
SHOW, LIMIT_T = 22.5, 70.6
PW, PH = 540, 555
f_lab, f_num, f_mg, f_pop, f_lim = (ImageFont.truetype(ANTON, s) for s in (56, 170, 64, 54, 40))
ORANGE = (255, 150, 30, 255)

def state(t):
    v, pop = 0, None
    for a, b, tot, lab in STEPS:
        prev = v
        if t >= b: v = tot
        elif t >= a:
            x = (t - a) / (b - a); v = prev + (tot - prev) * (1 - (1 - x) ** 3)
        if a <= t < b + 1.2: pop = lab
    return int(round(v)), pop

def ctext(d, cx, y, s, f, fill, stroke=8):
    w = d.textlength(s, font=f); d.text((cx - w / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))

FR = os.path.join(S, "sq_counter"); shutil.rmtree(FR, ignore_errors=True); os.makedirs(FR)
cache = {}
n = int(DUR * FPS) + 1
for i in range(n):
    t = i / FPS
    alpha = 0 if t < SHOW else min(1, (t - SHOW) / 0.3)
    v, pop = state(t); over = t >= LIMIT_T
    key = (round(alpha, 2), v, pop, over)
    if key not in cache:
        im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        if alpha > 0:
            d = ImageDraw.Draw(im); cx = PW // 2 - 10
            ctext(d, cx, 60, "CAFFEINE", f_lab, (255, 255, 255, 255), 6)
            num = str(v); col = ORANGE if over else (255, 255, 255, 255)
            nw = d.textlength(num, font=f_num); mw = d.textlength(" MG", font=f_mg)
            x0 = cx - (nw + mw) / 2
            d.text((x0, 130), num, font=f_num, fill=col, stroke_width=9, stroke_fill=(0, 0, 0, 255))
            d.text((x0 + nw, 222), " MG", font=f_mg, fill=col, stroke_width=6, stroke_fill=(0, 0, 0, 255))
            if over:
                ctext(d, cx, 380, "FDA DAILY LIMIT:", f_lim, (255, 255, 255, 255), 5)
                ctext(d, cx, 428, "400 MG", f_lim, ORANGE, 5)
            elif pop:
                ctext(d, cx, 390, pop, f_pop, ORANGE, 6)
            if alpha < 1:
                im.putalpha(im.getchannel("A").point(lambda p: int(p * alpha)))
        p = os.path.join(FR, f"u{len(cache):04d}.png"); im.save(p); cache[key] = p
    os.symlink(cache[key], os.path.join(FR, f"f{i:05d}.png"))

fc = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=30:3,eq=brightness=-0.10[bg];"
      "[b]scale=1080:810:flags=lanczos[fg];[bg][fg]overlay=0:555,eq=saturation=1.06:contrast=1.03,unsharp=5:5:0.3[v0]")
args = ["ffmpeg", "-y", "-v", "error", "-i", V]
for k, (a, b, p) in enumerate(L):
    args += ["-loop", "1", "-t", str(DUR), "-framerate", str(FPS), "-i", p]
    fc += (f";[{k+1}:v]format=rgba,fade=t=in:st={a}:d=0.18:alpha=1,fade=t=out:st={b-0.18:.2f}:d=0.18:alpha=1[o{k}]"
           f";[v{k}][o{k}]overlay=0:0:enable='between(t,{a},{b})'[v{k+1}]")
ci = len(L) + 1
args += ["-framerate", str(FPS), "-i", os.path.join(FR, "f%05d.png")]
fc += f";[{ci}:v]format=rgba[cnt];[v{len(L)}][cnt]overlay=540:0:shortest=0:eof_action=pass,format=yuv420p[v]"
args += ["-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", OUT]
subprocess.run(args, check=True); print("ok", len(cache), "unique counter frames")
