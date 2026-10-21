"""Build YouTube Shorts (1080x1920, 9:16) from the re-rendered beat clips.

  python make_short.py 1_barrel            # -> shorts/out/short_1_barrel.mp4  (+ a few preview frames)
  python make_short.py all

Layout: a square 1080x1080 crop of the 16:9 clip (native resolution, no upscaling) in the middle, a blurred copy of the same
picture filling the 9:16 frame, a big hook line at the top for the first seconds, burned-in captions below the picture,
an end card for the last seconds. Narration comes from each clip's own mp4 (the real Algieba voice).
Edit SHORTS below to change segments (clip time window, crop x), hook text, captions and the end card.
"""
import os
import subprocess
import sys
import wave

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RENDERS = os.path.join(HERE, "render", "renders")
OUT = os.path.join(HERE, "out")
FONTS = "C:/Windows/Fonts/"
W, H = 1080, 1920
LEAD = 0.8                          # narration starts this far into every clip
GOLD = (255, 205, 70)

# segment: beat, t0/t1 = window inside the clip (seconds; None = narration start - 0.2 .. narration end + 0.3),
#          x = left edge of the 1080-px crop in the 1920-px frame (420 = centred), cap = burn captions, mute = no narration
SHORTS = {
    "1_barrel": dict(
        title="One cannonball. One barrel. The Dutch surrendered.",
        hook=["WHAT IF ONE CANNONBALL", "HIT THE WRONG BARREL?"], hook_secs=3.4,
        segments=[
            dict(beat="S50", t0=2.2, t1=5.2, x=420, cap=False, mute=True),        # teaser: the explosion, no voice
            dict(beat="S48", x=420, cap=True),
            dict(beat="S49", x=420, cap=True),
            dict(beat="S50", t0=0.6, x=420, cap=True),
        ],
        end=["FULL STORY", "THE BATTLE OF COLACHEL", "link in the description"], end_secs=2.6),
    "2_captain": dict(
        title="The Dutch captain who was captured, then hired by the king",
        hook=["HE LOST THE BATTLE.", "THE KING HIRED HIM."], hook_secs=3.4,
        segments=[
            dict(beat="S55", x=420, cap=True),
            dict(beat="S56", x=420, cap=True),
            dict(beat="S58", x=420, cap=True),
            dict(beat="S60", x=420, cap=True),
        ],
        end=["FULL STORY", "THE BATTLE OF COLACHEL", "link in the description"], end_secs=2.6),
    "3_twice": dict(
        title="One lucky shot hit gunpowder twice (1740 and 1741)",
        hook=["A LUCKY SHOT.", "THE SAME TARGET. TWICE."], hook_secs=3.4,
        segments=[
            dict(beat="S26", x=420, cap=True, label=("NEAR KOLLAM", "1740")),
            dict(beat="S51", x=420, cap=True, label=("COLACHEL", "1741")),
        ],
        end=["FULL STORY", "THE BATTLE OF COLACHEL", "link in the description"], end_secs=2.6),
}


def lines():
    d = {}
    for ln in open(os.path.join(ROOT, "audio", "lines.txt"), encoding="utf-8"):
        if "|" in ln:
            b, t = ln.rstrip("\n").split("|", 1)
            d[b] = t
    return d


def wav_secs(beat):
    with wave.open(os.path.join(HERE, "render", f"{beat}.wav")) as w:
        return w.getnframes() / w.getframerate()


