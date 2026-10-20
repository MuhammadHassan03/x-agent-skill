#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""xcount.py - count a post the way X does, offline.

X does not count characters. It counts weighted characters using the public
twitter-text configuration (v3):

  * code points 0-4351 and the ranges 8192-8205, 8208-8223, 8242-8247 weigh 1
  * every other code point weighs 2 (CJK, Arabic, most emoji, and so on)
  * an emoji sequence (flag, skin tone, ZWJ family, keycap) weighs 2 in total
  * every URL weighs 23, whatever its real length
  * text is normalised to NFC first

Limits: 280 on a free account. Premium accounts can post up to 25,000 on every
tier (see references/x-rules.md, last checked 2026-10-21). The default here is
the free tier. Pass --premium to check the long limit.

This is a faithful re-implementation of the counting rules, not a call to X.
The one approximation is URL detection: it recognises http(s) links, www links
and bare domains on a fixed list of common TLDs. A bare domain on a rare TLD may
be counted as plain text here and as a 23-weight link by X. When a post sits
within a few characters of the limit, count it again in the composer.

Usage
  python xcount.py post.txt
  python xcount.py - < post.txt
  python xcount.py post.txt --premium
  python xcount.py post.txt --json

Exit codes: 0 fits, 1 over the limit, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Dict, List, Optional, Tuple

FREE_LIMIT = 280
PREMIUM_LIMIT = 25000
URL_WEIGHT = 23
DEFAULT_WEIGHT = 2
# (start, end) inclusive, weight 1. Vendored from twitter-text config/v3.json.
LIGHT_RANGES: Tuple[Tuple[int, int], ...] = (
    (0, 4351),
    (8192, 8205),
    (8208, 8223),
    (8242, 8247),
)

_TLDS = (
    "com|org|net|io|co|ai|dev|app|me|us|uk|ca|de|fr|es|it|nl|se|no|fi|dk|ch|at|be|"
    "au|nz|in|jp|kr|cn|br|mx|ru|pl|info|biz|xyz|tv|fm|gg|sh|to|so|ly|link|blog|"
    "tech|site|online|store|shop|page|news|media|email|world|today|cloud|studio|"
    "design|agency|digital|network|systems|company|ink|club|live|pro|gov|edu"
)
URL_RE = re.compile(
    r"(?i)(?:https?://[^\s<>\"]+|www\.[^\s<>\"]+"
    r"|(?<![@\w./-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:" + _TLDS + r")\b(?:/[^\s<>\"]*)?)"
)
_TRAILING = ".,;:!?)]}'\""

# One emoji sequence, matched greedily so it weighs 2 in total.
_MOD = "[\U0001F3FB-\U0001F3FF]"
_BASE = (
    "(?:[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿"
    "←-⇿⤀-⥿〰〽㊗㊙©®‼⁉"
    "™ℹⓂ▪▫▶◀◻-◾])"
)
EMOJI_RE = re.compile(
    "(?:[\U0001F1E6-\U0001F1FF]{2}"                       # flag
    "|[0-9#*]️?⃣"                                # keycap
    "|\U0001F3F4[\U000E0020-\U000E007E]+\U000E007F"        # subdivision flag
    "|" + _BASE + "️?" + _MOD + "?"
    "(?:‍" + _BASE + "️?" + _MOD + "?)*)"
)
# A bare keycap-like digit is not an emoji without the keycap mark, and the
# symbols above include a few text-presentation characters. Only count those as
# emoji when followed by the emoji variation selector.
_TEXT_SYMBOLS = set("©®‼⁉™ℹⓂ▪▫▶◀"
                    "◻◼◽◾←↑→↓↔↕↖"
                    "↗↘↙")


def _weight(cp: int) -> int:
    for lo, hi in LIGHT_RANGES:
        if lo <= cp <= hi:
            return 1
    return DEFAULT_WEIGHT


def _url_spans(text: str) -> List[Tuple[int, int]]:
    spans = []
    for m in URL_RE.finditer(text):
        start, end = m.start(), m.end()
        while end > start and text[end - 1] in _TRAILING:
            end -= 1
        if end > start:
            spans.append((start, end))
    return spans


def count(text: str, premium: bool = False) -> Dict[str, object]:
    """Return the weighted length of `text` and where it sits against the limit."""
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    spans = _url_spans(text)
    total = 0
    urls = len(spans)
    i = 0
    si = 0
    while i < len(text):
        if si < len(spans) and i == spans[si][0]:
            total += URL_WEIGHT
            i = spans[si][1]
            si += 1
            continue
        m = EMOJI_RE.match(text, i)
        if m and m.end() > i:
            seq = m.group(0)
            keep = not (len(seq) == 1 and seq in _TEXT_SYMBOLS)
            if keep and (si >= len(spans) or m.end() <= spans[si][0]):
                total += DEFAULT_WEIGHT
                i = m.end()
                continue
        total += _weight(ord(text[i]))
        i += 1
    limit = PREMIUM_LIMIT if premium else FREE_LIMIT
    return {
        "weighted": total,
        "limit": limit,
        "remaining": limit - total,
        "over": max(0, total - limit),
        "fits": total <= limit,
        "tier": "premium" if premium else "free",
        "urls": urls,
        "code_points": len(text),
        "non_latin_weight_2": sum(1 for c in text if _weight(ord(c)) == 2),
    }


def read_input(path: str) -> str:
    if path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Weighted post length, the way X counts it.")
    ap.add_argument("input", help="text file, or - for stdin")
    ap.add_argument("--premium", action="store_true", help="check the 25,000 long-post limit")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    try:
        text = read_input(args.input)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"xcount: cannot read input: {exc}", file=sys.stderr)
        return 2
    res = count(text.rstrip("\r\n"), premium=args.premium)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        state = "FITS" if res["fits"] else f"OVER by {res['over']}"
        print(f"{res['weighted']} / {res['limit']} weighted ({res['tier']})  {state}")
        print(f"  remaining {res['remaining']}, urls {res['urls']} (each 23), "
              f"weight-2 characters {res['non_latin_weight_2']}")
        if not args.premium and not res["fits"]:
            print("  Over 280 on a free account. Cut it, or split it with /x-thread.")
    return 0 if res["fits"] else 1


if __name__ == "__main__":
    sys.exit(main())
