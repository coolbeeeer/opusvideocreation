#!/usr/bin/env bash
# Dev helper: copy the shared kits into assets/, rebuild the skeleton, snapshot the given film times and tile them.
#   ./dev.sh 1.0,2.5,4.0 hook-v1      -> PNGs in .snaps/hook-v1, contact sheet in review/hook-v1.jpg
# Needs HYPERFRAMES_FFMPEG_PATH / HYPERFRAMES_FFPROBE_PATH when FFmpeg is not on a system path (docs/01-environment.md).
set -euo pipefail
cd "$(dirname "$0")"
cp ../../lib/kit.js ../../lib/kit-plus.js ../../lib/kit-ocean.js assets/
python build.py > /dev/null
name=$(basename "${2:-snap}")
rm -rf ".snaps/$name"
HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.9.56 snapshot --at "$1" --no-end -o ".snaps/$name" 2>&1 | grep -E "saved|rror" || true
n=$(ls .snaps/"$name"/frame-*.png | wc -l)
cols=$(( n < 6 ? n : 6 )); rows=$(( (n + cols - 1) / cols ))
mkdir -p review
"${HYPERFRAMES_FFMPEG_PATH:-ffmpeg}" -v error -y -pattern_type glob -i ".snaps/$name/frame-*.png" \
  -vf "scale=300:-1,tile=${cols}x${rows}:padding=4:color=0x202020" -frames:v 1 "review/$name.jpg"
echo "review/$name.jpg ($n frames)"
