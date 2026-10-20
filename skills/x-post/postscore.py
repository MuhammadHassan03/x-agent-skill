#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""postscore.py - score a draft X post before you post it. Offline, heuristic.

Five checks, each 0-100, combined into one score:

  HOOK         the first line has to work alone. Penalises thread openers,
               throat-clearing, hashtags, and a first line that is too long or
               too short to land.
  SPECIFICITY  numbers, money, names, a first-person event. Unfilled
               {{placeholders}} do not count and are flagged: never post one.
  REPLY PULL   does the post give a reader something concrete to answer or
               disagree with. Replies are the heaviest everyday signal in the
               ranking weights (references/x-algorithm.md).
  LINK         a link in the body of a free-account post. Marked "observed, not
               coded": no link penalty exists in the open-sourced ranking
               parameters, but link posts from non-Premium accounts were
               observed to get less reach (Buffer, March 2025). Default move:
               put the link in the first reply.
  BAIT         "like and repost if", "follow for more", "RT if", and friends.
               Bait is a ranking risk AND an Original Content Rewards
               ineligibility problem, so it is flagged twice.

This is a set of local heuristics. It does not know how a post will perform.
Against a public tweet corpus the hook score separates weak hooks from strong
ones modestly; see the README measurement section for the numbers.

Usage
  python postscore.py draft.txt
  python postscore.py draft.txt --json
  python postscore.py --hooks hooks.txt        one candidate first line per line
  python postscore.py - < draft.txt
  python postscore.py draft.txt --premium      Premium account: link check relaxed

Exit codes: 0 scored (no hard flag), 1 hard flag raised, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xcount  # noqa: E402

HOOKS_JSON = os.path.join(HERE, "hooks.json")

PLACEHOLDER_RE = re.compile(r"\{\{[^}]*\}\}")
URL_RE = xcount.URL_RE
HASHTAG_RE = re.compile(r"(?<!\w)#\w+")
NUMBER_RE = re.compile(r"(?<![\w])(?:[$£€]\s?)?\d[\d,.]*(?:\s?(?:%|k|m|x|hrs?|days?|weeks?|months?|years?))?", re.I)
PROPER_RE = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-zA-Z]{2,}\b")
FIRST_PERSON_RE = re.compile(r"\b(i|i'm|i've|i'd|my|me|we|our)\b", re.I)
EVENT_RE = re.compile(r"\b(sent|shipped|lost|won|charged|paid|quit|launched|read|wrote|tried|asked|got|signed|closed|fired|hired|built|ran|spent)\b", re.I)

BAIT = [
    (r"\b(like|rt|retweet|repost)\s*(and|&|\+|or)\s*(like|rt|retweet|repost|follow)\b", "like/repost solicitation"),
    (r"\b(rt|retweet|repost|like)\s+if\b", "\"RT/like if\" bait"),
    (r"\bfollow (me )?for more\b", "\"follow for more\""),
    (r"\bfollow (me )?(and|&) (i'?ll|i will)\b", "follow-for-reward bait"),
    (r"\bcomment\s+[\"'“]?\w+[\"'”]?\s+(and|&|to)\s+(get|receive)\b", "comment-to-receive bait"),
    (r"\b(tag|mention) (someone|a friend|your)\b", "tag bait"),
    (r"\bdrop a (\W|\w)+ (if|below)\b", "drop-a-reaction bait"),
    (r"\bbookmark this\b", "\"bookmark this\" bait"),
    (r"\bshare (this )?if\b", "\"share if\" bait"),
    (r"\bturn on notifications\b|\bhit the bell\b", "notification bait"),
]
BAIT_RES = [(re.compile(p, re.I), name) for p, name in BAIT]

BAD_OPENERS = [
    (r"^\s*(a )?thread\b|\U0001F9F5|^\s*1\s*/\s*\d*\b", "thread opener as the hook"),
    (r"^\s*(here'?s why|let me explain|let'?s talk about|i want to talk about|story time)\b", "throat-clearing opener"),
    (r"^\s*(breaking|just in|big news|huge)\b", "news-bait opener"),
    (r"^\s*(this is huge|game.?changer|let that sink in|here'?s the kicker)\b", "stock hype opener"),
    (r"^\s*(unpopular opinion|hot take)\s*:?\s*$", "label with no claim"),
]
BAD_OPENER_RES = [(re.compile(p, re.I), name) for p, name in BAD_OPENERS]

QUESTION_RE = re.compile(r"\?")
INVITE_RE = re.compile(r"\b(what'?s your|how do you|do you|did you|have you|which (one|do)|tell me|curious (how|what|whether)|disagree|your (number|rate|process|experience))\b", re.I)
GENERIC_Q_RE = re.compile(r"^\s*(thoughts|agree|right|ideas|anyone|who else)\s*\?*\s*$", re.I)


