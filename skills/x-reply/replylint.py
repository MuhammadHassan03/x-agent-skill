#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""replylint.py - lint a draft reply against an approximation of X's 0-3 rubric.

What the open-sourced code shows (xai-org/x-algorithm, grox/flows/reply_spam,
commit pinned in references/x-algorithm.md): replies under a post whose parent or
root account has more than 250,000 followers get a 0-3 score plus a short reason
from a Grok model. The prompt that defines the rubric is deliberately NOT
published ("to reduce gameability"). So the bands below are this repo's
approximation of an unpublished rubric, not a copy of it:

  0  spam-like or empty: generic praise only, emoji only, a link drop, pure
     self-promotion, or a repeat of the parent
  1  low value: on topic but adds nothing the parent did not say
  2  decent: on topic and either specific or informative
  3  strong: on topic, specific, and adds information, experience or a real
     counter-point

Under smaller accounts the reply goes through a different, spam-oriented
classifier instead of the 0-3 ranker. Writing for the rubric helps both.

Checks (each pass/fail, with a reason):
  generic praise    "Great point", "This!", "So true", "100%", "Well said"
  on topic          shares content words with the parent (when --parent given)
  specific          a number, a name, or a first-person event
  adds information  a reason, an example, or a counter-point beyond agreement
  length sane       about 40 to 280 weighted characters
  promo / links     a link or "check out my" in a reply
  hashtags / emoji  hashtags in a reply, emoji-only replies
  self-reply chain  --prior-replies-in-thread N: you are about to reply to your
                    own reply in a thread under someone else's post. In the
                    open-sourced code a multi-step reply-spam filter looks at
                    threads where the replier is replying to themselves, under
                    a root account with 1,000+ followers; when 2 or more of
                    the replier's posts are flagged, their reply ranking score
                    is set to 0. A single reply is never flagged. Edit your
                    first reply instead of stacking a second.

It never decides for you. It tells you which band the draft is likely in and
what to fix. It does not and cannot know what X will score.

Usage
  python replylint.py reply.txt --parent parent.txt
  python replylint.py reply.txt --parent parent.txt --json
  python replylint.py reply.txt --prior-replies-in-thread 1
  python replylint.py - < reply.txt

Exit codes: 0 band 2 or 3, 1 band 0 or 1, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Set

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "x-post"))
import xcount  # noqa: E402

GENERIC_PRAISE = re.compile(
    r"^\W*(great|good|nice|excellent|amazing|awesome|fantastic|brilliant|solid|powerful|love)\s+"
    r"(point|post|thread|take|share|content|insight|advice|one|stuff|read|breakdown)\W*$"
    r"|^\W*(this|so true|100%|facts|exactly|agreed|well said|couldn'?t agree more|spot on|"
    r"you'?re (so )?right|this is (so )?(true|gold|great)|love this|needed this|big if true|underrated)\W*$",
    re.I,
)
PRAISE_OPENER = re.compile(
    r"^\W*(great|good|nice|excellent|amazing|awesome|fantastic|brilliant)\s+(point|post|thread|take|insight)"
    r"|^\W*(love this|so true|well said|this\b|exactly\b|100%|facts\b)",
    re.I,
)
PROMO = re.compile(r"\b(check out|dm me|link in (my )?bio|follow me|my (newsletter|course|thread|profile)|subscribe)\b", re.I)
HASHTAG = re.compile(r"(?<!\w)#\w+")
NUMBER = re.compile(r"(?<!\w)(?:[$£€]\s?)?\d[\d,.]*(?:\s?(?:%|k|m|x))?")
PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-zA-Z]{2,}\b")
FIRST_PERSON_EVENT = re.compile(
    r"\b(i|we|my)\b.{0,40}\b(tried|ran|sent|lost|built|paid|charged|switched|quit|saw|found|"
    r"measured|tested|shipped|hired|fired|learned|noticed|had|did|used)\b", re.I)
REASON = re.compile(r"\b(because|since|which is why|the reason|so that|that'?s why|instead|however|but|unless|except|"
                    r"if you|when you|the catch|the trade-?off|for example|for instance|e\.g\.)\b", re.I)
EMOJI_ONLY = re.compile(r"^[\W_\U0001F300-\U0001FAFF☀-➿]+$")
STOP = set("the a an and or but if of to in on for with at by from as is are was were be been it its this that these those "
           "i you he she we they them my your our their not no yes so do does did have has had will would can could should "
           "just very really more most than then there here what which who whom how why when where about into over because since while after before also got get".split())


# Scripts written without spaces between words: match on character bigrams instead of whole runs.
NO_SPACE_SCRIPT = re.compile("[\u0e00-\u0e7f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]")


def words(text: str) -> List[str]:
    """Lower-cased word tokens in any script. Spaceless scripts (CJK, Thai) yield character bigrams."""
    out: List[str] = []
    for tok in re.findall(r"[^\W_]+(?:['\u2019][^\W_]+)?", text.lower()):
        if NO_SPACE_SCRIPT.search(tok):
            out.extend([tok] if len(tok) < 2 else [tok[i:i + 2] for i in range(len(tok) - 1)])
        else:
            out.append(tok)
    return out


def content(text: str) -> Set[str]:
    return {w for w in words(text) if w not in STOP and (len(w) > 2 or NO_SPACE_SCRIPT.search(w))}


