#!/usr/bin/env sh
# Copyright (c) 2026 Muhammad Hassan. MIT License.
# Re-render demo/x-agent-skill.gif with VHS (https://github.com/charmbracelet/vhs).
# Needs: vhs, ttyd and ffmpeg on PATH, and Python 3.9+. Run from anywhere; it cd's to the repo root.
#   sh demo/render.sh                 uses python3 (set PY=python on Windows)
#   PY=python sh demo/render.sh
set -eu
cd "$(dirname "$0")/.."
PY="${PY:-python3}"
command -v vhs >/dev/null 2>&1 || { echo "vhs not found. Install: https://github.com/charmbracelet/vhs#installation" >&2; exit 1; }
tmp="$(mktemp "${TMPDIR:-/tmp}/x-agent-skill.XXXXXX.tape")"
trap 'rm -f "$tmp"' EXIT
sed "s/__PY__/$PY/g" demo/x-agent-skill.tape > "$tmp"
vhs "$tmp"
size=$(wc -c < demo/x-agent-skill.gif)
echo "wrote demo/x-agent-skill.gif ($size bytes)"
[ "$size" -lt 3145728 ] || { echo "WARNING: GIF is over 3 MB" >&2; exit 2; }
