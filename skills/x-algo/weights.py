#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""weights.py - regenerate references/x-algorithm.md from a pasted param.rs.

The ranking weights in xai-org/x-algorithm move often. This tool does not fetch
anything. You open home-mixer/params/param.rs yourself, save or paste it to a
file, note the commit hash and commit date shown on GitHub, and run:

  python weights.py param.rs --commit 74d49a4 --date 2026-10-20 -o references/x-algorithm.md

It parses every `param!(Name, f64, "key", value);` whose name ends in
`Weight` or `WeightBoost`, writes the table with the commit and dates pinned, and diffs against
the previous version of the output file so you can see what moved. A commit hash
is mandatory: a weights table without a pin is how stale numbers spread.

The prose sections (how to read the weights, reply handling, observed link
behaviour, numbers to stop quoting) are static text in this file. They carry
their own "verified at" commit and are NOT re-verified by a run. If the code
they describe changes, edit them.

Usage
  python weights.py param.rs --commit SHA --date YYYY-MM-DD
  python weights.py param.rs --commit SHA --date YYYY-MM-DD -o references/x-algorithm.md
  python weights.py - --commit SHA --date YYYY-MM-DD --json < param.rs
  python weights.py param.rs --commit SHA --date YYYY-MM-DD --check references/x-algorithm.md

Exit codes: 0 ok, 1 --check found the file out of date, 2 bad input.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

SOURCE_URL = "https://github.com/xai-org/x-algorithm/blob/main/home-mixer/params/param.rs"
STATIC_VERIFIED_COMMIT = "74d49a4ffb398949a5f9312f828d7112d7d31f00"
STATIC_VERIFIED_DATE = "2026-10-21"

PARAM_RE = re.compile(
    r"param!\(\s*(\w+)\s*,\s*(\w+)\s*,\s*\"([^\"]+)\"\s*,\s*(-?[0-9][0-9_]*(?:\.[0-9_]+)?|true|false)\s*,?\s*\)\s*;",
    re.S,
)

MEANING = {
    "ShareViaCopyLinkWeight": "someone copies the link to the post",
    "ReplyWeight": "reply",
    "BidirectionalFollowReplyWeightBoost": "added to the reply weight when author and viewer follow each other",
    "QuoteWeight": "quote post",
    "ShareViaDmWeight": "shared in a DM",
    "FollowAuthorWeight": "viewer follows the author from this post",
    "ShareWeight": "share",
    "RetweetWeight": "repost",
    "FavoriteWeight": "like",
    "ClickWeight": "click into the post",
    "OpenLinkWeight": "open a link in the post",
    "DwellWeight": "dwell on the post",
    "ContDwellTimeWeight": "continuous dwell time",
    "ContClickDwellTimeWeight": "continuous dwell time after a click",
    "PhotoExpandWeight": "expand a photo",
    "VideoOpenWeight": "open a video",
    "ProfileClickWeight": "click through to the author's profile",
    "QuotedClickWeight": "click on a quoted post",
    "PostUnexploredWeight": "post is new to the viewer",
    "VqvWeight": "qualified video view",
    "QuotedVqvWeight": "qualified video view of a quoted post",
    "ReactWithVideoWeight": "react with a video",
    "BidirectionalFollowDwellWeightBoost": "added to dwell weight when author and viewer follow each other",
    "NotInterestedWeight": "viewer taps not interested",
    "BlockAuthorWeight": "viewer blocks the author",
    "MuteAuthorWeight": "viewer mutes the author",
    "ReportWeight": "viewer reports the post",
    "NotDwelledWeight": "viewer scrolled past without dwelling",
}


def parse_params(text: str) -> List[Dict[str, object]]:
    out = []
    for m in PARAM_RE.finditer(text.replace("\r\n", "\n")):
        name, typ, key, raw = m.groups()
        if typ not in ("f64", "f32"):
            continue
        if not re.search(r"(Weight|WeightBoost)$", name):
            continue
        out.append({"name": name, "key": key, "value": float(raw.replace("_", ""))})
    return out


def fmt(v: float) -> str:
    return f"{v:g}"


def previous_values(md: str) -> Dict[str, float]:
    prev: Dict[str, float] = {}
    for m in re.finditer(r"^\|\s*`(\w+)`\s*\|\s*(-?[0-9.]+)\s*\|", md, re.M):
        prev[m.group(1)] = float(m.group(2))
    return prev


def diff_section(params: List[Dict[str, object]], prev: Dict[str, float]) -> List[str]:
    cur = {str(p["name"]): float(p["value"]) for p in params}  # type: ignore[arg-type]
    lines = []
    for name in sorted(cur):
        if name not in prev:
            lines.append(f"- added: `{name}` = {fmt(cur[name])}")
        elif prev[name] != cur[name]:
            lines.append(f"- changed: `{name}` {fmt(prev[name])} -> {fmt(cur[name])}")
    for name in sorted(prev):
        if name not in cur:
            lines.append(f"- removed: `{name}` (was {fmt(prev[name])})")
    return lines


