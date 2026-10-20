#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""xanalytics.py - read YOUR OWN analytics export and rank posts by outlier multiple.

You export your post analytics from X yourself (Creator Studio / Analytics, a
CSV download from your own account) and give the file to this tool. It reads the
file. It never touches X.

X does not document the column layout of the organic export, so headers are
matched flexibly (case, spaces and punctuation ignored). Required: an
impressions column. Used when present: post text, date, likes, replies, reposts,
bookmarks, shares, profile visits, link clicks, engagements, new follows, a
post-type or reply flag.

Method:
  * Replies are dropped by default (a reply flag column, or text that starts
    with "@"). Pass --include-replies to keep them.
  * Baseline = the median impressions of all remaining posts. Needs 3 or more.
  * Outlier multiple = impressions / baseline. Never raw impressions.
  * Feature comparison (link in body, length, question, weekday, hour) shows the
    median multiple per group, and only for groups with 3 or more posts. These
    are observations on your own small sample, not causes. With under 30 posts
    treat every comparison as a prompt to test, not a finding.

Usage
  python xanalytics.py analytics.csv
  python xanalytics.py analytics.csv --top 10 --json
  python xanalytics.py analytics.csv --include-replies
  python xanalytics.py - < analytics.csv

Exit codes: 0 ok, 2 bad input.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import statistics
import sys
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "x-post"))
import xcount  # noqa: E402

ALIASES: Dict[str, List[str]] = {
    "text": ["posttext", "text", "post", "tweettext", "content", "tweet", "fulltext"],
    "date": ["date", "time", "posted", "createdat", "posttime", "timestamp", "datetime"],
    "impressions": ["impressions", "views", "impressioncount", "totalimpressions"],
    "likes": ["likes", "like", "favorites", "likecount"],
    "replies": ["replies", "reply", "replycount"],
    "reposts": ["reposts", "retweets", "repost", "retweet", "repostcount"],
    "bookmarks": ["bookmarks", "bookmark", "bookmarkcount"],
    "shares": ["shares", "share", "sharecount"],
    "profile_visits": ["profilevisits", "profileclicks", "profilevisit"],
    "link_clicks": ["linkclicks", "urlclicks", "linkclick", "detailexpands"],
    "engagements": ["engagements", "totalengagements", "engagement"],
    "follows": ["follows", "newfollows", "newfollowers", "followsfromposts"],
    "kind": ["posttype", "type", "isreply", "reply", "replyflag", "inreplyto"],
}
NUMERIC = ["impressions", "likes", "replies", "reposts", "bookmarks", "shares",
           "profile_visits", "link_clicks", "engagements", "follows"]
DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d", "%b %d, %Y %H:%M", "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y %H:%M",
                "%m/%d/%Y", "%d %b %Y %H:%M", "%d %b %Y", "%a %b %d %H:%M:%S %z %Y"]


