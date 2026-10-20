#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""swipe.py - rank posts YOU collected by how far they beat their own account.

Raw views are not evidence. A 2,000,000-follower account at 400,000 views had a
quiet day; a 4,000-follower account at 400,000 views found something. This ranks
on the outlier multiple: views divided by that account's own typical post.

How the data gets here: you browse X yourself, by hand, at human speed, and note
down posts that caught your eye plus a few ordinary ones from the same account.
You paste or type them into a CSV or TSV. This tool never touches X.

Columns (headers are matched flexibly, case and spacing ignored):

  account    @handle                       aliases: handle, user, username, author
  views      views or impressions          aliases: impressions, view count
  hook       the post's first line         aliases: text, post, tweet, content
  median     optional: the account's typical views (overrides the computed one)

Baseline per account:
  1. the `median` column if you gave one;
  2. otherwise the median of that account's captured posts, which needs 3 or
     more posts for the account. Capture ordinary posts too, not only the hits,
     or the median is inflated and the multiple is understated.
Accounts with neither are listed as "no baseline" and never ranked.

Numbers like 12.4K, 1.2M and 3,400 are understood.

Usage
  python swipe.py captured.tsv
  python swipe.py captured.csv --min-multiple 3 --top 15
  python swipe.py captured.tsv --out ~/.claude/x/swipe.md
  python swipe.py captured.tsv --json
  python swipe.py - < captured.tsv

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
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.join(HERE, "..", "x-post", "hooks.json")

ALIASES = {
    "account": ["account", "handle", "user", "username", "author", "screenname"],
    "views": ["views", "impressions", "viewcount", "impressioncount"],
    "hook": ["hook", "text", "post", "tweet", "content", "firstline", "posttext"],
    "median": ["median", "medianviews", "baseline", "typical", "medianimpressions"],
}


def norm(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", h.lower())


def parse_num(s: str) -> Optional[float]:
    s = (s or "").strip().lower().replace(",", "").replace("_", "")
    if not s:
        return None
    m = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*([kmb]?)", s)
    if not m:
        return None
    mult = {"": 1, "k": 1e3, "m": 1e6, "b": 1e9}[m.group(2)]
    return float(m.group(1)) * mult


def map_columns(header: List[str]) -> Dict[str, int]:
    idx: Dict[str, int] = {}
    normed = [norm(h) for h in header]
    for field, names in ALIASES.items():
        for n in names:
            if n in normed:
                idx[field] = normed.index(n)
                break
    return idx


def load_formulas() -> List[Tuple[str, "re.Pattern[str]"]]:
    try:
        with open(HOOKS, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    return [(h["name"], re.compile(h["match"], re.I)) for h in data["hooks"]]


def classify(hook: str, formulas: List[Tuple[str, "re.Pattern[str]"]]) -> str:
    for name, pat in formulas:
        if pat.search(hook.strip()):
            return name
    return "unclassified"


def parse(text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ValueError("empty input")
    first = text.splitlines()[0]
    delim = max(["\t", ",", ";"], key=first.count)
    if first.count(delim) == 0:
        raise ValueError("could not find a header row with delimiters (tab, comma or semicolon)")
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    header, body = rows[0], rows[1:]
    idx = map_columns(header)
    missing = [f for f in ("account", "views") if f not in idx]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}. Found headers: {header}")
    notes: List[str] = []
    out: List[Dict[str, Any]] = []
    for n, r in enumerate(body, 2):
        if not any(c.strip() for c in r):
            continue
        get = lambda f: r[idx[f]].strip() if f in idx and idx[f] < len(r) else ""  # noqa: E731
        views = parse_num(get("views"))
        acct = get("account").lstrip("@").lower()
        if views is None or not acct:
            notes.append(f"row {n}: skipped (account or views missing or not a number)")
            continue
        out.append({"account": acct, "views": views, "hook": get("hook"),
                    "median": parse_num(get("median"))})
    if not out:
        raise ValueError("no usable rows")
    return out, notes


def rank(rows: List[Dict[str, Any]], min_multiple: float = 3.0) -> Dict[str, Any]:
    by: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[r["account"]].append(r)
    formulas = load_formulas()
    ranked: List[Dict[str, Any]] = []
    no_base: List[Dict[str, Any]] = []
    for acct, posts in by.items():
        given = next((p["median"] for p in posts if p["median"]), None)
        if given:
            base, source = given, "given"
        elif len(posts) >= 3:
            base, source = statistics.median(p["views"] for p in posts), "computed"
        else:
            no_base.append({"account": acct, "posts": len(posts),
                            "reason": "needs a median column or 3+ captured posts"})
            continue
        if base <= 0:
            no_base.append({"account": acct, "posts": len(posts), "reason": "baseline is zero"})
            continue
        for p in posts:
            ranked.append({"account": acct, "views": p["views"], "baseline": base,
                           "baseline_source": source, "multiple": round(p["views"] / base, 2),
                           "hook": p["hook"], "formula": classify(p["hook"], formulas) if p["hook"] else "unclassified",
                           "outlier": p["views"] / base >= min_multiple})
    ranked.sort(key=lambda r: -r["multiple"])
    by_formula: Dict[str, List[float]] = defaultdict(list)
    for r in ranked:
        if r["outlier"]:
            by_formula[r["formula"]].append(r["multiple"])
    summary = sorted(({"formula": f, "outliers": len(v), "median_multiple": round(statistics.median(v), 2)}
                      for f, v in by_formula.items()), key=lambda d: (-d["outliers"], -d["median_multiple"]))
    return {"ranked": ranked, "no_baseline": no_base, "formula_summary": summary,
            "min_multiple": min_multiple}


def fmt(n: float) -> str:
    return f"{n:,.0f}"


def render_md(res: Dict[str, Any], top: int) -> str:
    L = ["# Swipe file", "",
         f"Ranked by outlier multiple (views over that account's own baseline). Outlier = {res['min_multiple']}x or more.",
         "Your own research: n is small, formulas are labels not causes.", ""]
    for r in res["ranked"][:top]:
        flag = "**OUTLIER** " if r["outlier"] else ""
        L.append(f"- {flag}{r['multiple']}x  @{r['account']}  ({fmt(r['views'])} vs {fmt(r['baseline'])} {r['baseline_source']})  "
                 f"[{r['formula']}]  {r['hook'][:140]}")
    if res["formula_summary"]:
        L += ["", "## Formulas among the outliers", ""]
        for s in res["formula_summary"]:
            L.append(f"- {s['formula']}: {s['outliers']} outlier(s), median {s['median_multiple']}x")
    if res["no_baseline"]:
        L += ["", "## No baseline (not ranked)", ""]
        for s in res["no_baseline"]:
            L.append(f"- @{s['account']}: {s['reason']}")
    return "\n".join(L) + "\n"


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return data.decode("utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Rank collected posts by outlier multiple over each account's own baseline.")
    ap.add_argument("input", help="CSV/TSV file, or - for stdin")
    ap.add_argument("--min-multiple", type=float, default=3.0)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", help="write the swipe file (markdown) here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        rows, notes = parse(read_input(args.input))
        res = rank(rows, args.min_multiple)
    except (OSError, ValueError) as exc:
        print(f"swipe: {exc}", file=sys.stderr)
        return 2
    res["skipped"] = notes
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        md = render_md(res, args.top)
        if args.out:
            path = os.path.expanduser(args.out)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(md)
            print(f"wrote {path}", file=sys.stderr)
        sys.stdout.buffer.write(md.encode("utf-8"))
        for n in notes:
            print(n, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
