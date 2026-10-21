#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""render_fallback.py - render demo/x-agent-skill.gif WITHOUT VHS, from the tape's own commands.

Use this only when VHS cannot run (it hung on Windows with a current Chrome when this GIF was made).
It reads the visible `Type "..."` commands from x-agent-skill.tape, RUNS them for real in the repo root
(through bash), and draws the typed commands and their actual output as a dark terminal animation at
1200px wide. Nothing is typed in by hand, so the GIF still shows real tool output. It is a drawing of a
terminal, not a screen recording; `make demo` (VHS) is the canonical way to render.

Needs Pillow (`pip install pillow`) and bash. Run from anywhere:
  python demo/render_fallback.py
  python demo/render_fallback.py --font /path/to/Mono.ttf --py python3
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1200, 800
PAD, TOP = 28, 56
BG, BAR, FG, DIM = (14, 15, 18), (24, 26, 31), (222, 226, 233), (140, 148, 160)
GREEN, RED, YELLOW, ACC = (120, 230, 180), (244, 124, 124), (246, 193, 119), (255, 106, 61)
FONTS = ["C:/Windows/Fonts/consola.ttf", "/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
MAX_BYTES = 3 * 1024 * 1024


def commands(tape: str, py: str) -> List[Tuple[str, bool]]:
    """Visible commands from the tape, each with whether the screen was cleared (hidden `clear`) before it."""
    out: List[Tuple[str, bool]] = []
    hidden, clear = False, True
    for line in tape.splitlines():
        s = line.strip()
        if s == "Hide":
            hidden = True
        elif s == "Show":
            hidden = False
        elif s.startswith('Type "clear"') and hidden:
            clear = True
        elif s.startswith("Type ") and not hidden:
            m = re.match(r'Type "(.*?)"(?:\s+Sleep\s+\S+\s+Enter)?\s*$', s)
            if m:
                out.append((m.group(1).replace("__PY__", py), clear))
                clear = False
    return out


def run(cmd: str) -> str:
    bash = shutil.which("bash")
    if not bash:
        raise SystemExit("render_fallback: bash not found")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([bash, "-c", cmd], cwd=ROOT, capture_output=True, env=env)
    return (p.stdout + p.stderr).decode("utf-8", "replace").replace("\r", "").rstrip("\n")


def color_for(token: str):
    if token in ("STRONG", "PASS", "ok", "pass", "FITS"):
        return GREEN
    if token in ("WEAK", "FLAGGED", "FAIL", "BLOCKING:", "MISS", "BLOCKED"):
        return RED
    if token in ("REVIEW", "weak"):
        return YELLOW
    return None


def draw_line(d: ImageDraw.ImageDraw, x: int, y: int, text: str, font, cw: int) -> None:
    pos = 0
    for part in re.split(r"(\s+)", text):
        c = color_for(part.strip()) if part.strip() else None
        d.text((x + pos * cw, y), part, font=font, fill=c or FG)
        pos += len(part)


def frame(lines: List[Tuple[str, bool]], font, cw: int, lh: int, cursor: bool = False) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 40], fill=BAR)
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse([18 + i * 24, 14, 30 + i * 24, 26], fill=c)
    y = TOP
    for text, is_cmd in lines[-((H - TOP - 10) // lh):]:
        if is_cmd:
            d.text((PAD, y), "$", font=font, fill=GREEN)
            d.text((PAD + 2 * cw, y), text, font=font, fill=FG)
        else:
            draw_line(d, PAD, y, text, font, cw)
        y += lh
    if cursor:
        d.rectangle([PAD + 2 * cw + len(lines[-1][0]) * cw, y - lh + 3, PAD + 3 * cw + len(lines[-1][0]) * cw, y - 3], fill=FG)
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render the demo GIF without VHS, from the tape's real commands.")
    ap.add_argument("--tape", default=os.path.join(HERE, "x-agent-skill.tape"))
    ap.add_argument("--out", default=os.path.join(HERE, "x-agent-skill.gif"))
    ap.add_argument("--py", default="python", help="python command used in the commands")
    ap.add_argument("--font")
    a = ap.parse_args(argv)
    fp = next((p for p in ([a.font] if a.font else []) + FONTS if p and os.path.exists(p)), None)
    if not fp:
        raise SystemExit("render_fallback: no monospace font found; pass --font")
    font = ImageFont.truetype(fp, 20)
    cw = round(font.getlength("M"))
    lh = 28
    cmds = commands(open(a.tape, encoding="utf-8").read(), a.py)
    if not cmds:
        raise SystemExit("render_fallback: no commands found in the tape")
    frames: List[Image.Image] = []
    durs: List[int] = []

    def add(img: Image.Image, ms: int) -> None:
        frames.append(img)
        durs.append(ms)

    shown: List[Tuple[str, bool]] = []
    cols = (W - 2 * PAD) // cw - 2
    for cmd, clear in cmds:
        if clear:
            shown = []
        base = list(shown)
        for k in range(0, len(cmd) + 1, 4):
            add(frame(base + [(cmd[:k], True)], font, cw, lh, cursor=True), 70)
        add(frame(base + [(cmd, True)], font, cw, lh), 350)
        out = run(cmd)
        lines = []
        for raw in (out.split("\n") if out else []):
            indent = " " * (len(raw) - len(raw.lstrip()) + 2)
            while len(raw) > cols:
                cut = raw.rfind(" ", 0, cols)
                cut = cut if cut > cols // 2 else cols
                lines.append(raw[:cut])
                raw = indent + raw[cut:].lstrip()
            lines.append(raw)
        shown = base + [(cmd, True)]
        for j in range(0, len(lines), 3):
            chunk = [(ln, False) for ln in lines[j:j + 3]]
            shown = shown + chunk
            add(frame(shown, font, cw, lh), 90)
        durs[-1] = 3800
    # One shared palette keeps the file small and the colours stable.
    pal = frames[len(frames) // 2].quantize(colors=48, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(a.out, save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True, disposal=1)
    size = os.path.getsize(a.out)
    print(f"wrote {a.out}: {len(frames)} frames, {size / 1024:.0f} KB, {sum(durs) / 1000:.1f}s")
    if size >= MAX_BYTES:
        print("WARNING: over 3 MB", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
