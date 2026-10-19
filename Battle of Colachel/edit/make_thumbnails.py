"""Thumbnail text variations (1280x720 JPG, well under YouTube's 2 MB limit) from the text-free stills in ../thumbnail/.

  python make_thumbnails.py        # writes ../thumbnail/variants/thumb_*.jpg and a contact sheet

Edit VARIANTS to change wording. Text is gold serif with a dark outline so it stays readable at phone size.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TH = os.path.abspath(os.path.join(HERE, "..", "thumbnail"))
OUT = os.path.join(TH, "variants")
FONT = "C:/Windows/Fonts/georgiab.ttf"
W, H = 1280, 720

# name, background file, [(text, size, x, y, anchor)], optional dark panel (x0, y0, x1, y1)
VARIANTS = [
    ("1_one_shot_cannon", "thumbnail_cannonball_no_text_1280x720.jpg",
     [("ONE SHOT", 128, 50, 40, "la"), ("COLACHEL  1741", 56, 56, 190, "la")], None),
    ("2_one_burning_shot_cannon", "thumbnail_cannonball_no_text_1280x720.jpg",
     [("ONE", 130, 50, 25, "la"), ("BURNING", 86, 50, 160, "la"), ("SHOT", 130, 50, 255, "la")], None),
    ("3_why_the_dutch_lost_king", "thumbnail_no_text_1280x720.jpg",
     [("WHY THE", 84, 780, 30, "ma"), ("DUTCH LOST", 104, 780, 112, "ma"), ("COLACHEL  1741", 52, 780, 235, "ma")], None),
    ("4_battle_of_colachel_cannon", "thumbnail_cannonball_no_text_1280x720.jpg",
     [("THE BATTLE OF", 54, 46, 400, "la"), ("COLACHEL", 96, 40, 462, "la"), ("1741", 70, 46, 585, "la")], None),
    ("5_one_shot_king", "thumbnail_no_text_1280x720.jpg",
     [("ONE SHOT", 128, 770, 25, "ma"), ("COLACHEL  1741", 56, 770, 170, "ma")], None),
]


def gold_text(img, text, size, x, y, anchor):
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(img)
    # soft shadow + dark outline
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 5, y + 6), text, font=f, fill=(0, 0, 0, 200), anchor=anchor, stroke_width=10, stroke_fill=(0, 0, 0, 200))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text((x, y), text, font=f, fill=(20, 12, 4, 255), anchor=anchor, stroke_width=9, stroke_fill=(20, 12, 4, 255))
    # gold face with a vertical gradient
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text((x, y), text, font=f, fill=255, anchor=anchor)
    bb = mask.getbbox()
    grad = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    y0, y1 = bb[1], bb[3]
    for yy in range(y0, y1 + 1):
        t = (yy - y0) / max(1, y1 - y0)
        c = (int(255 - 40 * t), int(232 - 72 * t), int(140 - 90 * t), 255)
        gd.line([(0, yy), (W, yy)], fill=c)
    img.paste(grad, (0, 0), mask)


def main():
    os.makedirs(OUT, exist_ok=True)
    tiles = []
    for name, bg, lines, _ in VARIANTS:
        im = Image.open(os.path.join(TH, bg)).convert("RGBA").resize((W, H))
        for text, size, x, y, anchor in lines:
            gold_text(im, text, size, x, y, anchor)
        p = os.path.join(OUT, f"thumb_{name}.jpg")
        im.convert("RGB").save(p, quality=92)
        tiles.append((name, im.convert("RGB")))
        print(p, os.path.getsize(p) // 1024, "KB")
    sheet = Image.new("RGB", (W, H * ((len(tiles) + 1) // 2) // 1))
    sheet = Image.new("RGB", (W, (H // 2) * ((len(tiles) + 1) // 2)))
    for i, (_, im) in enumerate(tiles):
        sheet.paste(im.resize((W // 2, H // 2)), ((i % 2) * W // 2, (i // 2) * H // 2))
    sheet.save(os.path.join(OUT, "contact_sheet.jpg"), quality=90)


if __name__ == "__main__":
    main()
