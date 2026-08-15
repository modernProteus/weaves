#!/usr/bin/env python3
"""
Preview card for a static read under static/ — the pages make_cards.py doesn't
cover, because it only walks nodes/*.json.

	python3 tools/make_read_card.py            # write the card
	python3 tools/make_read_card.py --fonts    # just report what fonts it finds

Writes static/clear-conversations/talarico-corpus/card.png at 1200x630, which
the static/ passthrough copies to
/weaves/clear-conversations/talarico-corpus/card.png — the absolute URL the
og:image tag points at.

The card is the finding: sixty-one dots, one per message, in order. Sixty are
outbound. The single madder dot is the only reply the recipient ever sent.

Fonts resolve in this order, per role: tools/ttf → your installed user and
system fonts → a generic face of the right class. It never dies over a font;
it tells you what it used and carries on.
"""
import os, sys, glob
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF  = os.path.join(ROOT, "tools", "ttf")
OUT  = os.path.join(ROOT, "static", "clear-conversations", "talarico-corpus", "card.png")

W, H   = 1200, 630
SS     = 2
VAT    = (19, 26, 46)
LINEN  = (237, 230, 216)
MADDER = (190, 68, 56)
OCHRE  = (184, 146, 48)
WARP   = (29, 36, 55)
MUTED  = (142, 150, 174)

TOTAL, REPLY_AT = 61, 23

EYEBROW = "CLEAR CONVERSATIONS"
TITLE   = ["341 days inside", "a fundraising voice"]
META    = "60 OUT  ·  1 IN  ·  SEP 2025 — AUG 2026"
FOOT    = "One reply. It asked them to be meaningful."

# Where fonts live, most-specific first. tools/ttf wins so the repo is authoritative.
FONT_DIRS = [
	TTF,
	os.path.expanduser("~/Library/Fonts"),          # macOS, user-installed
	"/Library/Fonts",                                # macOS, machine-wide
	"/System/Library/Fonts/Supplemental",            # macOS, shipped
	"/System/Library/Fonts",
	"/usr/share/fonts",                              # linux
	os.path.expanduser("~/.local/share/fonts"),
	"C:/Windows/Fonts",                              # windows
]

# role -> (preferred names in order, generic fallbacks in order)
ROLES = {
	"display": (["fraunces", "playfair", "lora", "spectral", "eb garamond"],
				["georgia", "timesnewroman", "times", "dejavuserif", "liberationserif"]),
	"body":    (["karla", "inter", "worksans", "publicsans", "poppins"],
				["helvetica", "arial", "dejavusans", "liberationsans", "verdana"]),
	"mono":    (["spacemono", "space mono", "jetbrainsmono", "ibmplexmono", "robotomono"],
				["menlo", "consolas", "couriernew", "dejavusansmono", "liberationmono"]),
}

_index = None
def font_index():
	"""Every font file we can see, as (normalised_name, path), nearest dir first."""
	global _index
	if _index is None:
		_index, seen = [], set()
		for d in FONT_DIRS:
			if not d or not os.path.isdir(d):
				continue
			for path in sorted(glob.glob(os.path.join(d, "**", "*.*"), recursive=True)):
				if not path.lower().endswith((".ttf", ".otf", ".ttc")):
					continue
				if path in seen:
					continue
				seen.add(path)
				norm = os.path.basename(path).lower()
				for junk in ("-", "_", " ", "[", "]"):
					norm = norm.replace(junk, "")
				_index.append((norm, path))
	return _index


def resolve(role):
	preferred, generic = ROLES[role]
	idx = font_index()
	for group, kind in ((preferred, "brand"), (generic, "generic")):
		for want in group:
			key = want.replace(" ", "").replace("-", "")
			# prefer a regular/variable cut over italics and heavy weights
			hits = [p for n, p in idx if key in n]
			if hits:
				hits.sort(key=lambda p: (
					any(x in os.path.basename(p).lower() for x in ("italic", "oblique")),
					not any(x in os.path.basename(p).lower() for x in ("regular", "variable", "[")),
					len(os.path.basename(p)),
				))
				return hits[0], kind, want
	return None, None, None


def load(path, size):
	try:
		return ImageFont.truetype(path, size * SS)
	except Exception:
		return ImageFont.truetype(path, size * SS, index=0)


resolved = {}
print("  fonts")
for role in ("display", "body", "mono"):
	path, kind, matched = resolve(role)
	resolved[role] = path
	if path is None:
		print(f"    {role:8s} none found — falling back to PIL's built-in face")
	else:
		where = "tools/ttf" if path.startswith(TTF) else os.path.dirname(path)
		flag = " " if kind == "brand" else " (substitute — not brand-exact)"
		print(f"    {role:8s} {os.path.basename(path)}{flag}\n             from {where}")

if os.path.isdir(TTF):
	have = [f for f in sorted(os.listdir(TTF)) if f.lower().endswith((".ttf", ".otf", ".ttc"))]
	print(f"\n  tools/ttf contains: {', '.join(have) if have else '(no font files)'}")
else:
	print(f"\n  no tools/ttf directory at {TTF}")

if "--fonts" in sys.argv:
	sys.exit(0)


def f(role, size):
	p = resolved[role]
	return load(p, size) if p else ImageFont.load_default()


def tracked(d, xy, text, font, fill, track=0):
	x, y = xy
	for ch in text:
		d.text((x, y), ch, font=font, fill=fill)
		x += d.textlength(ch, font=font) + track
	return x


img = Image.new("RGB", (W * SS, H * SS), VAT)
d = ImageDraw.Draw(img)

M = 84 * SS
f_eyebrow, f_title = f("mono", 17), f("display", 66)
f_meta, f_foot     = f("mono", 16), f("body", 21)

sq = 13 * SS
d.rectangle([M, 76 * SS, M + sq, 76 * SS + sq], fill=OCHRE)
tracked(d, (M + sq + 15 * SS, 74 * SS), EYEBROW, f_eyebrow, OCHRE, track=2.4 * SS)

y = 132 * SS
for line in TITLE:
	d.text((M, y), line, font=f_title, fill=LINEN)
	y += 82 * SS

row_y = 412 * SS
span  = W * SS - 2 * M
pitch = span / (TOTAL - 1)
r_out, r_in = 4.6 * SS, 8.2 * SS

d.line([M, row_y, W * SS - M, row_y], fill=WARP, width=int(2 * SS))
for i in range(TOTAL):
	if i == REPLY_AT:
		continue
	cx = M + i * pitch
	d.ellipse([cx - r_out, row_y - r_out, cx + r_out, row_y + r_out], fill=(92, 102, 128))

cx = M + REPLY_AT * pitch
d.ellipse([cx - r_in - 5 * SS, row_y - r_in - 5 * SS, cx + r_in + 5 * SS, row_y + r_in + 5 * SS], fill=VAT)
d.ellipse([cx - r_in, row_y - r_in, cx + r_in, row_y + r_in], fill=MADDER)
d.line([cx, row_y + r_in + 7 * SS, cx, row_y + 30 * SS], fill=MADDER, width=int(2 * SS))

tracked(d, (M, row_y + 52 * SS), META, f_meta, MUTED, track=1.6 * SS)
d.text((M, H * SS - 92 * SS), FOOT, font=f_foot, fill=LINEN)
d.rectangle([0, H * SS - 7 * SS, W * SS, H * SS], fill=MADDER)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.resize((W, H), Image.LANCZOS).save(OUT, optimize=True)
print(f"\n  wrote {os.path.relpath(OUT, ROOT)}  {os.path.getsize(OUT) // 1024} KB  {W}x{H}")