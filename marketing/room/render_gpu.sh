#!/usr/bin/env bash
# FLOAT / Room: full-quality render on a rented NVIDIA GPU box (e.g. RunPod RTX 4090).
#
#   git clone -b claude/practical-johnson-6qm853 https://github.com/KyleJKistner/blimpy.git
#   cd blimpy/marketing/room
#   bash render_gpu.sh            # 16:9 and 4:5, render + finish + master
#   bash render_gpu.sh wide       # one format only
#   SHARD=0/2 bash render_gpu.sh  # split frames across machines (0/2 and 1/2), then
#                                 # copy all renders/<fmt>/final/*.png to one box and
#                                 # rerun with RENDER=0 to finish and master.
#
# Downloads Blender 4.5 LTS and the Inter font family (SIL OFL) into ./.cache;
# nothing is installed system-wide except ffmpeg via apt when it is missing.
set -euo pipefail
cd "$(dirname "$0")"
FORMATS=${1:-both}
SHARD=${SHARD:-0/1}
RENDER=${RENDER:-1}
CACHE="$PWD/.cache"
mkdir -p "$CACHE"

if ! command -v ffmpeg >/dev/null; then
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg
fi
# Blender's bundled libraries cover Cycles; these X/GL libs let it start headless.
if command -v apt-get >/dev/null; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libxi6 libxkbcommon0 libsm6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libegl1 >/dev/null || true
fi

BLENDER_DIR="$CACHE/blender-4.5.14-linux-x64"
if [ ! -x "$BLENDER_DIR/blender" ]; then
  curl -fsSL https://download.blender.org/release/Blender4.5/blender-4.5.14-linux-x64.tar.xz | tar xJ -C "$CACHE"
fi
BLENDER="$BLENDER_DIR/blender"

if [ -z "${FLOAT_FONT_DIR:-}" ]; then
  if ! ls "$CACHE"/fonts/InterDisplay-SemiBold.otf >/dev/null 2>&1; then
    mkdir -p "$CACHE/fonts" && curl -fsSL -o "$CACHE/inter.zip" https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip
    python3 - "$CACHE" <<'EOF'
import sys, zipfile, pathlib
cache = pathlib.Path(sys.argv[1])
with zipfile.ZipFile(cache / 'inter.zip') as z:
    for n in z.namelist():
        if n.endswith('.otf') and '/InterDisplay-' in n and 'Italic' not in n:
            (cache / 'fonts' / pathlib.Path(n).name).write_bytes(z.read(n))
EOF
  fi
  export FLOAT_FONT_DIR="$CACHE/fonts"
fi

if [ ! -x "$CACHE/venv/bin/python" ]; then
  python3 -m venv "$CACHE/venv"
  "$CACHE/venv/bin/pip" install -q -r source/requirements.txt
fi
PY="$CACHE/venv/bin/python"

"$PY" source/textures.py
"$PY" source/score.py

case "$FORMATS" in both) LIST="wide feed" ;; *) LIST="$FORMATS" ;; esac
for FMT in $LIST; do
  if [ "$RENDER" = "1" ]; then
    "$BLENDER" -b -noaudio --python source/render.py -- --quality final --format "$FMT" --gpu --shard "$SHARD" \
      2>&1 | grep --line-buffered -E "RENDERED|Cycles device|Error|rror:" || true
    "$BLENDER" -b -noaudio --python source/render.py -- --quality final --format "$FMT" --track-only >/dev/null 2>&1
  fi
  if [ "$SHARD" = "0/1" ] || [ "$RENDER" = "0" ]; then
    missing=$(for f in $(seq 0 719); do [ -f "renders/$FMT/final/f_$(printf %04d "$f").png" ] || echo "$f"; done | wc -l)
    if [ "$missing" != "0" ]; then echo "$FMT: $missing frames missing; not finishing." >&2; continue; fi
    "$PY" source/finish.py --format "$FMT" --quality final
    "$PY" source/master.py --format "$FMT" --quality final
  fi
done
ls -la deliverables/
