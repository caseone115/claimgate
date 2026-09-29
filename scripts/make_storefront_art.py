#!/usr/bin/env python3
"""Generate the storefront art: cover, thumbnail and a free-kit variant.

The listing had no image at all, which makes its card in search, its profile
card and every social share fall back to a generic placeholder. These are drawn
from the same palette as the landing page so a click-through looks continuous.

    python3 scripts/make_storefront_art.py
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "storefront"
FONTS = pathlib.Path("/usr/share/fonts/truetype/dejavu")

BG, PANEL, LINE = (10, 11, 13), (17, 19, 22), (35, 39, 45)
INK, MUTED, DIM = (242, 244, 247), (148, 154, 164), (107, 114, 128)
BRAND, BAD, GOOD = (94, 234, 212), (248, 113, 113), (74, 222, 128)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def pill(d, xy, text, f, fill, fg):
    x, y = xy
    pad, gap = 16, 10
    w = d.textlength(text, font=f)
    h = f.size + 18
    d.rounded_rectangle([x, y, x + w + pad * 2, y + h], radius=h // 2, fill=fill)
    d.text((x + pad, y + h // 2), text, font=f, fill=fg, anchor="lm")
    return x + w + pad * 2 + gap


def cover(path, title, sub, badge, price_line, price_colour):
    """1280x720 — the storefront cover and the social share image."""
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for y in range(H):  # subtle top-lit gradient
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10 + 8 * (1 - t)), int(11 + 9 * (1 - t)), int(13 + 11 * (1 - t))))
    d.rectangle([0, 0, W, 5], fill=BRAND)
    f_badge, f_title, f_sub, f_mono, f_price, f_chip = (
        font("DejaVuSans-Bold.ttf", 22), font("DejaVuSans-Bold.ttf", 58),
        font("DejaVuSans.ttf", 26), font("DejaVuSansMono.ttf", 22),
        font("DejaVuSans-Bold.ttf", 32), font("DejaVuSans.ttf", 21))

    pill(d, (68, 64), badge, f_badge, BRAND, (10, 11, 13))
    d.text((68, 128), title, font=f_title, fill=INK)
    y = 222
    for line in sub:
        d.text((68, y), line, font=f_sub, fill=MUTED)
        y += 40

    # right column: what the gate actually catches — fills the top-right quadrant
    # with information rather than empty space
    for i, caught in enumerate(("unsupported figure", "absolute claim", "missing AI disclosure")):
        cy = 156 + i * 52
        w = d.textlength(caught, font=f_chip)
        x1 = 1212
        x0 = x1 - w - 44
        d.rounded_rectangle([x0, cy, x1, cy + 38], radius=19, outline=(45, 51, 59), width=2)
        d.ellipse([x0 + 15, cy + 15, x0 + 23, cy + 23], fill=BRAND)
        d.text((x0 + 32, cy + 19), caught, font=f_chip, fill=MUTED, anchor="lm")

    d.rounded_rectangle([64, 322, 1216, 592], radius=18, fill=PANEL, outline=LINE, width=2)
    rows = [
        ("$ claimgate init my-project", MUTED),
        ("wrote policy.json, evidence/, CHECKLIST.md, .github/workflows/gate.yml", DIM),
        ("", DIM),
        ("$ claimgate check draft.md --evidence evidence/", MUTED),
        ("BLOCKED  unsupported figure: 4.2x faster", BAD),
        ("BLOCKED  absolute claim: guaranteed", BAD),
        ("OK       claim substantiated by evidence/acme-spec.md", GOOD),
    ]
    yy = 348
    for text, colour in rows:
        if text:
            d.text((92, yy), text, font=f_mono, fill=colour)
        yy += 31
    d.text((68, 622), price_line, font=f_price, fill=price_colour)
    im.save(path, "PNG", optimize=True)
    return path


def thumb(path):
    """600x600 square — profile, Discover and library thumbnails."""
    S = 600
    im = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(im)
    for y in range(S):
        t = y / S
        d.line([(0, y), (S, y)], fill=(int(10 + 8 * (1 - t)), int(11 + 9 * (1 - t)), int(13 + 11 * (1 - t))))
    d.rounded_rectangle([44, 44, S - 44, S - 44], radius=28, fill=PANEL, outline=LINE, width=3)
    d.rectangle([44, 44, S - 44, 51], fill=BRAND)
    d.text((S // 2, 190), "BLOCKED", font=font("DejaVuSans-Bold.ttf", 86), fill=BAD, anchor="mm")
    d.text((S // 2, 268), "before it ships", font=font("DejaVuSans.ttf", 40), fill=MUTED, anchor="mm")
    d.line([(110, 330), (S - 110, 330)], fill=LINE, width=2)
    d.text((S // 2, 372), "ClaimGate", font=font("DejaVuSans-Bold.ttf", 52), fill=INK, anchor="mm")
    d.text((S // 2, 428), "claim substantiation", font=font("DejaVuSansMono.ttf", 25), fill=BRAND, anchor="mm")
    d.text((S // 2, 500), "for AI-assisted copy", font=font("DejaVuSans.ttf", 26), fill=DIM, anchor="mm")
    im.save(path, "PNG", optimize=True)
    return path


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    made = [
        cover(OUT / "claimgate-cover-1280x720.png",
              "ClaimGate",
              ["A publish gate for AI-assisted marketing copy.",
               "Every figure must appear in your evidence — or it is blocked."],
              "FOR AI-ASSISTED COPY", "US$149  ·  one-off  ·  source is public and MIT",
              BRAND),
        cover(OUT / "claimgate-starter-kit-cover-1280x720.png",
              "ClaimGate Starter Kit",
              ["The free front door: policy, evidence folder, checklist",
               "and a CI job that gates every pull request."],
              "FREE  ·  PAY WHAT YOU WANT", "Suggested US$19  ·  free forever  ·  no API key",
              GOOD),
        thumb(OUT / "claimgate-thumbnail-600x600.png"),
    ]
    for p in made:
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024}KB  {Image.open(p).size}")
