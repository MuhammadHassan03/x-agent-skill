#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""thread.py - split a long draft into a thread of posts that fit, offline.

Rules it applies:

  * Each post is at most 280 weighted characters (xcount.py rules: URLs weigh
    23, CJK and most emoji weigh 2).
  * A blank line in the draft is a post boundary. A paragraph that is too long
    is split at sentence ends, and a sentence that is too long is split at
    word boundaries (and flagged).
  * Links are pulled out of every post and emitted as a separate FIRST REPLY
    block, to be posted as a reply under post 1. On a free account, links in the
    root post were observed to cost reach (observed, not coded; see
    references/x-algorithm.md). With --links-last the old behaviour is kept and
    the links go in the last post of the thread instead.
  * With --number, posts get an "i/N" prefix, counted in the budget.
  * The first post is checked as a hook (postscore.check_hook).

It writes nothing to X. You copy the posts into the composer yourself.

Usage
  python thread.py draft.txt
  python thread.py draft.txt --number
  python thread.py draft.txt --pack          merge short paragraphs into one post
  python thread.py draft.txt --links-last    put links in the last post, no FIRST REPLY block
  python thread.py draft.txt --json
  python thread.py - < draft.txt

Exit codes: 0 ok, 1 ok with warnings that need a human, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "x-post"))
import postscore  # noqa: E402
import xcount  # noqa: E402

LIMIT = xcount.FREE_LIMIT
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=\S)|(?<=[。！？])")


def weighted(s: str) -> int:
    return int(xcount.count(s)["weighted"])


def _chunks(word: str, budget: int) -> List[str]:
    """Break a run with no spaces (CJK, a pasted token) into pieces that fit."""
    if weighted(word) <= budget:
        return [word]
    out, cur = [], ""
    for ch in word:
        if weighted(cur + ch) > budget:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def split_long(text: str, budget: int, warnings: List[str]) -> List[str]:
    """Split one over-budget paragraph at sentence ends, then at words."""
    sentences = [s for s in SENT_SPLIT.split(text.strip()) if s]
    out: List[str] = []
    cur = ""
    for s in sentences:
        if weighted(s) > budget:
            if cur:
                out.append(cur)
                cur = ""
            warnings.append("a single sentence was longer than a post and was split mid-sentence; rewrite it")
            piece = ""
            for word in s.split(" "):
                for chunk in _chunks(word, budget):
                    cand = (piece + " " + chunk).strip()
                    if weighted(cand) <= budget:
                        piece = cand
                    else:
                        if piece:
                            out.append(piece)
                        piece = chunk
            if piece:
                cur = piece
            continue
        cand = (cur + " " + s).strip()
        if weighted(cand) <= budget:
            cur = cand
        else:
            out.append(cur)
            cur = s
    if cur:
        out.append(cur)
    return out