def lint(reply: str, parent: Optional[str] = None, prior_in_thread: int = 0) -> Dict[str, object]:
    reply = reply.replace("\r\n", "\n").strip()
    parent = parent.replace("\r\n", "\n").strip() if parent else None
    w = int(xcount.count(reply)["weighted"])
    plain = xcount.URL_RE.sub(" ", reply)
    checks: List[Dict[str, object]] = []

    def add(name: str, ok: bool, detail: str, fatal: bool = False) -> None:
        checks.append({"check": name, "pass": ok, "detail": detail, "fatal": fatal and not ok})

    generic = bool(GENERIC_PRAISE.match(plain.strip())) or (
        bool(PRAISE_OPENER.match(plain)) and len(content(plain)) <= 4)
    add("no generic praise", not generic,
        "reads as generic praise or agreement with nothing added" if generic else "ok", fatal=True)
    opener = bool(PRAISE_OPENER.match(plain)) and not generic
    add("no praise opener", not opener,
        "opens with a compliment; cut to the substance, the compliment adds nothing" if opener else "ok")

    emoji_only = bool(EMOJI_ONLY.match(plain)) or not words(plain)
    add("has words", not emoji_only, "emoji or symbols only" if emoji_only else "ok", fatal=True)

    if parent:
        shared = content(plain) & content(parent)
        ratio = len(shared) / max(len(content(plain)), 1)
        on_topic = len(shared) >= 1
        repeat = len(content(plain)) >= 3 and ratio >= 0.8
        add("on topic", on_topic, f"shares {sorted(shared)[:5]} with the parent" if on_topic
            else "shares no content words with the parent post", fatal=True)
        add("not a restatement", not repeat,
            "only repeats words from the parent; add something it did not say" if repeat else "ok")
    else:
        ratio = 0.0
        add("on topic", True, "not checked: pass --parent with the post you are replying to")

    specific = bool(NUMBER.search(plain) or len(set(PROPER.findall(plain))) >= 1 or FIRST_PERSON_EVENT.search(plain))
    add("specific", specific, "has a number, a name or a first-person event" if specific
        else "no number, name or concrete event")
    adds = bool(REASON.search(plain) or FIRST_PERSON_EVENT.search(plain) or NUMBER.search(plain))
    add("adds information", adds and not generic,
        "gives a reason, an example, a number or a counter-point" if adds and not generic
        else "agreement or restatement only; give a reason, an example or a counter-point")

    ok_len = 40 <= w <= 280
    add("length sane", ok_len, f"{w} weighted characters" + ("" if ok_len else "; aim for roughly 40 to 280"))

    has_link = bool(xcount.count(reply)["urls"])
    promo = bool(PROMO.search(plain))
    add("no link or promo", not (has_link or promo),
        "a link or self-promotion in a reply to someone else's post reads as spam" if (has_link or promo) else "ok",
        fatal=promo and has_link)
    add("no hashtags", not HASHTAG.search(plain), "hashtags in a reply" if HASHTAG.search(plain) else "ok")

    chain = prior_in_thread >= 1
    add("no self-reply chain", not chain,
        f"you already replied {prior_in_thread}x in this thread; stacking a second reply is the shape the multi-step reply-spam filter looks for. Edit your first reply instead"
        if chain else "ok", fatal=True)

    fatal = any(c["fatal"] for c in checks)
    if fatal:
        band = 0
    else:
        passed = {c["check"]: c["pass"] for c in checks}
        band = 1
        if passed["on topic"] and passed["adds information"] and passed["length sane"]:
            band = 2
        if band == 2 and passed["specific"] and passed["no praise opener"] and passed["no link or promo"] \
                and passed.get("not a restatement", True) and passed["no hashtags"]:
            band = 3
    return {"band": band, "weighted": w, "checks": checks,
            "fix": [str(c["detail"]) for c in checks if not c["pass"]]}


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return data.decode("utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Lint a draft reply against a 0-3 rubric approximation.")
    ap.add_argument("input", help="reply file, or - for stdin")
    ap.add_argument("--parent", help="file with the post you are replying to")
    ap.add_argument("--prior-replies-in-thread", type=int, default=0, metavar="N",
                    help="how many replies you already posted in this thread")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        reply = read_input(args.input)
        parent = read_input(args.parent) if args.parent else None
        if not reply.strip():
            raise ValueError("empty reply")
        if args.prior_replies_in_thread < 0:
            raise ValueError("--prior-replies-in-thread must be 0 or more")
    except (OSError, ValueError) as exc:
        print(f"replylint: {exc}", file=sys.stderr)
        return 2
    res = lint(reply, parent, args.prior_replies_in_thread)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        names = {0: "SPAM-LIKE", 1: "LOW VALUE", 2: "DECENT", 3: "STRONG"}
        print(f"\nREPLY BAND {res['band']}/3  {names[res['band']]}   ({res['weighted']} weighted)")  # type: ignore[index]
        print("-" * 56)
        for c in res["checks"]:  # type: ignore[union-attr]
            mark = "pass" if c["pass"] else ("FAIL" if c["fatal"] else "weak")
            print(f"  {mark:<5} {c['check']:<20} {c['detail']}")
        print("\nApproximation of a rubric X does not publish. Treat it as a checklist, not a prediction.\n")
    return 0 if res["band"] >= 2 else 1  # type: ignore[operator]


if __name__ == "__main__":
    sys.exit(main())
