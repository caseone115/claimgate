#!/usr/bin/env python3
"""Social share cards for the public pages.

Why this exists: measured 2026-09-30, the live landing page and the Article 50
article carry **no `og:image`** and **no `<img>` at all**, and no canonical URL.
Sharing either page — which is precisely what the outreach asks a recipient to
do — renders a blank grey placeholder instead of the product, and search engines
have nothing to attach the page to. The Gumroad listings fall back to Gumroad's
generic opengraph image for the same reason.

These cards are drawn from the same palette as the landing pages, so the card and
the page look like one thing. Deterministic and re-runnable:

    python3 scripts/make_share_art.py
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "og"
FONTS = pathlib.Path("/usr/share/fonts/truetype/dejavu")

BG, PANEL, LINE = (10, 11, 13), (17, 19, 22), (35, 39, 45)
INK, MUTED, DIM = (242, 244, 247), (148, 154, 164), (107, 114, 128)
BRAND, BAD, GOOD = (94, 234, 212), (248, 113, 113), (74, 222, 128)

W, H = 1200, 630
PAD = 64


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def pill(d, xy, text, f, fill, fg):
    x, y = xy
    w = d.textlength(text, font=f)
    h = f.size + 20
    d.rounded_rectangle([x, y, x + w + 36, y + h], radius=h // 2, fill=fill)
    d.text((x + 18, y + h // 2 + 1), text, font=f, fill=fg, anchor="lm")


def chip_rows(d, y, rows, f, max_x):
    """Outlined chips, laid out in explicit rows so nothing can wrap by accident."""
    for row in rows:
        x = PAD
        for text, colour in row:
            cw = d.textlength(text, font=f) + 48
            assert x + cw <= max_x, f"chip overflows the card: {text!r}"
            d.rounded_rectangle([x, y, x + cw, y + 40], radius=20,
                                outline=LINE, width=2)
            d.ellipse([x + 16, y + 16, x + 25, y + 25], fill=colour)
            d.text((x + 34, y + 21), text, font=f, fill=MUTED, anchor="lm")
            x += cw + 14
        y += 50
    return y - 10


def assert_not_clipped(path):
    """Structural proof the card is not cut off: the outer margins hold no ink."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    worst = 0
    for x0, y0, x1, y1, name in ((0, 12, 40, h - 12, "left"),
                                 (w - 40, 12, w, h - 12, "right"),
                                 (0, h - 14, w, h, "bottom")):
        for x in range(x0, x1, 3):
            for y in range(y0, y1, 3):
                r, g, b = px[x, y]
                worst = max(worst, max(r, g, b))
    assert worst < 90, (f"{name} margin of {path.name} holds bright pixels "
                        f"(max={worst}) - text is running off the card")
    return worst


def card(path, badge, title_lines, sub_lines, chips, price, price_colour,
         title_size=54):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for y in range(H):                                  # top-lit gradient
        t = y / H
        d.line([(0, y), (W, y)],
               fill=(int(BG[0] + 9 * (1 - t)), int(BG[1] + 10 * (1 - t)),
                     int(BG[2] + 12 * (1 - t))))
    d.rectangle([0, 0, W, 6], fill=price_colour)

    f_badge = font("DejaVuSans-Bold.ttf", 20)
    f_title = font("DejaVuSans-Bold.ttf", title_size)
    f_sub = font("DejaVuSans.ttf", 25)
    f_chip = font("DejaVuSans.ttf", 20)
    f_price = font("DejaVuSans-Bold.ttf", 29)

    pill(d, (PAD, 50), badge, f_badge, price_colour, BG)

    y = 122
    for line in title_lines:
        d.text((PAD, y), line, font=f_title, fill=INK)
        y += title_size + 12
    y += 10
    for line in sub_lines:
        d.text((PAD, y), line, font=f_sub, fill=MUTED)
        y += 36

    chip_rows(d, 372, chips, f_chip, W - PAD)
    d.text((PAD, H - 106), price, font=f_price, fill=price_colour)
    d.text((PAD, H - 58), "caseone115.github.io/claimgate", font=f_chip, fill=DIM)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG", optimize=True)
    return path


if __name__ == "__main__":
    made = [
        card(OUT / "claimgate-share-1200x630.png",
             "FOR AI-ASSISTED MARKETING COPY",
             ["Every claim must", "appear in your evidence"],
             ["ClaimGate checks a draft against your own sources, enforces your",
              "banned-claims policy and flags the AI disclosure EU Art.50 requires."],
             [[("unsupported figure  blocked", BAD),
               ("absolute claim  blocked", BAD)],
              [("claim substantiated  ok", GOOD),
               ("exit code 1 in CI", BRAND)]],
             "US$39 launch  ·  was US$149  ·  source is public and MIT", BRAND),
        card(OUT / "claimgate-kit-share-1200x630.png",
             "FREE  ·  PAY WHAT YOU WANT",
             ["The free front door:", "policy, evidence, gate"],
             ["Policy file, evidence folder, draft template, six-question",
              "checklist, and a CI job that gates every pull request."],
             [[("no API key", GOOD), ("no network", GOOD)],
              [("runs in your repo", GOOD), ("free forever", GOOD)]],
             "US$0  ·  suggested US$19  ·  no signup", GOOD),
    ]
    for p in made:
        worst = assert_not_clipped(p)
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024}KB  "
              f"{Image.open(p).size}  margins clean (max={worst})")
