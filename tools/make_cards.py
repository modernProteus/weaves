#!/usr/bin/env python3
"""
Generates one preview card per node: assets/plate.png composited on the left,
title and question set on the right. Run from the repo root.

    python3 tools/make_cards.py

Reads nodes/*.json, writes dist/n/<id>/card.png. Skips drafts.
Needs Pillow and the TTFs in tools/ttf/.
"""

import json, glob, os, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF  = os.path.join(ROOT, "tools", "ttf")

W, H  = 1200, 630
SS    = 2                     # supersample then downsample

VAT    = (19, 26, 46)
LINEN  = (237, 230, 216)
MADDER = (190, 68, 56)
OCHRE  = (184, 146, 48)
WARP   = (29, 36, 55)

# Static card: drawing and text share the frame more evenly.
PLATE_H   = 470
TEXT_X    = 500
TEXT_W    = W - TEXT_X - 56

# Video card: no title, so the drawing gives up room to the question. Keep these
# in step with the crop and overlay in tools/make_videos.sh.
PLATE_H_V = 380
PLATE_Y_V = (630 - PLATE_H_V) // 2
TEXT_X_V  = 372
TEXT_W_V  = W - TEXT_X_V - 44


def font(name, size):
    return ImageFont.truetype(os.path.join(TTF, name + ".ttf"), size * SS)


def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= width * SS:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines


def block(draw, lines, f, lead):
    """Real ink extents of a set of lines, measured rather than estimated.
    Fraunces overhangs its nominal line box, so nominal maths clips."""
    tops, bots, widest = [], [], 0
    for i, l in enumerate(lines):
        x0, y0, x1, y1 = draw.textbbox((0, i * lead), l, font=f)
        tops.append(y0); bots.append(y1); widest = max(widest, x1 - x0)
    return min(tops), max(bots), widest


def fit(draw, text, face, box_w, box_h, hi, lo):
    """Largest size at which the text actually fits the box. Short hooks get big
    type; long ones step down only as far as they must. Returns the font, the
    wrapped lines, the leading, and the offset that puts ink at the box top."""
    for size in range(hi, lo - 1, -2):
        f = font(face, size)
        lead = size * SS * 1.26
        lines = wrap(draw, text, f, box_w)
        top, bot, widest = block(draw, lines, f, lead)
        if widest <= box_w * SS and (bot - top) <= box_h * SS:
            return f, lines, lead, top, bot - top
    f = font(face, lo)
    lead = lo * SS * 1.26
    lines = wrap(draw, text, f, box_w)
    top, bot, _ = block(draw, lines, f, lead)
    return f, lines, lead, top, bot - top


ITALIC = "fraunces-latin-400-italic"
BOLD   = "fraunces-latin-600-normal"

TOP, BOT = 74, 496          # text area, above the mode badge at 522


def card(node, plate, draw_plate=True, show_title=True):
    img = Image.new("RGB", (W * SS, H * SS), VAT)
    d = ImageDraw.Draw(img)

    for x in range(0, W, 48):
        d.line([(x * SS, 0), (x * SS, H * SS)], fill=WARP, width=1 * SS)

    # the drawing, left. omitted for the video base, where the animation goes here.
    tx, tw = (TEXT_X, TEXT_W) if show_title else (TEXT_X_V, TEXT_W_V)

    if draw_plate:
        p = plate.copy()
        scale = (PLATE_H * SS) / p.height
        p = p.resize((int(p.width * scale), int(p.height * scale)), Image.LANCZOS)
        img.paste(p, (44 * SS, int((H * SS - p.height) / 2)), p)

    hook = node.get("hook") or node.get("action") or node.get("question") or ""

    if show_title:
        ft, tl, tlead, ttop, th = fit(d, node.get("title", ""), BOLD, tw, 150, 58, 30)
        fh, hl, hlead, htop, hh = fit(d, hook, ITALIC, tw, BOT - TOP - 150 - 26, 46, 20)
        gap = 26 * SS
        y = TOP * SS + max(0, ((BOT - TOP) * SS - (th + gap + hh)) / 2)
        d_y = y - ttop
        for i, line in enumerate(tl):
            d.text((tx * SS, d_y + i * tlead), line, font=ft, fill=LINEN)
        y += th + gap
    else:
        # No title on the video card: iMessage prints it below and drops the
        # description, so the question gets the whole box and every point of size
        # it can take. Two lines land near 90px; six step down to fit.
        fh, hl, hlead, htop, hh = fit(d, hook, ITALIC, tw, BOT - TOP, 108, 24)
        y = TOP * SS + max(0, ((BOT - TOP) * SS - hh) / 2)

    d_y = y - htop
    for i, line in enumerate(hl):
        d.text((tx * SS, d_y + i * hlead), line, font=fh, fill=MADDER)

    fm = font("space-mono-latin-400-normal", 15)
    kind = node.get("kind", "thread")
    if kind != "thread":
        label = kind.upper()
    elif not node.get("lit"):
        label = "SPARK"
    elif len(node.get("reads", [])) > 1:
        label = "BROADEN"
    else:
        label = "THREAD"
    x = tx * SS
    for ch in label:
        d.text((x, 522 * SS), ch, font=fm, fill=OCHRE)
        x += d.textlength(ch, font=fm) + 5 * SS

    return img.resize((W, H), Image.LANCZOS)


def main():
    plate_path = os.path.join(ROOT, "assets", "plate.png")
    if not os.path.exists(plate_path):
        print("no assets/plate.png — skipping card generation")
        return

    missing = [f for f in ("fraunces-latin-600-normal", "fraunces-latin-400-italic",
                           "space-mono-latin-400-normal")
               if not os.path.exists(os.path.join(TTF, f + ".ttf"))]
    if missing:
        sys.exit("missing fonts in tools/ttf/: " + ", ".join(missing))

    if not os.path.isdir(os.path.join(ROOT, "dist")):
        sys.exit("no dist/ — run `node build.mjs` first, it wipes dist/ before writing")
    plate = Image.open(plate_path).convert("RGBA")

    made = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "nodes", "*.json"))):
        node = json.load(open(f))
        if node.get("status") == "draft":
            continue
        nid = node.get("id") or os.path.basename(f)[:-5]
        out = os.path.join(ROOT, "dist", "n", nid)
        os.makedirs(out, exist_ok=True)
        card(node, plate).save(os.path.join(out, "card.png"), optimize=True)
        # base plate for the animated card: same layout, drawing left out
        if os.environ.get("CQ_VIDEO_CARDS"):
            card(node, plate, draw_plate=False, show_title=False).save(os.path.join(out, "_base.png"))
        made += 1
        print(f"  card: {nid}")
    print(f"generated {made} card(s)")


if __name__ == "__main__":
    main()
