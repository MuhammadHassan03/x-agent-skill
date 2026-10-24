#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""detect.py - a five-check panel scoring how machine-written a draft looks.

Five local heuristics modelled on signals public AI-text detectors measure:
sentence-length variation, concreteness, stock vocabulary, typographic
fingerprint, and voice. Everything is computed on your machine from the text.
Nothing is uploaded.

What this is NOT: GPTZero, Originality, Copyleaks, Winston or Turnitin. It does
not call their APIs and cannot promise their verdicts. It also never says a
draft is "undetectable", because nothing here can know that.

X posts are short. A check that needs more text than the draft has returns
"too short" and is left out of the verdict instead of scoring a fake 50. With
fewer than three checks scored the verdict says so.

Each check is a HUMAN score 0-100, higher is better. PASS needs an overall of 70+
with no check under 55. Overall = 60% mean + 40% weakest check.

Usage
  python detect.py draft.txt
  python detect.py before.txt after.txt     compare two drafts
  python detect.py draft.txt --json
  python detect.py - < draft.txt

Exit codes: 0 PASS, 1 not PASS, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

SENT_RE = re.compile(r"[^.!?\n。！？]+[.!?。！？]*")
WORD_RE = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?")
CONTRACTIONS = re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.I)
PRONOUNS = re.compile(r"\b(i|me|my|mine|we|us|our|you|your)\b", re.I)
NUMBERS = re.compile(r"(?<!\w)\d[\d,.]*%?|\$\d")
PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b", re.M)

Result = Tuple[Optional[float], str]


def clamp(n: float) -> float:
    return max(0.0, min(100.0, n))


def scale(value: float, human: float, machine: float) -> float:
    if human == machine:
        return 50.0
    return clamp((value - machine) / (human - machine) * 100)


def sentences(text: str) -> List[str]:
    return [s.strip() for s in SENT_RE.findall(text) if len(s.split()) > 2]


def words(text: str) -> List[str]:
    return WORD_RE.findall(text)


def check_burstiness(text: str) -> Result:
    lens = [len(s.split()) for s in sentences(text)]
    if len(lens) < 4:
        return None, "too short to judge (needs 4+ sentences)"
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    return scale(cv, human=0.70, machine=0.22), f"variation {cv:.2f} across {len(lens)} sentences (want 0.55+)"


def check_specificity(text: str) -> Result:
    w = words(text)
    if len(w) < 12:
        return None, "too short to judge (needs 12+ words)"
    hits = len(NUMBERS.findall(text)) + len(set(PROPER.findall(text)))
    density = hits * 100 / len(w)
    return scale(density, human=6.0, machine=0.5), f"{hits} concrete markers, {density:.1f} per 100 words (want 4+)"


def _pat(find: str) -> "re.Pattern[str]":
    return re.compile(r"(?<![\w])" + re.escape(find).replace(r"\ ", r"\s+") + r"(?![\w])", re.I)


def check_slop(text: str, lex: Dict[str, Any]) -> Result:
    w = words(text)
    if not w:
        return None, "empty"
    hits, found = 0, []
    for entry in lex["words"] + lex["phrases"]:
        n = len(_pat(entry["find"]).findall(text))
        if n:
            hits += n
            found.append(entry["find"])
    density = hits * 100 / max(len(w), 8)
    detail = f"{hits} stock terms, {density:.1f} per 100 words"
    if found:
        detail += " (" + ", ".join(sorted(found)[:4]) + (", ..." if len(found) > 4 else "") + ")"
    return scale(density, human=0.0, machine=4.0), detail


def check_fingerprint(text: str) -> Result:
    if not text.strip():
        return None, "empty"
    invisible = sum(1 for c in text if unicodedata.category(c) == "Cf" and c != "‍")
    em = text.count("\u2014")
    curly = sum(text.count(c) for c in "‘’“”")
    ellip = text.count("…")
    hard = sum(text.count(c) for c in "   ")
    total = invisible * 4 + em * 2 + curly + ellip + hard
    per1k = total * 1000 / max(len(text), 200)
    detail = f"{invisible} invisible, {em} em dash, {curly} curly quote, {ellip} ellipsis, {hard} hard space"
    return scale(per1k, human=0.0, machine=12.0), detail