def build(text: str, number: bool = False, pack: bool = False, links_last: bool = False) -> Dict[str, object]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    warnings: List[str] = []
    if not text:
        raise ValueError("empty draft")
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    # Pull links out of the body.
    links: List[str] = []
    label: Optional[str] = None
    cleaned: List[str] = []
    for i, p in enumerate(paras):
        spans = xcount._url_spans(p)
        if spans:
            pieces, last = [], 0
            for a, b in spans:
                links.append(p[a:b])
                pieces.append(p[last:a])
                last = b
            pieces.append(p[last:])
            q = re.sub(r"[ \t]{2,}", " ", "".join(pieces)).strip()
            q = re.sub(r"\s+([,.;:!?])", r"\1", q)
            if re.fullmatch(r"[\s.,;:!?_()\[\]\-\u2013\u2014]*", q):
                continue
            if q.endswith(":") and label is None:
                label = q
                continue
            if re.search(r"(here|below|link|at|on|via)\s*[:.]?\s*$", q, re.I):
                warnings.append(f"paragraph {i + 1}: a link was removed and the sentence may now dangle; check it reads on its own")
            cleaned.append(q)
        else:
            cleaned.append(p)
    if not cleaned and links:
        raise ValueError("draft contains only links; nothing to thread")
    urls = "\n".join(dict.fromkeys(links))
    # The FIRST REPLY block carries the introducing line if there was one, else just the URLs
    # (same shape as postscore.py --split-link). Only --links-last needs a label inside the thread.
    link_line = ((label + "\n" + urls) if label else urls) if links else ""
    reserve = 8 if number else 0     # room for "12/12 "
    budget = LIMIT - reserve
    posts: List[str] = []
    for p in cleaned:
        pieces = [p] if weighted(p) <= budget else split_long(p, budget, warnings)
        for piece in pieces:
            if pack and posts and weighted(posts[-1] + "\n\n" + piece) <= budget and not posts[-1].endswith(("?", ":")):
                posts[-1] = posts[-1] + "\n\n" + piece
            else:
                posts.append(piece)
    first_reply = ""
    if link_line and links_last:
        if not label:
            link_line = "Links:\n" + link_line
        if posts and weighted(posts[-1] + "\n\n" + link_line) <= budget:
            posts[-1] = posts[-1] + "\n\n" + link_line
        else:
            posts.append(link_line)
    elif link_line:
        first_reply = link_line
        if weighted(first_reply) > LIMIT:
            warnings.append(f"the FIRST REPLY block is over {LIMIT}; use fewer links")
    if number and len(posts) > 1:
        n = len(posts)
        posts = [f"{i}/{n} {p}" for i, p in enumerate(posts, 1)]
    counts = [weighted(p) for p in posts]
    if len(posts) == 1:
        warnings.append("this fits in one post. Post it as one; a one-post thread is just a post")
    if len(posts) > 12:
        warnings.append(f"{len(posts)} posts. Long threads lose readers; consider cutting to the strongest ones")
    if posts:
        hook = postscore.check_hook(re.sub(r"^\d+/\d+ ", "", posts[0]))
        for note in hook[2]:
            warnings.append(f"hook post: {note}")
        if hook[0] < 55:
            warnings.append(f"hook post scores {hook[0]:.0f}/100; the first post decides whether anyone opens the thread")
    over = [i + 1 for i, c in enumerate(counts) if c > LIMIT]
    if over:
        warnings.append(f"post(s) {over} are over {LIMIT}")
    if postscore.find_bait("\n".join(posts)):
        warnings.append("engagement bait found in the thread (also an Original Content Rewards ineligibility problem)")
    return {"posts": posts, "weighted": counts, "limit": LIMIT, "links_moved": len(links),
            "first_reply": first_reply or None, "warnings": warnings}


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return data.decode("utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Split a long draft into thread posts.")
    ap.add_argument("input", help="draft file, or - for stdin")
    ap.add_argument("--number", action="store_true", help="prefix posts with i/N")
    ap.add_argument("--pack", action="store_true", help="merge short paragraphs into one post")
    ap.add_argument("--links-last", action="store_true", help="put links in the last post instead of a FIRST REPLY block")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        res = build(read_input(args.input), number=args.number, pack=args.pack, links_last=args.links_last)
    except (OSError, ValueError) as exc:
        print(f"thread: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        for i, (p, c) in enumerate(zip(res["posts"], res["weighted"]), 1):  # type: ignore[arg-type]
            print(f"--- post {i}/{len(res['posts'])}  ({c}/{LIMIT})")  # type: ignore[arg-type]
            print(p)
        print("---")
        if res["first_reply"]:
            print("FIRST REPLY (post it as a reply under post 1)")
            print(res["first_reply"])
            print("---")
        elif res["links_moved"]:
            print(f"{res['links_moved']} link(s) moved to the last post.")
        for w in res["warnings"]:  # type: ignore[union-attr]
            print(f"WARNING: {w}")
    return 1 if res["warnings"] else 0


if __name__ == "__main__":
    sys.exit(main())
