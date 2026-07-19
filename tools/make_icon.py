# Regenerates assets/card.png — the shared preview icon.
#
# A single thread, pulled loose, coiling inward around a question. One stroke,
# thick where it's slack and narrowing as it draws in. The centre dot is madder,
# the same colour the bookshelf mark uses on the site.
#
# Square on purpose: shape decides the card layout. A square renders as the
# compact form (icon left, title and question right, text as the focus). Make it
# wide and clients switch to the big banner instead. build.mjs reads the PNG
# header and sets the tags to match, so changing the shape here is enough.
#
# Run from the repo root:  python3 tools/make_icon.py
#
# Tunable: TURNS (how many coils), r1 (outer radius), the width curve in the
# draw loop, and cx/cy to shift the composition.

import math
from PIL import Image, ImageDraw

SS = 4
S = 640
s = S * SS

VAT    = (19, 26, 46)
OCHRE  = (184, 146, 48)
MADDER = (190, 68, 56)
WARP   = (29, 36, 55)

img = Image.new("RGB", (s, s), VAT)
d = ImageDraw.Draw(img)

for x in range(0, S, 40):
    d.line([(x * SS, 0), (x * SS, s)], fill=WARP, width=1 * SS)

cx, cy = S * 0.53, S * 0.47

# A single thread, pulled loose, coiling inward. One stroke.
# Wide where it's slack, narrowing as it draws in.

pts = []
TURNS = 2.6
STEPS = 900
r0, r1 = 14.0, 196.0

for i in range(STEPS + 1):
    t = i / STEPS
    th = t * TURNS * 2 * math.pi
    r = r0 + (r1 - r0) * (t ** 1.35)
    pts.append((cx + r * math.cos(th - math.pi * 0.55),
                cy + r * math.sin(th - math.pi * 0.55)))

# let the loose end relax out of the coil rather than stopping dead
ax, ay = pts[-1]
bx, by = pts[-14]
dx, dy = ax - bx, ay - by
n = math.hypot(dx, dy) or 1
for k in range(1, 130):
    e = k / 130
    pts.append((ax + dx / n * k * 0.9,
                ay + dy / n * k * 0.9 * (1 - e * 0.72)))

for i in range(len(pts) - 1):
    t = i / (len(pts) - 1)
    w = 3.0 + 8.0 * (t ** 1.15)
    d.line([(pts[i][0] * SS, pts[i][1] * SS),
            (pts[i + 1][0] * SS, pts[i + 1][1] * SS)],
           fill=OCHRE, width=max(1, int(w * SS)))

# the centre: the question the thread coils around
d.ellipse([((cx - 9) * SS, (cy - 9) * SS), ((cx + 9) * SS, (cy + 9) * SS)],
          fill=MADDER)

img.resize((S, S), Image.LANCZOS).save("assets/card.png", optimize=True)
print("icon.png written")