def clip_path(beat):
    for f in os.listdir(RENDERS):
        if f.endswith("_1080p.mp4") and f"_{beat}_" in f:
            return os.path.join(RENDERS, f)
    sys.exit(f"clip for {beat} not rendered yet in {RENDERS}")


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def outlined(d, xy, text, fnt, fill, stroke=8, anchor="ma"):
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def chunks(text, n=6):
    words, out, cur = text.split(), [], []
    for w in words:
        cur.append(w)
        if len(cur) >= n or w.endswith((".", "?", "!")):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def caption_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font("arialbd.ttf", 74)
    words, rows, cur = text.upper().split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > W - 150 and cur:
            rows.append(cur)
            cur = w
        else:
            cur = t
    rows.append(cur)
    y = 1545
    for r in rows:
        outlined(d, (W // 2, y), r, f, (255, 255, 255), 9)
        y += 92
    img.save(path)


def hook_png(lines_, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font("impact.ttf", 100)
    y = 170
    for i, r in enumerate(lines_):
        outlined(d, (W // 2, y), r, f, GOLD if i == len(lines_) - 1 else (255, 255, 255), 10)
        y += 125
    img.save(path)


def label_png(place, date, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([70, 450, 70 + 500, 450 + 120], fill=(24, 19, 15, 225), outline=GOLD + (255,), width=3)
    d.text((100, 472), place, font=font("georgiab.ttf", 42), fill=GOLD)
    d.text((100, 525), date, font=font("georgiai.ttf", 34), fill=(245, 233, 205))
    img.save(path)


def end_png(rows, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1525, W, 1850], fill=(0, 0, 0, 175))
    outlined(d, (W // 2, 1560), rows[0], font("arialbd.ttf", 54), GOLD, 4)
    outlined(d, (W // 2, 1640), rows[1], font("impact.ttf", 84), (255, 255, 255), 6)
    outlined(d, (W // 2, 1765), rows[2], font("arial.ttf", 50), (235, 235, 235), 3)
    img.save(path)


def build(key):
    cfg = SHORTS[key]
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "_tmp_" + key)
    os.makedirs(tmp, exist_ok=True)
    text = lines()
    segs, t = [], 0.0
    for s in cfg["segments"]:
        secs = wav_secs(s["beat"])
        t0 = s.get("t0", max(0.0, LEAD - 0.2))
        t1 = s.get("t1", LEAD + secs + 0.3)
        segs.append(dict(s, t0=t0, t1=t1, start=t, dur=t1 - t0, secs=secs))
        t += t1 - t0
    total = t
    overlays = []                                                    # (png, t_on, t_off)
    hook_png(cfg["hook"], os.path.join(tmp, "hook.png"))
    overlays.append(("hook.png", 0.0, cfg["hook_secs"]))
    k = 0
    for s in segs:
        if s.get("label"):
            p = f"label{k}.png"
            label_png(*s["label"], os.path.join(tmp, p))
            overlays.append((p, s["start"] + 0.4, s["start"] + 3.6))
            k += 1
        if not s.get("cap"):
            continue
        cs = chunks(text[s["beat"]])
        tot = sum(len(c) for c in cs)
        pos = 0
        for c in cs:
            a = LEAD + s["secs"] * pos / tot
            pos += len(c)
            b = LEAD + s["secs"] * pos / tot
            p = f"cap{k}.png"
            caption_png(c, os.path.join(tmp, p))
            k += 1
            on, off = s["start"] + max(0.0, a - s["t0"]), s["start"] + min(s["dur"], b - s["t0"])
            off = min(off, total - cfg["end_secs"])
            if off > on:
                overlays.append((p, on, off))
    end_png(cfg["end"], os.path.join(tmp, "end.png"))
    overlays.append(("end.png", total - cfg["end_secs"], total))

    ins, fc = [], []
    for i, s in enumerate(segs):
        ins += ["-i", clip_path(s["beat"])]
        x = s.get("x", 420)
        fc.append(f"[{i}:v]trim=start={s['t0']:.3f}:end={s['t1']:.3f},setpts=PTS-STARTPTS,fps=24,split=2[a{i}][b{i}]")
        fc.append(f"[a{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:6,eq=brightness=-0.12[bg{i}]")
        fc.append(f"[b{i}]crop=1080:1080:{x}:0[fg{i}]")
        fc.append(f"[bg{i}][fg{i}]overlay=0:(H-h)/2[v{i}]")
        if s.get("mute"):
            fc.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={s['dur']:.3f}[au{i}]")
        else:
            fc.append(f"[{i}:a]atrim=start={s['t0']:.3f}:end={s['t1']:.3f},asetpts=PTS-STARTPTS,aresample=48000[au{i}]")
    fc.append("".join(f"[v{i}][au{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[cv][ca]")
    last, n0 = "cv", len(segs)
    for j, (png, on, off) in enumerate(overlays):
        ins += ["-loop", "1", "-i", os.path.join(tmp, png)]
        idx = n0 + j
        nxt = f"o{j}"
        fc.append(f"[{last}][{idx}:v]overlay=0:0:enable='between(t,{on:.2f},{off:.2f})'[{nxt}]")
        last = nxt
    fc.append(f"[ca]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    out = os.path.join(OUT, f"short_{key}.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", f"[{last}]", "-map", "[aout]",
                                                    "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                                                    "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "aac", "-b:a", "192k", out]
    subprocess.run(cmd, check=True)
    for tt in (1.5, total * 0.45, total - 1.2):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tt:.2f}", "-i", out, "-frames:v", "1",
                        os.path.join(OUT, f"prev_{key}_{int(tt * 10):03d}.png")], check=True)
    print(f"{out}  {total:.1f} s")


if __name__ == "__main__":
    for k in (SHORTS if sys.argv[1:] == ["all"] else sys.argv[1:]):
        build(k)
