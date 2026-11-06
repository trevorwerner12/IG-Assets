import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
S = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(S, "trials_src")
OUT = "/home/user/IG-Assets/trial-reels"
os.makedirs(OUT, exist_ok=True)
A = os.path.join(S, "fonts/Anton.ttf")
R = {1:(1.00,1.00,"none",0.0,True),2:(1.10,1.00,"none",0.0,False),3:(0.90,1.00,"none",0.0,False),
     4:(1.00,1.06,"warm",0.0,False),5:(1.10,1.00,"punch",0.0,True),6:(1.05,1.00,"none",0.4,False),
     7:(0.95,1.04,"cool",0.0,True)}
GR = {"none":"", "warm":",colorbalance=rs=0.05:gs=0.01:bs=-0.05:rm=0.03:bm=-0.03",
      "cool":",colorbalance=rs=-0.04:bs=0.05:bm=0.03", "punch":",eq=saturation=1.18:contrast=1.07"}
TM = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,"
      "zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
def probe(p):
    e = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "csv=p=0", p],
                       capture_output=True, text=True).stdout
    dur = max(float(x) for x in re.findall(r"^[\d.]+$", e, re.M))
    return dur, "audio" in e
def endcard():
    p = os.path.join(S, "trials_endcard.png")
    W, H = 1080, 1920
    im = Image.new("RGBA", (W, H), (0, 0, 0, 165)); d = ImageDraw.Draw(im)
    for txt, sz, y in [("FOLLOW", 150, 760), ("@FUELED_4_FITNESS", 96, 950), ("FOR MORE HIGH-PROTEIN EATS", 58, 1085)]:
        f = ImageFont.truetype(A, sz); w = d.textlength(txt, font=f)
        d.text(((W-w)/2, y), txt, font=f, fill=(255,255,255,255), stroke_width=6, stroke_fill=(0,0,0,255))
    im.save(p); return p
EC = endcard()
def render(v, day, rec=None):
    sp, z, g, trim, ec = R[rec or day]
    src = f"{SRC}/{v}.mov"; out = f"{OUT}/{v}_d{day}.mp4"
    if os.path.exists(out) and os.path.getsize(out) > 100000: return out
    dur, has_a = probe(src)
    D = (dur - trim) / sp
    zw, zh = int(round(1080*z/2)*2), int(round(1920*z/2)*2)
    vf = (f"[0:v]scale={zw}:{zh}:flags=lanczos,crop=1080:1920,{TM}{GR[g]},"
          f"setpts=(PTS-STARTPTS)/{sp},fps=30")
    args = ["ffmpeg", "-y", "-v", "error"]
    if trim: args += ["-ss", str(trim)]
    args += ["-i", src]
    if ec:
        args += ["-loop", "1", "-t", f"{D+1.6:.3f}", "-i", EC]
        vf += (f",tpad=stop_mode=clone:stop_duration=1.6[base];[1:v]format=rgba,fade=t=in:st={D:.3f}:d=0.3:alpha=1[ec];"
               f"[base][ec]overlay=0:0:enable='gte(t,{D:.3f})',format=yuv420p[v]")
        T = D + 1.6
    else:
        vf += ",format=yuv420p[v]"; T = D
    if has_a:
        af = (f"[0:a]atempo={sp},apad,atrim=0:{T:.3f},afade=t=out:st={max(0,T-1.2):.3f}:d=1.2[a]" if ec
              else f"[0:a]atempo={sp}[a]")
        fc, amap = vf + ";" + af, "[a]"
    else:
        args += ["-f", "lavfi", "-t", f"{T:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
        fc, amap = vf, f"{2 if ec else 1}:a"
    args += ["-filter_complex", fc, "-map", "[v]", "-map", amap, "-t", f"{T:.3f}",
             "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-profile:v", "high", "-maxrate", "10M", "-bufsize", "20M",
             "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
             "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", out + ".tmp.mp4"]
    subprocess.run(args, check=True); os.rename(out + ".tmp.mp4", out)
    return out
jobs = [a.split(":") for a in sys.argv[1:]]
def run(j):
    v, d = j[0], j[1]; rec = int(j[2]) if len(j) > 2 else None
    try: return f"done {v} d{d} {os.path.getsize(render(v, int(d), rec))}"
    except Exception as e: return f"FAIL {v} d{d} {e!r}"
with ThreadPoolExecutor(2) as ex:
    for r in ex.map(run, jobs): print(r, flush=True)
