#!/usr/bin/env bash
# Why does the preview look wrong? Run this and read.
#   bash tools/doctor.sh
set -uo pipefail
cd "$(dirname "$0")/.."

say() { printf "%-34s %s\n" "$1" "$2"; }
yn()  { [ "$1" = 0 ] && echo "no" || echo "yes"; }

echo "── config ─────────────────────────────────────────"
node -e '
const c = require("./weaves.config.json");
const p = (k,v) => console.log(k.padEnd(34) + v);
p("baseUrl", c.baseUrl);
p("repo", c.repo);
p("videoCards", String(!!c.videoCards));
const who = Object.entries(c.people||{}).map(([k,v]) =>
  k + ":" + ((typeof v === "object" && v.contact) ? "set" : "EMPTY"));
p("contacts", who.join("  "));
if (/YOURNAME/.test(c.baseUrl + c.repo)) console.log("\n  !! placeholder URLs still in config");
'

echo
echo "── assets ─────────────────────────────────────────"
for f in plate.png card.png page-spark.mp4 spark.mp4 spark-poster.png; do
  [ -f "assets/$f" ] && say "assets/$f" "present" || say "assets/$f" "-"
done
[ -f assets/spark.mp4 ] && [ -f assets/plate.png ] && \
  echo "  !! assets/spark.mp4 is ignored while per-node cards are on; delete it"

echo
echo "── code version ───────────────────────────────────"
say "build.mjs has ogVideo()"      "$(yn $(grep -c 'function ogVideo' build.mjs))"
say "build.mjs has per-node cards" "$(yn $(grep -c 'function ogImage' build.mjs))"
say "make_cards.py is lit-aware"   "$(yn $(grep -c 'until it.s lit' tools/make_cards.py))"
say "make_videos.sh present"       "$(yn $([ -f tools/make_videos.sh ] && echo 1 || echo 0))"
say "workflow runs make_videos"    "$(yn $(grep -c 'make_videos' .github/workflows/pages.yml))"
say "workflow sets CQ_VIDEO_CARDS" "$(yn $(grep -c 'CQ_VIDEO_CARDS' .github/workflows/pages.yml))"

echo
echo "── what the build actually emits ──────────────────"
node build.mjs >/dev/null 2>&1
for d in dist/n/*/; do
  id=$(basename "$d")
  img=$(grep -o 'og:image" content="[^"]*"' "$d/index.html" | sed 's/.*content="//;s/"//' | sed 's|.*/weaves||')
  vid=$(grep -o 'og:video" content="[^"]*"' "$d/index.html" | sed 's/.*content="//;s/"//' | sed 's|.*/weaves||')
  printf "  %-22s img %-34s vid %s\n" "$id" "${img:--}" "${vid:--none}"
done
