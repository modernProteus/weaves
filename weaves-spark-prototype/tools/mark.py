"""
Proximity mark for Weaves preview cards.

Draws the doctrinal map behind a spark's title: concentric distance from the
President, with the three radii where different authorities have drawn the
privilege line, and advisers placed on both sides of them.

  dashed linen   the President and his direct advisers
  ochre          In re Sealed Case / Judicial Watch -- organisational proximity
  madder         the Aug 2026 OLC opinion -- subject matter and proximity only
  filled square  an adviser inside the ochre line
  hollow square  an adviser outside it
  dimmed square  outside even the madder line ("no matter how remote")

Marks are seeded by node id, so the same node draws the same mark forever.

Pillow only, no new dependencies. Arcs and ellipses in Pillow are aliased, so
everything is drawn at SS x scale and downsampled with LANCZOS at the end;
this is the whole reason for the supersampling and not an accident.

Compose with the card renderer:

    from mark import draw_proximity
    draw_proximity(img, (688, 92, 424, 446), node_id="olc-private-advisers-privilege")

Standalone proof (writes proof.png next to this file):

    python3 tools/mark.py
"""

import hashlib
import math

from PIL import Image, ImageDraw

# Weaves tokens
INDIGO = (0x13, 0x1A, 0x2E)
LINEN = (0xED, 0xE6, 0xD8)
MUTED = (0x8E, 0x96, 0xAE)
MADDER = (0xBE, 0x44, 0x38)
OCHRE = (0xB8, 0x92, 0x30)

SS = 4  # supersample factor


def _blend(fg, bg, alpha):
    """Pillow has no per-shape alpha on arc/ellipse, so pre-blend against the ground."""
    return tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))


def _dashed_circle(d, cx, cy, r, colour, width, dash_deg=7, gap_deg=6):
    box = (cx - r, cy - r, cx + r, cy + r)
    a = 0.0
    while a < 360:
        d.arc(box, a, min(a + dash_deg, 360), fill=colour, width=width)
        a += dash_deg + gap_deg


def _advisers(node_id, r_inner, r_outer, n=16):
    """Deterministic polar placement. Same id in, same field out, forever."""
    h = hashlib.sha256(node_id.encode()).digest()
    out = []
    for i in range(n):
        # golden-angle spiral keeps them from clumping, hash only perturbs it
        ang = (i * 2.399963) + (h[i % len(h)] / 255.0) * 0.55
        t = (i + 0.5) / n
        rad = r_inner + (r_outer - r_inner) * (t ** 0.82)
        rad += (h[(i * 3 + 7) % len(h)] / 255.0 - 0.5) * (r_outer - r_inner) * 0.10
        out.append((rad, ang))
    return out


