"""Make the text overlays for the final film (title card, name plates, place/date labels) as 1920x1080 transparent PNGs,
plus overlays.json (when each one is shown) computed from the real clip timings.

  python make_overlays.py            # writes edit/overlays/*.png, edit/title_card.png, edit/overlays.json

Styles follow _channel-context/Visual_Style.md: name plates are a dark plaque with a thin gold border, the name in serif
capitals and a one-line italic gloss; the title card is a dark map silhouette with a spaced small "THE BATTLE OF", a large
gold serif title, a line of sides and date, thin gold rules and a small red star. Edit PLATES / LABELS below to change text or timing.
Times are given as (beat, seconds into the narration of that beat) so they follow any later re-timing.
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "blender"))
FONTS = "C:/Windows/Fonts/"
W, H = 1920, 1080
GOLD, CREAM, DARK = (214, 176, 78), (245, 233, 205), (24, 19, 15)
INTRO = 5.0                      # seconds of title card in front of S01

# beat, word in the narration at which the plate appears (None = start of the clip), name, gloss, seconds shown
PLATES = [
    ("S03", "Marthanda Varma", "MARTHANDA VARMA", "King of Travancore", 4.0),
    ("S19", "Gustaaf Willem van Imhoff", "GUSTAAF VAN IMHOFF", "Dutch governor of Ceylon", 4.0),
    ("S32", "Eustachius De Lannoy", "EUSTACHIUS DE LANNOY", "Dutch captain, about twenty-five", 4.0),
    ("S58", "Valiya Kappithan", "VALIYA KAPPITHAN", "\u201cThe Great Captain\u201d", 4.0),
]
# beat, offset into the clip (s), line 1 (place), line 2 (date or note), seconds shown
LABELS = [
    ("S01", 1.5, "COLACHEL, SOUTHERN INDIA", "August 1741", 4.0),
    ("S07", 1.0, "KERALA", "The early 1700s", 3.5),
    ("S11", 3.5, "KOCHI", "The Dutch fort", 3.5),
    ("S13", 3.0, "TRAVANCORE", "Capital: Padmanabhapuram", 3.5),
    ("S14", 1.5, "PADMANABHAPURAM", "1729", 3.5),
    ("S19", 0.8, "KOCHI", "1739", 3.0),
    ("S24", 3.0, "KOCHI", "November 1739: war is declared", 4.0),
    ("S25", 1.5, "NEAR KOLLAM", "1740", 3.0),
    ("S27", 1.5, "VARKALA", "1740", 3.0),
    ("S30", 1.0, "OFF COLACHEL", "26 November 1740", 4.0),
    ("S31", 1.0, "COLACHEL", "February 1741", 3.5),
    ("S36", 1.5, "KALKULAM", "1741", 3.0),
    ("S37", 1.0, "THIRUVATTAR", "Adikesava Perumal temple", 3.5),
    ("S38", 1.0, "COLACHEL", "June 1741: the monsoon", 3.5),
    ("S48", 1.0, "COLACHEL", "5 August 1741", 3.5),
    ("S52", 7.0, "THE SURRENDER", "7 August 1741 (Dutch records)", 4.0),
    ("S54", 1.0, "UDAYAGIRI FORT", "", 3.0),
    ("S59", 6.0, "THE NEDUMKOTTA", "A line of walls and ditches", 4.0),
    ("S60", 5.0, "UDAYAGIRI FORT", "1777", 3.5),
    ("S61", 1.0, "KANYAKUMARI", "October 1741", 3.5),
    ("S62", 1.0, "MAVELIKKARA", "1753", 3.0),
    ("S64", 1.0, "THIRUVANANTHAPURAM", "1750", 3.5),
    ("S65", 1.0, "COLACHEL, TODAY", "", 3.0),
]


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def spaced(draw, xy, text, fnt, fill, spacing, anchor="l"):
    """Draw text with extra letter spacing; anchor 'l' (left) or 'm' (centre)."""
    widths = [draw.textlength(c, font=fnt) for c in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x, y = xy
    if anchor == "m":
        x -= total / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=fnt, fill=fill)
        x += w + spacing
    return total


def plaque(lines, name, w_min=520):
    """A lower-left plate: dark plaque, thin gold border, serif capitals, italic gloss. lines = [(text, kind)]."""
    big, small = font("georgiab.ttf", 46), font("georgiai.ttf", 30)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tw = max([spaced(ImageDraw.Draw(Image.new("RGBA", (10, 10))), (0, 0), t, big if k == "big" else small, CREAM, 4 if k == "big" else 0)
              for t, k in lines] + [w_min - 80])
    pw, ph = int(tw + 80), 36 + sum(60 if k == "big" else 44 for _, k in lines)
    x0, y0 = 110, H - 130 - ph
    d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=DARK + (222,))
    d.rectangle([x0 + 6, y0 + 6, x0 + pw - 6, y0 + ph - 6], outline=GOLD + (255,), width=2)
    y = y0 + 20
    for t, k in lines:
        if k == "big":
            spaced(d, (x0 + 40, y), t, big, GOLD, 4)
            y += 60
        else:
            d.text((x0 + 40, y), t, font=small, fill=CREAM)
            y += 44
    img.save(os.path.join(HERE, "overlays", name + ".png"))


def title_card():
    """The 1920x1080 title card (opaque, dark, with a Kerala silhouette)."""
    import kerala_geo as geo
    img = Image.new("RGB", (W, H), (28, 24, 21))
    d = ImageDraw.Draw(img)
    poly = geo.land_polygon_detailed(120.0)
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    sc = (H * 1.02) / (max(ys) - min(ys))
    ox = W * 0.22
    pts = [(ox + (x - min(xs)) * sc * 1.0, H * 0.98 - (y - min(ys)) * sc) for x, y in poly]
    sil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sil).polygon(pts, fill=(58, 46, 36, 255), outline=(96, 76, 52, 255))
    from PIL import ImageChops, ImageFilter
    a = sil.getchannel("A").filter(ImageFilter.GaussianBlur(3))
    rad = Image.radial_gradient("L").point(lambda v: max(0, 255 - int(v * 1.25)))      # 255 at the centre, fading out
    rad = rad.resize((int(W * 1.1), int(H * 1.5)))
    ramp = Image.new("L", (W, H), 0)
    ramp.paste(rad, (int(W * 0.58 - rad.width / 2), int(H * 0.62 - rad.height / 2)))
    sil.putalpha(ImageChops.multiply(a, ramp))
    img.paste(sil, (0, 0), sil)
    d = ImageDraw.Draw(img)
    cx = W // 2 + 120
    small, big, mid = font("georgia.ttf", 34), font("georgiab.ttf", 190), font("georgiai.ttf", 40)
    spaced(d, (cx, 300), "T H E   B A T T L E   O F", small, CREAM, 8, anchor="m")
    d.line([(cx - 330, 365), (cx + 330, 365)], fill=GOLD, width=3)
    tw = spaced(ImageDraw.Draw(Image.new("RGB", (10, 10))), (0, 0), "COLACHEL", big, GOLD, 12)
    for off, col in ((5, (70, 52, 20)), (0, GOLD)):                   # a bevelled look: dark shadow then the gold face
        spaced(d, (cx + off, 400 + off), "COLACHEL", big, col, 12, anchor="m")
    d.line([(cx - 330, 640), (cx + 330, 640)], fill=GOLD, width=3)
    d.text((cx, 690), "Travancore vs the Dutch East India Company, 1741", font=mid, fill=CREAM, anchor="mm")
    star = [(cx, 770 - 22)]
    import math
    star = [(cx + (22 if i % 2 == 0 else 9) * math.sin(i * math.pi / 5), 790 - (22 if i % 2 == 0 else 9) * math.cos(i * math.pi / 5)) for i in range(10)]
    d.polygon(star, fill=(190, 40, 34))
    img.save(os.path.join(HERE, "title_card.png"))


def build():
    os.makedirs(os.path.join(HERE, "overlays"), exist_ok=True)
    from clip_timeline import beat_starts, word_time
    start, dur = beat_starts(INTRO)
    items = []
    for beat, phrase, name, gloss, secs in PLATES:
        fn = f"plate_{beat}"
        plaque([(name, "big"), (gloss, "small")], fn)
        t = word_time(beat, phrase, start, dur)
        items.append(dict(file=f"overlays/{fn}.png", t0=round(t, 2), t1=round(t + secs, 2), kind="plate", beat=beat))
    for beat, off, place, note, secs in LABELS:
        fn = f"label_{beat}"
        plaque([(place, "big")] + ([(note, "small")] if note else []), fn, w_min=420)
        t = start[int(beat[1:])] + off
        items.append(dict(file=f"overlays/{fn}.png", t0=round(t, 2), t1=round(t + secs, 2), kind="label", beat=beat))
    title_card()
    items.sort(key=lambda i: i["t0"])
    json.dump(dict(intro_seconds=INTRO, overlays=items), open(os.path.join(HERE, "overlays.json"), "w"), indent=2)
    print(f"{len(items)} overlays written; title card {INTRO}s; film length {sum(dur.values()) + INTRO:.0f}s")


if __name__ == "__main__":
    build()
