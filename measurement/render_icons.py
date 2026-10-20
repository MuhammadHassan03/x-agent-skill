#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""render_icons.py - render the site's PNG icons and the 1200x630 social preview from the mark.

Research-style helper, NOT part of the plugin: it needs Pillow (`pip install pillow`),
like measurement/validate.py needs pyarrow. The mark is drawn from the same geometry as
site/icon.svg (viewBox 512), supersampled 8x and downsampled, so the PNGs match the SVG.

Writes into the output directory (default: ../site):
  favicon-32.png, apple-touch-icon.png (180), icon-64.png (README), og.png (1200x630)

The social preview text is rasterised with the first font found from a short list of
common bold system fonts. Pass --font to use another (an open-licence font is the safest
choice if you redistribute the output commercially).

Usage
  python measurement/render_icons.py
  python measurement/render_icons.py --handle mirza_hassan07 --out site
  python measurement/render_icons.py --font /path/to/Inter-Bold.ttf
"""
from __future__ import annotations

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
INK = (14, 15, 18, 255)
EDGE = (34, 38, 46, 255)
PAPER = (242, 243, 245, 255)
ACCENT = (255, 106, 61, 255)
MUTED = (160, 168, 180, 255)
SS = 8  # supersampling factor
FONTS = [
    "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def rotated_bar(canvas: Image.Image, x: float, y: float, w: float, h: float, r: float,
                angle: float, cx: float, cy: float, fill) -> None:
    """Draw a rounded bar and rotate it clockwise by `angle` degrees about (cx, cy), like SVG."""
    k = canvas.width / 512
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([x * k, y * k, (x + w) * k, (y + h) * k], radius=r * k, fill=fill)
    if angle:
        layer = layer.rotate(-angle, resample=Image.BICUBIC, center=(cx * k, cy * k))
    canvas.alpha_composite(layer)


def mark(size: int) -> Image.Image:
    big = size * SS
    k = big / 512
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big - 1, big - 1], radius=113 * k, fill=EDGE)          # stroke: 3px out, 3px in
    d.rounded_rectangle([6 * k, 6 * k, 506 * k - 1, 506 * k - 1], radius=107 * k, fill=INK)
    rotated_bar(img, 140, 131, 40, 250, 12, 22, 160, 256, PAPER)
    rotated_bar(img, 280, 186, 40, 180, 12, 45, 300, 276, PAPER)
    rotated_bar(img, 280, 186, 40, 180, 12, -45, 300, 276, PAPER)
    rotated_bar(img, 390, 176, 28, 190, 7, 0, 0, 0, ACCENT)
    return img.resize((size, size), Image.LANCZOS)


def font(path, size):
    for p in ([path] if path else []) + FONTS:
        if p and os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise SystemExit("render_icons: no bold font found; pass --font /path/to/font.ttf")


def social(handle: str, font_path) -> Image.Image:
    w, h = 1200, 630
    img = Image.new("RGBA", (w, h), INK)
    m = mark(220)
    img.alpha_composite(m, (90, (h - 220) // 2))
    d = ImageDraw.Draw(img)
    x = 90 + 220 + 70
    big, mid, small = font(font_path, 78), font(font_path, 34), font(font_path, 30)
    d.text((x, 205), "The skills write.", font=big, fill=PAPER)
    d.text((x, 205 + 92), "You post.", font=big, fill=ACCENT)
    d.text((x, 205 + 92 + 120), "@" + handle, font=mid, fill=PAPER)
    d.text((x, 205 + 92 + 120 + 52), "Claude Code skills for X. No API, no bot.", font=small, fill=MUTED)
    return img.convert("RGB")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render site icons and the social preview from the mark.")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "site"))
    ap.add_argument("--handle", default="mirza_hassan07", help="X handle without the @")
    ap.add_argument("--font", help="path to a bold .ttf for the social preview")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    for name, size in (("favicon-32.png", 32), ("apple-touch-icon.png", 180), ("icon-64.png", 64)):
        mark(size).save(os.path.join(a.out, name), optimize=True)
    social(a.handle.lstrip("@"), a.font).save(os.path.join(a.out, "og.png"), optimize=True)
    print("wrote favicon-32.png, apple-touch-icon.png, icon-64.png, og.png to", os.path.abspath(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
