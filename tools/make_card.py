# Regenerates assets/card.png — the shared OG image for every node.
#
# The glyph is this system's own lineage notation at scale: one thread placed
# in ochre, then a hollow workbench square and a hollow bookshelf circle,
# neither taken yet. Same marks as the spine on every page.
#
# Fonts: Space Mono, fetched from npm and converted, since Google Fonts isn't
# reachable from every build environment.
#
#   npm pack @fontsource/space-mono
#   tar xzf fontsource-space-mono-*.tgz --strip-components=1 -C fonts
#   pip install fonttools brotli
#   python3 -c "from fontTools.ttLib import TTFont; \
#     [TTFont(f'fonts/files/space-mono-latin-{w}-normal.woff2').save( \
#      f'ttf/space-mono-latin-{w}-normal.ttf') for w in (400, 700)]"
#
# Then: python3 tools/make_card.py   (run from the repo root)

from PIL import Image, ImageDraw, ImageFont

SS = 4                      # supersample, then downsample for clean edges
W, H = 1200, 630
w, h = W * SS, H * SS

VAT    = (19, 26, 46)
LINEN  = (237, 230, 216)
DIM    = (142, 150, 174)
MADDER = (190, 68, 56)
OCHRE  = (184, 146, 48)
WARP   = (29, 36, 55)       # faint threads on the ground
LINK   = (78, 86, 108)

img = Image.new("RGB", (w, h), VAT)
d = ImageDraw.Draw(img)

# ── ground: warp under tension ────────────────────────────────
for x in range(0, W, 48):
    d.line([(x * SS, 0), (x * SS, h)], fill=WARP, width=1 * SS)

# ── the glyph: this system's own lineage notation ─────────────
# one thread placed, two possible continuations, neither taken yet.

cx, cy = 372, 272
fork    = (600, 272)
up      = (828, 142)
down    = (828, 402)

S = lambda p: (p[0] * SS, p[1] * SS)

# links
d.line([S((cx + 46, cy)), S(fork)], fill=LINK, width=4 * SS)
d.line([S(fork), S((up[0] - 42, up[1]))], fill=LINK, width=4 * SS)
d.line([S(fork), S((down[0] - 42, down[1]))], fill=LINK, width=4 * SS)

# thread — placed
r = 45
d.rectangle([S((cx - r, cy - r)), S((cx + r, cy + r))], fill=OCHRE)

# workbench — square, hollow, not yet
r = 41
d.rectangle([S((up[0] - r, up[1] - r)), S((up[0] + r, up[1] + r))],
            outline=LINEN, width=5 * SS)

# bookshelf — circle, hollow, not yet
d.ellipse([S((down[0] - r, down[1] - r)), S((down[0] + r, down[1] + r))],
          outline=MADDER, width=5 * SS)

# ── wordmark ──────────────────────────────────────────────────
mono = ImageFont.truetype("tools/ttf/space-mono-latin-700-normal.ttf", 38 * SS)

def tracked(draw, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track * SS
    return x

label = "WEAVES"
width = sum(d.textlength(c, font=mono) for c in label) + 16 * SS * (len(label) - 1)
tracked(d, ((w - width) / 2, 486 * SS), label, mono, OCHRE, 16)

small = ImageFont.truetype("tools/ttf/space-mono-latin-400-normal.ttf", 20 * SS)
sub = "SPARK · THREAD · WORKBENCH · BOOKSHELF"
sw = sum(d.textlength(c, font=small) for c in sub) + 5 * SS * (len(sub) - 1)
tracked(d, ((w - sw) / 2, 552 * SS), sub, small, DIM, 5)

img.resize((W, H), Image.LANCZOS).save("assets/card.png", optimize=True)
print("card.png written")
