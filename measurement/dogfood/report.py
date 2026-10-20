#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""report.py - turn the 30-day dogfood Creator Studio export into the numbers the README needs.

Reads YOUR analytics CSV (standard library only, offline) using the same parser as
skills/x-audit/xanalytics.py, keeps the dogfood window, and prints:

  * posts and replies in the window, days with at least one post
  * baseline (median impressions per post) and the top outlier multiples
  * median multiple for posts with a link in the body vs without, with n
  * the same median impressions for the 30 days BEFORE the window, if the export has them
  * totals for profile visits, link clicks and follows if the columns exist
  * the numbers you supply by hand: follower counts, leads, calls, clients

It prints AGGREGATES ONLY: no post text and no post IDs are written to the JSON or the
markdown block. The README block is what you paste into the "30-day dogfood" section.

With about 30 posts every comparison is a prompt to test, not a finding. The report says so.

Usage
  python report.py analytics.csv --start 2026-10-21 --end 2026-11-19 \
      --followers-start 120 --followers-end 164 --leads 6 --calls 2 --clients 1
  python report.py analytics.csv --start 2026-10-21 --end 2026-11-19 --json
  python report.py analytics.csv --start 2026-10-21 --end 2026-11-19 --log ~/.claude/x/log.md

--log counts how many logged drafts were marked edited (a line ending in "| edited: yes").

Exit codes: 0 ok, 2 bad input.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import statistics
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "x-audit"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "x-post"))
import xanalytics  # noqa: E402
import xcount  # noqa: E402


def d(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


def med(values: List[float]) -> Optional[float]:
    return float(statistics.median(values)) if values else None


def build(csv_text: str, start: datetime.date, end: datetime.date, manual: Dict[str, Optional[int]],
          log_text: str = "") -> Dict[str, Any]:
    if end < start:
        raise ValueError("--end is before --start")
    posts, notes, mapping = xanalytics.parse(csv_text, include_replies=False)
    everything, _, _ = xanalytics.parse(csv_text, include_replies=True)
    if not any(p["date"] for p in posts):
        raise ValueError("no parseable dates in the export; cannot cut the window")
    in_win = [p for p in posts if p["date"] and start <= p["date"].date() <= end]
    kept_rows = {p["row"] for p in posts}
    replies = [p for p in everything if p["row"] not in kept_rows and p["date"] and start <= p["date"].date() <= end]
    before_start = start - datetime.timedelta(days=(end - start).days + 1)
    before = [p for p in posts if p["date"] and before_start <= p["date"].date() < start]
    res: Dict[str, Any] = {"window": [start.isoformat(), end.isoformat()], "columns_used": mapping,
                           "posts": len(in_win), "replies": len(replies),
                           "days_with_a_post": len({p["date"].date() for p in in_win}),
                           "window_days": (end - start).days + 1}
    if len(in_win) < 3:
        raise ValueError(f"only {len(in_win)} post(s) in the window; need 3 or more for a baseline")
    imps = [p["impressions"] for p in in_win]
    base = med(imps)
    res["median_impressions_per_post"] = base
    res["before_window_posts"] = len(before)
    res["before_window_median_impressions"] = med([p["impressions"] for p in before]) if len(before) >= 3 else None
    mult = sorted((round(p["impressions"] / base, 2) for p in in_win), reverse=True) if base else []
    res["top_multiples"] = mult[:3]
    link = [p["impressions"] / base for p in in_win if p["text"] and xcount.count(p["text"])["urls"]]
    nolink = [p["impressions"] / base for p in in_win if p["text"] and not xcount.count(p["text"])["urls"]]
    res["link_in_body"] = {"n": len(link), "median_multiple": round(med(link), 2) if len(link) >= 3 else None}
    res["no_link"] = {"n": len(nolink), "median_multiple": round(med(nolink), 2) if len(nolink) >= 3 else None}
    for key in ("profile_visits", "link_clicks", "follows"):
        vals = [p.get(key) for p in in_win if p.get(key) is not None]
        res[key + "_total"] = int(sum(vals)) if vals else None
    res["manual"] = manual
    if manual.get("followers_start") is not None and manual.get("followers_end") is not None:
        res["follower_change"] = manual["followers_end"] - manual["followers_start"]
    if log_text:
        lines = [l for l in log_text.splitlines() if l.strip()]
        res["log_lines"] = len(lines)
        res["log_marked_edited"] = sum(1 for l in lines if l.rstrip().lower().endswith("edited: yes"))
    res["caveat"] = ("about 30 posts on one free account over one month: these are observations, "
                     "not findings; nothing here shows cause")
    res["notes"] = notes
    return res


def markdown(r: Dict[str, Any]) -> str:
    def f(v: Any) -> str:
        return "n/a" if v is None else (f"{v:,.0f}" if isinstance(v, float) and v >= 10 else str(v))

    m = r["manual"]
    L = [f"### 30-day dogfood: {r['window'][0]} to {r['window'][1]}", "",
         f"- posts: {r['posts']} on {r['days_with_a_post']} of {r['window_days']} days; replies: {r['replies']}",
         f"- median impressions per post: {f(r['median_impressions_per_post'])}"
         + (f" (previous 30 days: {f(r['before_window_median_impressions'])}, n={r['before_window_posts']})"
            if r["before_window_median_impressions"] is not None else " (no comparable previous 30 days in the export)"),
         f"- top outlier multiples: {', '.join(str(x) + 'x' for x in r['top_multiples'])}",
         f"- link in body: n={r['link_in_body']['n']}, median multiple {f(r['link_in_body']['median_multiple'])}; "
         f"no link: n={r['no_link']['n']}, median multiple {f(r['no_link']['median_multiple'])}",
         f"- profile visits {f(r['profile_visits_total'])}, link clicks {f(r['link_clicks_total'])}, follows from posts {f(r['follows_total'])}"]
    if "follower_change" in r:
        L.append(f"- followers: {m['followers_start']} to {m['followers_end']} ({r['follower_change']:+d})")
    L.append(f"- leads (replies or DMs about work): {f(m.get('leads'))}; calls: {f(m.get('calls'))}; clients: {f(m.get('clients'))}")
    if "log_lines" in r:
        L.append(f"- drafts logged: {r['log_lines']}, marked as edited by hand: {r['log_marked_edited']}")
    L += ["", f"_{r['caveat']}._", ""]
    return "\n".join(L)


def main(argv: Optional[List[str]] = None) -> int:
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Dogfood report from a Creator Studio CSV (aggregates only).")
    ap.add_argument("input", help="analytics CSV, or - for stdin")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--followers-start", type=int)
    ap.add_argument("--followers-end", type=int)
    ap.add_argument("--leads", type=int)
    ap.add_argument("--calls", type=int)
    ap.add_argument("--clients", type=int)
    ap.add_argument("--log", help="path to ~/.claude/x/log.md")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        data = sys.stdin.buffer.read() if args.input == "-" else open(args.input, "rb").read()
        log = open(os.path.expanduser(args.log), encoding="utf-8").read() if args.log else ""
        manual = {"followers_start": args.followers_start, "followers_end": args.followers_end,
                  "leads": args.leads, "calls": args.calls, "clients": args.clients}
        res = build(data.decode("utf-8-sig"), d(args.start), d(args.end), manual, log)
    except (OSError, ValueError) as exc:
        print(f"dogfood report: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        sys.stdout.write(markdown(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
