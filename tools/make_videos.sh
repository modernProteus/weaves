#!/usr/bin/env bash
# Animated preview cards: the spark animation composited into the left of each
# node's card, title and question already set on the right.
#
# Needs assets/page-spark.mp4 and dist/n/<id>/_base.png (from make_cards.py with
# CQ_VIDEO_CARDS=1). ffmpeg is preinstalled on GitHub's ubuntu runners.
#
#   CQ_VIDEO_CARDS=1 python3 tools/make_cards.py && bash tools/make_videos.sh
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=assets/page-spark.mp4
[ -f "$SRC" ] || { echo "no $SRC — skipping animated cards"; exit 0; }

# tight crop around the drawing, scaled to the same box the static card uses
CROP="crop=672:885:264:158,scale=-1:470"

n=0
for base in dist/n/*/_base.png; do
  [ -e "$base" ] || continue
  dir=$(dirname "$base")
  ffmpeg -v error -loop 1 -i "$base" -i "$SRC" \
    -filter_complex "[1:v]${CROP}[a];[0:v][a]overlay=44:80:shortest=1,format=yuv420p" \
    -c:v libx264 -profile:v baseline -level 3.1 -an -movflags +faststart \
    -crf 28 -shortest "$dir/card.mp4" -y
  rm -f "$base"
  echo "  video: $(basename "$dir")  $(( $(stat -c%s "$dir/card.mp4") / 1024 )) KB"
  n=$((n+1))
done
echo "generated $n animated card(s)"
