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

PLATE_H   = 470               # drawing height, of 630
TEXT_X    = 500               # where the text column starts
TEXT_W    = W - TEXT_X - 56


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


def card(node, plate):
    img = Image.new("RGB", (W * SS, H * SS), VAT)
    d = ImageDraw.Draw(img)

    for x in range(0, W, 48):
        d.line([(x * SS, 0), (x * SS, H * SS)], fill=WARP, width=1 * SS)

    # the drawing, left, bled slightly off the bottom so it frames rather than sits
    p = plate.copy()
    scale = (PLATE_H * SS) / p.height
    p = p.resize((int(p.width * scale), int(p.height * scale)), Image.LANCZOS)
    img.paste(p, (44 * SS, int((H * SS - p.height) / 2)), p)

    y = 200

    title = node.get("title", "")
    ft = font("fraunces-latin-600-normal", 54)
    tl = wrap(d, title, ft, TEXT_W)
    if len(tl) > 2:                                  # long titles step down a size
        ft = font("fraunces-latin-600-normal", 44)
        tl = wrap(d, title, ft, TEXT_W)
    for line in tl:
        d.text((TEXT_X * SS, y * SS), line, font=ft, fill=LINEN)
        y += 62 if ft.size == 54 * SS else 52

    y += 22

    hook = node.get("hook") or node.get("action") or node.get("question") or ""
    fh = font("fraunces-latin-400-italic", 34)
    hl = wrap(d, hook, fh, TEXT_W)
    if len(hl) > 4:
        fh = font("fraunces-latin-400-italic", 29)
        hl = wrap(d, hook, fh, TEXT_W)
    for line in hl[:5]:
        d.text((TEXT_X * SS, y * SS), line, font=fh, fill=MADDER)
        y += 46 if fh.size == 34 * SS else 40

    fm = font("space-mono-latin-400-normal", 15)
    label = {"thread": "THREAD", "workbench": "WORKBENCH", "bookshelf": "BOOKSHELF"} \
        .get(node.get("kind", "thread"), "THREAD")
    if len(node.get("reads", [])) > 1:
        label = "BROADEN"
    x = TEXT_X * SS
    for ch in label:
        d.text((x, 522 * SS), ch, font=fm, fill=OCHRE)
        x += d.textlength(ch, font=fm) + 5 * SS

    return img.resize((W, H), Image.LANCZOS)


def main():
    plate_path = os.path.join(ROOT, "assets", "plate.png")
    if not os.path.exists(plate_path):
        print("no assets/plate.png — skipping card generation")
        return
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
        made += 1
        print(f"  card: {nid}")
    print(f"generated {made} card(s)")


if __name__ == "__main__":
    main()