def load_formulas() -> List[Tuple[int, str, "re.Pattern[str]"]]:
    try:
        with open(HOOKS_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    return [(h["id"], h["name"], re.compile(h["match"], re.I)) for h in data["hooks"]]


def formula_for(line: str) -> Optional[str]:
    for _id, name, pat in load_formulas():
        if pat.search(line.strip()):
            return name
    return None


def clamp(n: float) -> float:
    return max(0.0, min(100.0, n))


def first_line(text: str) -> str:
    for ln in text.splitlines():
        if ln.strip():
            return ln.strip()
    return ""


def check_hook(text: str) -> Tuple[float, str, List[str]]:
    line = first_line(text)
    notes: List[str] = []
    if not line:
        return 0.0, "empty", ["empty post"]
    plain = PLACEHOLDER_RE.sub("", line)
    w = xcount.count(plain)["weighted"]
    score = 70.0
    if w < 20:
        score -= 25
        notes.append(f"first line is only {w} weighted characters, too thin to land")
    elif w > 120:
        score -= min(30, (w - 120) * 0.4)
        notes.append(f"first line is {w} weighted characters; the hook should work in about 100")
    for pat, name in BAD_OPENER_RES:
        if pat.search(line):
            score -= 30
            notes.append(name)
    if HASHTAG_RE.search(line):
        score -= 15
        notes.append("hashtag in the first line")
    if NUMBER_RE.search(plain):
        score += 15
    if FIRST_PERSON_RE.search(plain) and EVENT_RE.search(plain):
        score += 10
    if formula_for(line):
        score += 5
    if re.search(r"[\U0001F300-\U0001FAFF]{2,}", line):
        score -= 10
        notes.append("emoji string in the first line")
    return clamp(score), f"{w} weighted characters", notes


def check_specificity(text: str) -> Tuple[float, str, List[str]]:
    notes: List[str] = []
    body = PLACEHOLDER_RE.sub(" ", URL_RE.sub(" ", text))
    words = re.findall(r"\w+", body)
    if not words:
        return 0.0, "no words", ["empty post"]
    nums = len(NUMBER_RE.findall(body))
    names = len(set(PROPER_RE.findall(body)))
    event = 1 if (FIRST_PERSON_RE.search(body) and EVENT_RE.search(body)) else 0
    markers = nums + names + event * 2
    density = markers * 100 / max(len(words), 1)
    score = clamp(density * 8)
    ph = PLACEHOLDER_RE.findall(text)
    if ph:
        notes.append(f"{len(ph)} unfilled placeholder(s): {', '.join(sorted(set(ph)))}. Supply the real value before posting")
    if len(words) < 6:
        score = min(score, 40)
    return score, f"{markers} concrete markers in {len(words)} words", notes


def check_reply_pull(text: str) -> Tuple[float, str, List[str]]:
    notes: List[str] = []
    body = URL_RE.sub(" ", text)
    score = 35.0
    q = QUESTION_RE.findall(body)
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    if q and not GENERIC_Q_RE.match(last):
        score += 30
        if last.endswith("?"):
            score += 10
    if GENERIC_Q_RE.match(last):
        score -= 10
        notes.append("closing question is generic (\"thoughts?\"); ask something answerable in one line")
    if INVITE_RE.search(body):
        score += 15
    if re.search(r"\b(wrong|disagree|overrated|myth|nobody|never|always|most people)\b", body, re.I):
        score += 10
    if not q and not INVITE_RE.search(body):
        notes.append("nothing for a reader to answer or push back on")
    return clamp(score), ("question present" if q else "statement only"), notes


def check_link(text: str, premium: bool) -> Tuple[float, str, List[str]]:
    notes: List[str] = []
    n = xcount.count(text)["urls"]
    if n == 0:
        return 100.0, "no link in body", notes
    if premium:
        return 85.0, f"{n} link(s) in body (Premium: observed link suppression applies to non-Premium)", notes
    notes.append("link in the body of a free-account post. Observed, not coded: "
                 "no link penalty exists in the ranking parameters, but link posts from "
                 "non-Premium accounts were observed to reach less (Buffer, 18.8M posts, March 2025). "
                 "Move it to the first reply")
    return 35.0, f"{n} link(s) in body", notes


def find_bait(text: str) -> List[str]:
    found = []
    for pat, name in BAIT_RES:
        if pat.search(text):
            found.append(name)
    return found


def check_bait(text: str) -> Tuple[float, str, List[str]]:
    found = find_bait(text)
    if not found:
        return 100.0, "none", []
    notes = [f"engagement bait: {', '.join(found)}. This is also an Original Content Rewards "
             "ineligibility problem (engagement solicitation). Remove it"]
    return 0.0, ", ".join(found), notes


WEIGHTS = {"HOOK": 0.25, "SPECIFICITY": 0.25, "REPLY PULL": 0.20, "LINK": 0.15, "BAIT": 0.15}


def score(text: str, premium: bool = False) -> Dict[str, object]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    checks = {
        "HOOK": check_hook(text),
        "SPECIFICITY": check_specificity(text),
        "REPLY PULL": check_reply_pull(text),
        "LINK": check_link(text, premium),
        "BAIT": check_bait(text),
    }
    total = sum(checks[k][0] * WEIGHTS[k] for k in WEIGHTS)
    cnt = xcount.count(text, premium)
    hard: List[str] = []
    if PLACEHOLDER_RE.search(text):
        hard.append("unfilled {{placeholder}}")
    if find_bait(text):
        hard.append("engagement bait")
    if not cnt["fits"]:
        hard.append(f"over the {cnt['limit']} limit by {cnt['over']}")
    if len(HASHTAG_RE.findall(text)) > 2:
        hard.append("hashtag wall (more than 2)")
    verdict = "STRONG" if total >= 75 else "OK" if total >= 55 else "WEAK"
    if hard:
        verdict = "BLOCKED" if verdict != "WEAK" else "WEAK"
    return {
        "score": round(total, 1),
        "verdict": verdict,
        "hard_flags": hard,
        "formula": formula_for(first_line(text)),
        "length": {"weighted": cnt["weighted"], "limit": cnt["limit"], "fits": cnt["fits"]},
        "checks": {k: {"score": round(v[0], 1), "detail": v[1], "notes": v[2]} for k, v in checks.items()},
    }


def score_hook_line(line: str) -> Dict[str, object]:
    h = check_hook(line)
    s = check_specificity(line)
    b = check_bait(line)
    total = h[0] * 0.6 + s[0] * 0.4
    if find_bait(line):
        total = min(total, 20.0)
    return {"hook": line, "score": round(total, 1), "formula": formula_for(line),
            "notes": h[2] + s[2] + b[2]}


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return data.decode("utf-8-sig")


def bar(v: float, width: int = 20) -> str:
    n = round(v / 100 * width)
    return "#" * n + "." * (width - n)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Score a draft X post offline.")
    ap.add_argument("input", nargs="?", help="draft file, or - for stdin")
    ap.add_argument("--hooks", metavar="FILE", help="rank candidate first lines, one per line")
    ap.add_argument("--premium", action="store_true", help="account is Premium")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.hooks:
            lines = [ln.strip() for ln in read_input(args.hooks).splitlines() if ln.strip()]
            if not lines:
                raise ValueError("no hooks in file")
            ranked = sorted((score_hook_line(ln) for ln in lines), key=lambda r: -r["score"])  # type: ignore[arg-type,return-value]
            if args.json:
                print(json.dumps(ranked, indent=2, ensure_ascii=False))
            else:
                for i, r in enumerate(ranked, 1):
                    print(f"{i}. {r['score']:5.1f}  {r['formula'] or 'no formula matched':<24} {r['hook']}")
                    for n in r["notes"]:  # type: ignore[union-attr]
                        print(f"        - {n}")
                if ranked[0]["score"] < 50:  # type: ignore[operator]
                    print("\nBest hook is under 50. You do not have the hook yet; editing will not fix that.")
            return 0
        if not args.input:
            ap.error("give a draft file, - for stdin, or --hooks FILE")
        text = read_input(args.input)
        if not text.strip():
            raise ValueError("empty input")
    except (OSError, ValueError) as exc:
        print(f"postscore: {exc}", file=sys.stderr)
        return 2
    res = score(text, premium=args.premium)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        L = res["length"]
        print(f"\nPOST SCORE  {res['score']:.1f}  {res['verdict']}"
              f"   ({L['weighted']}/{L['limit']} weighted)")  # type: ignore[index]
        if res["formula"]:
            print(f"hook formula: {res['formula']}")
        print("-" * 64)
        for name, c in res["checks"].items():  # type: ignore[union-attr]
            print(f"  {name:<12} {bar(c['score'])} {c['score']:5.1f}  {c['detail']}")
            for n in c["notes"]:
                print(f"               - {n}")
        if res["hard_flags"]:
            print("\nBLOCKING: " + "; ".join(res["hard_flags"]))  # type: ignore[arg-type]
        print("")
    return 1 if res["hard_flags"] else 0


if __name__ == "__main__":
    sys.exit(main())