def norm(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", h.lower())


def num(s: str) -> Optional[float]:
    s = (s or "").strip().lower().replace(",", "")
    if not s or s in ("-", "n/a", "na"):
        return None
    m = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*([kmb]?)", s)
    if not m:
        return None
    return float(m.group(1)) * {"": 1, "k": 1e3, "m": 1e6, "b": 1e9}[m.group(2)]


def parse_date(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    if not s:
        return None
    for f in DATE_FORMATS:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    return None


def parse(text: str, include_replies: bool = False) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, str]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ValueError("empty input")
    first = text.splitlines()[0]
    delim = max([",", "\t", ";"], key=first.count)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    header, body = rows[0], rows[1:]
    normed = [norm(h) for h in header]
    idx: Dict[str, int] = {}
    for field, names in ALIASES.items():
        for n in names:
            if n in normed:
                idx[field] = normed.index(n)
                break
    if "impressions" not in idx:
        raise ValueError(f"no impressions column. Found headers: {header}")
    notes: List[str] = []
    mapping = {f: header[i] for f, i in idx.items()}
    posts: List[Dict[str, Any]] = []
    dropped_replies = 0
    for n, r in enumerate(body, 2):
        if not any(c.strip() for c in r):
            continue
        cell = lambda f: r[idx[f]].strip() if f in idx and idx[f] < len(r) else ""  # noqa: E731
        imp = num(cell("impressions"))
        if imp is None:
            notes.append(f"row {n}: skipped (impressions missing or not a number)")
            continue
        txt = cell("text")
        kind = cell("kind").lower()
        kind_head = normed[idx["kind"]] if "kind" in idx else ""
        if kind_head == "inreplyto":
            flagged = bool(kind)
        elif kind_head in ("isreply", "reply", "replyflag"):
            flagged = kind in ("true", "1", "yes", "y")
        else:
            flagged = kind in ("reply", "replies")
        is_reply = txt.lstrip().startswith("@") or flagged
        if is_reply and not include_replies:
            dropped_replies += 1
            continue
        p: Dict[str, Any] = {"row": n, "text": txt, "impressions": imp, "date": parse_date(cell("date"))}
        for f in NUMERIC:
            if f != "impressions":
                p[f] = num(cell(f))
        posts.append(p)
    if dropped_replies:
        notes.append(f"{dropped_replies} reply row(s) dropped (use --include-replies to keep them)")
    return posts, notes, mapping


def analyse(posts: List[Dict[str, Any]], top: int = 10) -> Dict[str, Any]:
    if len(posts) < 3:
        raise ValueError(f"need 3 or more posts for a baseline, got {len(posts)}")
    base = statistics.median(p["impressions"] for p in posts)
    if base <= 0:
        raise ValueError("median impressions is zero; the export looks empty or incomplete")
    for p in posts:
        p["multiple"] = round(p["impressions"] / base, 2)
        eng = p.get("engagements")
        if eng is None:
            parts = [p.get(k) for k in ("likes", "replies", "reposts", "bookmarks")]
            eng = sum(x for x in parts if x is not None) if any(x is not None for x in parts) else None
        p["engagement_rate"] = round(eng / p["impressions"], 4) if eng is not None and p["impressions"] else None
        w = int(xcount.count(p["text"])["weighted"]) if p["text"] else None
        p["weighted"] = w
    ranked = sorted(posts, key=lambda p: -p["multiple"])

    def group(name: str, keyf: Callable[[Dict[str, Any]], Optional[str]]) -> Dict[str, Any]:
        buckets: Dict[str, List[float]] = {}
        for p in posts:
            k = keyf(p)
            if k is not None:
                buckets.setdefault(k, []).append(p["multiple"])
        rows = []
        for k, v in sorted(buckets.items()):
            rows.append({"group": k, "n": len(v),
                         "median_multiple": round(statistics.median(v), 2) if len(v) >= 3 else None})
        return {"feature": name, "groups": rows}

    def length_bucket(p: Dict[str, Any]) -> Optional[str]:
        w = p["weighted"]
        if w is None:
            return None
        return "<=100" if w <= 100 else "101-200" if w <= 200 else "201-280" if w <= 280 else ">280"

    has_time = any(p["date"] and (p["date"].hour or p["date"].minute) for p in posts)
    features = [
        group("link in body", lambda p: None if not p["text"] else ("link" if xcount.count(p["text"])["urls"] else "no link")),
        group("length (weighted)", length_bucket),
        group("question", lambda p: None if not p["text"] else ("question" if "?" in p["text"] else "statement")),
        group("weekday", lambda p: p["date"].strftime("%a") if p["date"] else None),
        group("hour", lambda p: f"{p['date'].hour:02d}:00" if p["date"] and has_time else None),
    ]
    caveat = ("fewer than 30 posts: treat comparisons as prompts to test, not findings"
              if len(posts) < 30 else "comparisons are correlations on your own posts, not causes")
    def slim(p: Dict[str, Any]) -> Dict[str, Any]:
        return {"row": p["row"], "multiple": p["multiple"], "impressions": p["impressions"],
                "engagement_rate": p["engagement_rate"], "text": p["text"][:140],
                "date": p["date"].isoformat() if p["date"] else None}
    return {"posts": len(posts), "baseline_median_impressions": base,
            "top": [slim(p) for p in ranked[:top]],
            "bottom": [slim(p) for p in ranked[-min(top, len(ranked)):][::-1]],
            "features": features, "caveat": caveat}


def render(res: Dict[str, Any], notes: List[str], mapping: Dict[str, str]) -> str:
    L = [f"\nX ANALYTICS  {res['posts']} posts, baseline {res['baseline_median_impressions']:,.0f} median impressions",
         "columns used: " + ", ".join(f"{k}={v!r}" for k, v in mapping.items()), "", "TOP (outlier multiple)"]
    for p in res["top"]:
        er = f"  eng {p['engagement_rate']:.1%}" if p["engagement_rate"] is not None else ""
        L.append(f"  {p['multiple']:>6.2f}x  {p['impressions']:>9,.0f}{er}  {p['text'][:90]}")
    L += ["", "BOTTOM"]
    for p in res["bottom"][:5]:
        L.append(f"  {p['multiple']:>6.2f}x  {p['impressions']:>9,.0f}  {p['text'][:90]}")
    L += ["", "FEATURES (median multiple, groups of 3+ only)"]
    for f in res["features"]:
        if not f["groups"]:
            continue
        cells = [f"{g['group']}: " + (f"{g['median_multiple']}x" if g["median_multiple"] is not None else "n<3") + f" (n={g['n']})"
                 for g in f["groups"]]
        L.append(f"  {f['feature']:<18} " + "  |  ".join(cells))
    L += ["", f"Note: {res['caveat']}."] + [f"Note: {n}" for n in notes] + [""]
    return "\n".join(L)


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return data.decode("utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Rank your own posts by outlier multiple from an analytics CSV.")
    ap.add_argument("input", help="analytics CSV, or - for stdin")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--include-replies", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        posts, notes, mapping = parse(read_input(args.input), args.include_replies)
        res = analyse(posts, args.top)
    except (OSError, ValueError) as exc:
        print(f"xanalytics: {exc}", file=sys.stderr)
        return 2
    if args.json:
        res["notes"] = notes
        res["columns"] = mapping
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        sys.stdout.buffer.write(render(res, notes, mapping).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