def draw_proximity(img, box, node_id, ground=INDIGO):
    """
    img      an RGB Pillow image to draw onto
    box      (x, y, w, h) region for the mark; the mark is centred and square
    node_id  the node's id, used to seed adviser placement
    """
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    # Advisers sit beyond the madder ring, so hold back margin for them.
    # Without this they clip against the layer edge and lose their squares,
    # leaving orphan spokes pointing at nothing.
    R = min(w, h) / 2 * 0.86  # outermost (madder) radius

    r_pres = R * 0.30   # dashed linen: President + direct advisers
    r_espy = R * 0.585  # ochre: organisational proximity
    r_olc = R           # madder: the new outer bound

    layer = Image.new("RGB", (int(w * SS) + 2, int(h * SS) + 2), ground)
    d = ImageDraw.Draw(layer)
    ox, oy = (cx - x) * SS, (cy - y) * SS

    def circle(r, colour, width, dashed=False):
        rr = r * SS
        if dashed:
            _dashed_circle(d, ox, oy, rr, colour, max(1, round(width * SS)))
        else:
            d.ellipse((ox - rr, oy - rr, ox + rr, oy + rr),
                      outline=colour, width=max(1, round(width * SS)))

    # distance grid
    grid = _blend(MUTED, ground, 0.30)
    step = R / 11.0
    rr = step
    while rr < r_olc - step * 0.4:
        circle(rr, grid, 1)
        rr += step

    # advisers, drawn under the marked radii so the lines read on top
    spokes = _blend(LINEN, ground, 0.26)
    pts = _advisers(node_id, r_pres * 0.62, r_olc * 1.13)
    marks = []
    for rad, ang in pts:
        px, py = ox + rad * SS * math.cos(ang), oy + rad * SS * math.sin(ang)
        d.line((ox, oy, px, py), fill=spokes, width=max(1, round(0.9 * SS)))
        marks.append((px, py, rad))

    circle(r_pres, LINEN, 2.2, dashed=True)
    circle(r_espy, OCHRE, 2.6)
    circle(r_olc, MADDER, 2.8)

    s = 4.6 * SS
    for px, py, rad in marks:
        sq = (px - s, py - s, px + s, py + s)
        if rad <= r_espy:
            d.rectangle(sq, fill=OCHRE)
        elif rad <= r_olc:
            d.rectangle(sq, outline=LINEN, width=max(1, round(1.7 * SS)))
        else:  # beyond even the OLC line
            d.rectangle(sq, outline=_blend(MUTED, ground, 0.55),
                        width=max(1, round(1.6 * SS)))

    # the President
    pr = 6.4 * SS
    d.ellipse((ox - pr, oy - pr, ox + pr, oy + pr), fill=MADDER)

    layer = layer.resize((int(w), int(h)), Image.LANCZOS)
    img.paste(layer, (int(x), int(y)))
    return img


def paste_glyph(img, glyph_path, x, y, height):
    """
    Composite the spark glyph into the label lockup and return the width it
    occupied, so the caller can set the label's x from it rather than hardcode.

    The glyph is a keyed still from pagespark.mp4 (the ignition frame) with the
    ground removed, so it composites onto any background. Scaled from its own
    aspect; pass height only.
    """
    g = Image.open(glyph_path).convert("RGBA")
    w = max(1, round(g.width * height / g.height))
    g = g.resize((w, max(1, round(height))), Image.LANCZOS)
    img.paste(g, (round(x), round(y)), g)
    return w


if __name__ == "__main__":
    import os
    from PIL import ImageFont

    HERE = os.path.dirname(os.path.abspath(__file__))
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), INDIGO)
    draw_proximity(img, (688, 92, 424, 446), "olc-private-advisers-privilege")

    # Text here is only so the proof reads as a card. The real card renderer
    # already owns fonts and layout; this block is not the deliverable.
    d = ImageDraw.Draw(img)

    def font(names, size):
        for n in names:
            for root in ("/usr/share/fonts/truetype/google-fonts/",
                         "/usr/share/fonts/truetype/dejavu/",
                         "/usr/share/fonts/truetype/liberation/"):
                p = os.path.join(root, n)
                if os.path.exists(p):
                    return ImageFont.truetype(p, size)
        return ImageFont.load_default(size)

    disp = font(["Fraunces-SemiBold.ttf", "DejaVuSerif-Bold.ttf"], 46)
    mono = font(["SpaceMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"], 16)
    meta = font(["SpaceMono-Regular.ttf", "DejaVuSansMono.ttf"], 17)

    gw = paste_glyph(img, os.path.join(HERE, "assets", "spark-glyph.png"),
                     80, 74, 62)
    lx = 80 + gw + 20
    d.text((lx, 98), "S P A R K", font=mono, fill=OCHRE)
    d.rectangle((lx, 128, lx + 34, 131), fill=OCHRE)
    d.text((80, 250), "Executive privilege", font=disp, fill=LINEN)
    d.text((80, 306), "for private citizens", font=disp, fill=LINEN)
    d.rectangle((80, 418, 580, 419), fill=_blend(MUTED, INDIGO, 0.45))
    d.text((80, 446), "from nick  ·  essay  ·  ~9 min", font=meta,
           fill=_blend(MUTED, INDIGO, 0.9))

    out = os.path.join(HERE, "proof.png")
    img.save(out, optimize=True)
    print(f"wrote {out}  {img.size}  {os.path.getsize(out)} bytes")