def render(params: List[Dict[str, object]], commit: str, date: str, checked: str, source_url: str,
           prev: Optional[Dict[str, float]]) -> str:
    L: List[str] = []
    L += ["# X ranking weights", "",
          f"- source: {source_url}",
          f"- pinned commit: `{commit}`",
          f"- commit date: {date}",
          f"- last checked: {checked}",
          "- generated by `skills/x-algo/weights.py`; do not edit the table by hand", "",
          "These weights move often. The numbers below are true for the pinned commit and nothing else.", "",
          "## Weights", "",
          "| param | value | what it scales |", "|---|---|---|"]
    ordered = sorted(params, key=lambda p: -abs(float(p["value"])))  # type: ignore[arg-type]
    for p in ordered:
        L.append(f"| `{p['name']}` | {fmt(float(p['value']))} | {MEANING.get(str(p['name']), '(not described here)')} |")  # type: ignore[arg-type]
    reply = next((float(p["value"]) for p in params if p["name"] == "ReplyWeight"), None)  # type: ignore[arg-type]
    boost = next((float(p["value"]) for p in params if p["name"] == "BidirectionalFollowReplyWeightBoost"), None)  # type: ignore[arg-type]
    if reply is not None and boost is not None:
        L += ["", f"A reply from someone who follows the author and is followed back scales with {fmt(reply)} + {fmt(boost)} = {fmt(reply + boost)}."]
    if prev:
        d = diff_section(params, prev)
        L += ["", "## Changed since the previous version of this file", ""]
        L += d if d else ["- no weight changed"]
    L += ["", f"## How to read these (static text, verified at `{STATIC_VERIFIED_COMMIT[:7]}` on {STATIC_VERIFIED_DATE})", "",
          "- Each weight multiplies a predicted probability (or a continuous value such as watch time). It does not multiply a raw count.",
          "- The file's own comments say so, and call out the claim that one report cancels 468 likes as wrong. Never write it.",
          "- Negative actions carry big weights because they are rare, not because one of them equals hundreds of likes.",
          "- Mass blocking or reporting does not suppress a post for everyone: predictions are personalised, and only actions on posts served in Home count.",
          "", f"## Link posts: observed, not coded (static, checked {STATIC_VERIFIED_DATE})", "",
          "- `param.rs` has no link penalty. `OpenLinkWeight` rewards an open; nothing demotes the presence of a link.",
          "- Reach loss on link posts from non-Premium accounts was observed in March 2025 (Buffer, 18.8M posts). That is a measurement from outside, not a coded rule, and it predates this snapshot.",
          "- Default in this repo: link in the first reply, labelled 'observed, not coded'.",
          "", f"## Replies (static, verified at `{STATIC_VERIFIED_COMMIT[:7]}` on {STATIC_VERIFIED_DATE})", "",
          "Source: `grox/flows/reply_spam/` in the same repository.", "",
          "- A Grok model scores replies 0 to 3 and returns a reason. It runs when the parent or root account has more than 250,000 followers. The prompt is excluded from the open-source release.",
          "- Replies under accounts at or below that size go through a separate spam classifier instead.",
          "- A multi-step reply-spam filter looks at threads where the replier replies to their own reply, under a root account with 1,000 or more followers. It needs 2 or more flagged posts from the same author, the newest must be flagged, and accounts with high page rank or a grey badge are exempt. Flagged posts get a reply ranking score of 0 and a safety label.",
          "- A coordinated-spam filter applies when the root account has 180,000 or more followers and the thread is at least 2 levels deep.",
          "- Reply downvotes (March 2026, Premium users) list 'AI generated' as a reason. Source: secondary reporting, not verified in this repo.",
          "", "## Numbers to stop quoting", "",
          "Blogs still quote 2023 figures. They are wrong for this snapshot: reply 13.5, author reply-back +75, report -369. Use the table above.",
          ""]
    return "\n".join(L)


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return data.decode("utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Regenerate references/x-algorithm.md from a pasted param.rs.")
    ap.add_argument("input", help="param.rs, or - for stdin")
    ap.add_argument("--commit", required=True, help="commit hash you read the file at (7-40 hex chars)")
    ap.add_argument("--date", required=True, help="commit date, YYYY-MM-DD")
    ap.add_argument("--checked", default=datetime.date.today().isoformat(), help="date you checked, default today")
    ap.add_argument("--source-url", default=SOURCE_URL)
    ap.add_argument("--previous", help="previous output file to diff against (default: the -o file if it exists)")
    ap.add_argument("-o", "--out", help="write markdown here")
    ap.add_argument("--check", metavar="FILE", help="exit 1 if FILE's table differs from this param.rs")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if not re.fullmatch(r"[0-9a-fA-F]{7,40}", args.commit):
            raise ValueError("--commit must be a 7 to 40 character hex hash")
        for d in (args.date, args.checked):
            datetime.date.fromisoformat(d)
        params = parse_params(read_input(args.input))
        if len(params) < 5:
            raise ValueError(f"found only {len(params)} weight params; is this home-mixer/params/param.rs?")
        prev_path = args.previous or (args.out if args.out and os.path.exists(args.out) else None)
        prev = previous_values(open(prev_path, encoding="utf-8").read()) if prev_path and os.path.exists(prev_path) else None
        if args.check:
            have = previous_values(open(args.check, encoding="utf-8").read())
            d = diff_section(params, have)
            if d:
                print("\n".join(d))
                return 1
            print("up to date")
            return 0
    except (OSError, ValueError) as exc:
        print(f"weights: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"commit": args.commit, "date": args.date, "params": params}, indent=2))
        return 0
    md = render(params, args.commit.lower(), args.date, args.checked, args.source_url, prev)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print(f"wrote {args.out} ({len(params)} weights)", file=sys.stderr)
    else:
        sys.stdout.buffer.write(md.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
