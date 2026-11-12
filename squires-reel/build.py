import os, subprocess
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
S = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(S, "sgfx"); W, H = 1080, 1920
V = os.path.join(S, "squires/sq_1440.mp4")
OUT = "/home/user/IG-Assets/squires-reel/squires_interview_reel.mp4"
def layer(name, cx, cy, maxw, maxh):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.open(f"{G}/{name}.png").convert("RGBA")
    k = min(maxw / g.width, maxh / g.height); g = g.resize((int(g.width * k), int(g.height * k)), Image.LANCZOS)
    x, y = cx - g.width // 2, cy - g.height // 2
    sh = Image.new("RGBA", g.size, (0, 0, 0, 0)); sh.putalpha(g.getchannel("A").point(lambda v: int(v * 0.45)))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(sh, (x + 8, y + 12)); img.alpha_composite(g, (x, y))
    p = f"{G}/L_{name}_{cx}.png"; img.save(p); return p

CY = 280
L = [  # (start, end, png) -- product graphics go here once images arrive
]
fc = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=30:3,eq=brightness=-0.10[bg];"
      "[b]scale=1080:810:flags=lanczos[fg];[bg][fg]overlay=0:555,eq=saturation=1.06:contrast=1.03,unsharp=5:5:0.3[v0]")
args = ["ffmpeg", "-y", "-v", "error", "-i", V]
for k, (a, b, p) in enumerate(L):
    args += ["-loop", "1", "-t", "82.7", "-framerate", "30", "-i", p]
    fc += (f";[{k+1}:v]format=rgba,fade=t=in:st={a}:d=0.18:alpha=1,fade=t=out:st={b-0.18:.2f}:d=0.18:alpha=1[o{k}]"
           f";[v{k}][o{k}]overlay=0:0:enable='between(t,{a},{b})'[v{k+1}]")
fc += f";[v{len(L)}]format=yuv420p[v]"
args += ["-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", OUT]
subprocess.run(args, check=True); print("ok")