def check_voice(text: str, lex: Dict[str, Any]) -> Result:
    w = words(text)
    if len(w) < 12:
        return None, "too short to judge (needs 12+ words)"
    per100 = 100 / len(w)
    contractions = len(CONTRACTIONS.findall(text)) * per100
    person = len(PRONOUNS.findall(text)) * per100
    tells, names = 0, []
    for s in lex["structures"]:
        try:
            n = len(re.compile(s["regex"], re.M).findall(text))
        except re.error:
            continue
        if n:
            tells += n
            names.append(s["id"])
    score = (scale(contractions, human=3.0, machine=0.0) * 0.35
             + scale(person, human=8.0, machine=1.0) * 0.35
             + clamp(100 - tells * 22) * 0.30)
    detail = (f"{contractions:.1f} contractions, {person:.1f} personal pronouns per 100 words, "
              f"{tells} structural tell(s)")
    if names:
        detail += " [" + ", ".join(names[:4]) + "]"
    return clamp(score), detail


CHECKS = ["BURSTINESS", "SPECIFICITY", "SLOP DENSITY", "FINGERPRINT", "VOICE"]


def run(text: str, lex: Dict[str, Any]) -> Dict[str, Any]:
    text = text.replace("\r\n", "\n")
    res = {
        "BURSTINESS": check_burstiness(text),
        "SPECIFICITY": check_specificity(text),
        "SLOP DENSITY": check_slop(text, lex),
        "FINGERPRINT": check_fingerprint(text),
        "VOICE": check_voice(text, lex),
    }
    scored = [v[0] for v in res.values() if v[0] is not None]
    if not scored:
        return {"checks": res, "overall": None, "verdict": "NO TEXT", "scored": 0}
    overall = statistics.mean(scored) * 0.6 + min(scored) * 0.4
    if overall >= 70 and min(scored) >= 55:
        verdict = "PASS" if len(scored) >= 3 else "PASS (short text)"
    elif overall >= 50:
        verdict = "REVIEW"
    else:
        verdict = "FLAGGED"
    return {"checks": res, "overall": overall, "verdict": verdict, "scored": len(scored)}


def bar(score: float, width: int = 24) -> str:
    n = round(score / 100 * width)
    return "#" * n + "." * (width - n)


def render(r: Dict[str, Any], label: Optional[str] = None) -> None:
    title = "AI DETECTION PANEL" + (f"  -  {label}" if label else "")
    print("\n" + title)
    print("=" * max(len(title), 62))
    for name in CHECKS:
        score, detail = r["checks"][name]
        if score is None:
            print(f"  {name:<13} {'-' * 24}   n/a")
        else:
            print(f"  {name:<13} {bar(score)} {score:5.1f}")
        print(f"  {'':<13} {detail}")
    print("-" * 62)
    if r["overall"] is None:
        print("  No text to score.")
        return
    print(f"  {'HUMAN SCORE':<13} {bar(r['overall'])} {r['overall']:5.1f}   {r['verdict']}")
    print(f"  {r['scored']} of 5 checks scored.")
    if not r["verdict"].startswith("PASS"):
        scored = {k: v[0] for k, v in r["checks"].items() if v[0] is not None}
        print(f"\n  Weakest signal: {min(scored, key=scored.get)}. Fix that first.")
    print("")


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    # Windows PowerShell 5.1 writes UTF-16 for `>`; a BOM says so.
    return data.decode("utf-16" if data[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Score how machine-written a draft looks.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("compare", nargs="?", help="second file, to show before/after")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lexicon", default=LEX)
    args = ap.parse_args(argv)
    try:
        with open(args.lexicon, encoding="utf-8") as fh:
            lex = json.load(fh)
        targets = [(args.input, read_input(args.input))]
        if args.compare:
            targets.append((args.compare, read_input(args.compare)))
    except (OSError, ValueError) as exc:
        print(f"detect: {exc}", file=sys.stderr)
        return 2
    results = [run(t, lex) for _, t in targets]
    if args.json:
        payload = [{"source": n, "human_score": None if r["overall"] is None else round(r["overall"], 1),
                    "verdict": r["verdict"], "scored": r["scored"],
                    "checks": {k: {"score": None if v[0] is None else round(v[0], 1), "detail": v[1]}
                               for k, v in r["checks"].items()}}
                   for (n, _), r in zip(targets, results)]
        print(json.dumps(payload if args.compare else payload[0], indent=2))
    else:
        for (n, _), r in zip(targets, results):
            render(r, label=os.path.basename(n) if args.compare else None)
        if args.compare and all(r["overall"] is not None for r in results):
            a, b = results
            print(f"  {a['overall']:.1f} {a['verdict']}  ->  {b['overall']:.1f} {b['verdict']}   "
                  f"({b['overall'] - a['overall']:+.1f})\n")
    return 0 if results[-1]["verdict"].startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
