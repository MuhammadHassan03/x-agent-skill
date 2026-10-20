#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""humanize.py - strip the machine fingerprint out of a draft. Offline.

Four passes, in this order:

  1. INVISIBLE   delete characters a keyboard does not produce: zero-width
                 spaces and joiners, word joiners, soft hyphens, BOMs, bidi
                 controls, Unicode tag characters; normalise non-breaking and
                 narrow spaces. A zero-width joiner that glues an emoji sequence
                 (a family, a skin tone) is kept, because deleting it breaks the
                 emoji.
  2. TYPOGRAPHIC em dash -> comma, en dash -> hyphen, curly quotes -> straight,
                 ellipsis -> three dots, bullet -> hyphen, arrow -> ->.
  3. LEXICAL     replace the slop lexicon in slop.json (stock AI vocabulary plus
                 X-specific phrases like "let that sink in") with plain words,
                 keeping capitalisation and leaving URLs, @mentions and
                 $cashtags untouched.
  4. STRUCTURAL  FLAGGED, never rewritten: "not just X, it's Y", triads,
                 hashtag walls, numbered-emoji bullets, engagement bait. Changing
                 the shape of a sentence needs judgement, so that part is yours.

It never claims a draft is undetectable. See detect.py for what is measured.

Usage
  python humanize.py draft.txt
  python humanize.py draft.txt --report
  python humanize.py draft.txt -o clean.txt
  python humanize.py draft.txt --json
  python humanize.py - < draft.txt

Exit codes: 0 ok, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

PROTECT_RE = re.compile(r"https?://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.-]+|(?<![\w])[@$][A-Za-z_][\w]*")
SENT_RE = re.compile(r"[^.!?\n。！？]+[.!?。！？]*")
EMOJI_CH = "\U0001F000-\U0001FAFF☀-➿⬀-⯿️"
ZWJ_GLUE_RE = re.compile("(?<=[" + EMOJI_CH + "])‍(?=[" + EMOJI_CH + "])")


def load_lexicon(path: str = LEX) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _cp(spec: str) -> Union[int, Tuple[int, int]]:
    if "-" in spec:
        a, b = spec.split("-")
        return (int(a[2:], 16), int(b[2:], 16))
    return int(spec[2:], 16)


def protect(text: str) -> Tuple[str, List[str]]:
    found: List[str] = []

    def stash(m: "re.Match[str]") -> str:
        found.append(m.group(0))
        return f"\x00P{len(found) - 1}\x00"

    return PROTECT_RE.sub(stash, text), found


def restore(text: str, found: List[str]) -> str:
    for i, s in enumerate(found):
        text = text.replace(f"\x00P{i}\x00", s)
    return text


def pass_invisible(text: str, lex: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    hits: List[Dict[str, Any]] = []
    for entry in lex["invisible"]:
        cp = _cp(entry["cp"])
        if isinstance(cp, tuple):
            pattern = "[" + re.escape(chr(cp[0])) + "-" + re.escape(chr(cp[1])) + "]"
        else:
            pattern = re.escape(chr(cp))
        action = entry["action"]
        if action == "delete-outside-emoji":
            glue = [m.start() for m in ZWJ_GLUE_RE.finditer(text)]
            n = len(re.findall(pattern, text)) - len(glue)
            if n > 0:
                keep = set(glue)
                text = "".join(c for i, c in enumerate(text) if c != "‍" or i in keep)
                hits.append({"name": entry["cp"] + " ZERO WIDTH JOINER", "count": n, "action": "delete"})
            continue
        n = len(re.findall(pattern, text))
        if n:
            hits.append({"name": entry["cp"] + " " + entry["name"], "count": n, "action": action})
            text = re.sub(pattern, "" if action == "delete" else " ", text)
    stray = [c for c in text if unicodedata.category(c) == "Cf" and c != "‍"]
    if stray:
        hits.append({"name": "other invisible format chars", "count": len(stray), "action": "delete"})
        text = "".join(c for c in text if c == "‍" or unicodedata.category(c) != "Cf")
    return text, hits


def pass_typographic(text: str, lex: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    hits: List[Dict[str, Any]] = []
    for entry in lex["typographic"]:
        ch = entry["from"]
        n = text.count(ch)
        if not n:
            continue
        hits.append({"name": f"{ch.encode('unicode_escape').decode()} {entry['name']}", "count": n,
                     "to": entry["to"].strip() or "(space)"})
        if ch == "\u2014":
            text = re.sub(r"\s*\u2014\s*", ", ", text)
        elif ch == "–":
            text = re.sub(r"(?<=\d)\s*–\s*(?=\d)", "-", text)
            text = re.sub(r"\s+–\s+", ", ", text)
            text = text.replace("–", "-")
        else:
            text = text.replace(ch, entry["to"])
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)
    text = re.sub(r",[ \t]*\n", "\n", text)
    return text, hits


def _match_case(src: str, repl: str) -> str:
    if not repl:
        return repl
    if src.isupper() and len(src) > 1:
        return repl.upper()
    if src[0].isupper():
        return repl[0].upper() + repl[1:]
    return repl


def _pattern(find: str) -> "re.Pattern[str]":
    body = re.escape(find).replace(r"\ ", r"\s+")
    return re.compile(r"(?<![\w])" + body + r"(?![\w])", re.IGNORECASE)


def pass_lexical(text: str, lex: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    hits: List[Dict[str, Any]] = []
    entries = sorted(lex["phrases"] + lex["words"], key=lambda e: len(e["find"]), reverse=True)
    for entry in entries:
        pat = _pattern(entry["find"])
        found = pat.findall(text)
        if not found:
            continue
        hits.append({"find": entry["find"], "replace": entry["replace"] or "(deleted)",
                     "count": len(found), "family": entry["family"]})
        text = pat.sub(lambda m: _match_case(m.group(0), entry["replace"]), text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^[ \t]*(?:[,.;:]+[ \t]*)+", "", text)
    text = re.sub(r"(?m)^[ \t](?=\S)", "", text)
    text = re.sub(r"[ \t]+([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)
    text = text.replace("...", "\x00ELL\x00")
    text = re.sub(r"\.[ \t]*\.+", ".", text)
    text = re.sub(r"([!?])[ \t]*\.", r"\1", text)
    text = text.replace("\x00ELL\x00", "...")
    text = re.sub(r"(?m)(^|(?<=[.!?]) )(?:and|or|but|so)[ \t]*[.!?]+[ \t]*", r"\1", text)  # orphan "And!"
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r",\s*(also|so|still)\s*,\s*",
                  lambda m: ". " + m.group(1).capitalize() + ", ", text)
    return text, hits


def scan_structures(text: str, lex: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    for s in lex["structures"]:
        try:
            pat = re.compile(s["regex"], re.MULTILINE)
        except re.error:
            continue
        n = len(pat.findall(text))
        if n:
            flags.append({"id": s["id"], "name": s["name"], "count": n, "fix": s["fix"]})
    lens = [len(s.split()) for s in SENT_RE.findall(text) if len(s.split()) > 2]
    if len(lens) >= 5:
        mean = sum(lens) / len(lens)
        cv = ((sum((n - mean) ** 2 for n in lens) / len(lens)) ** 0.5) / mean if mean else 0
        if cv < 0.30:
            flags.append({"id": "uniform", "name": f"Uniform sentence length (variation {cv:.2f})",
                          "count": len(lens), "fix": "Break one sentence in half. Let another run long."})
    return flags


def restore_capitals(original: str, text: str) -> str:
    """Re-capitalise a sentence start after a deleted opener, but only for
    writers who capitalise in the first place. A lower-case voice is a style."""
    starts = re.findall(r"(?:^|[.!?]\s+|\n)\s*([A-Za-z])", original)
    if not starts or sum(1 for c in starts if c.isupper()) * 2 < len(starts):
        return text
    return re.sub(r"(?:^|(?<=[.!?] )|(?<=\n))([a-z])", lambda m: m.group(1).upper(), text)


def humanize(text: str, lex: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    original = text
    text, held = protect(text)
    text, inv = pass_invisible(text, lex)
    text, typo = pass_typographic(text, lex)
    text, lexi = pass_lexical(text, lex)
    text = restore_capitals(original, text)
    text = restore(text, held)
    structures = scan_structures(text, lex)
    return text.strip() + "\n", {"invisible": inv, "typographic": typo, "lexical": lexi,
                                  "structures": structures}


def render_report(report: Dict[str, Any], out: Any = sys.stderr) -> None:
    def head(t: str) -> None:
        print(f"\n{t}\n" + "-" * len(t), file=out)

    total = sum(h["count"] for k in ("invisible", "typographic", "lexical") for h in report[k])
    head("HUMANIZE REPORT")
    print(f"{total} machine artefacts removed, {len(report['structures'])} structural tells flagged for rewrite", file=out)
    if report["invisible"]:
        head("1. INVISIBLE CHARACTERS")
        for h in report["invisible"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['action']}", file=out)
    if report["typographic"]:
        head("2. TYPOGRAPHY")
        for h in report["typographic"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['to']}", file=out)
    if report["lexical"]:
        head("3. SLOP LEXICON")
        for h in report["lexical"]:
            print(f"  {h['count']:>3}x  {h['find']}  -> {h['replace']}   [{h['family']}]", file=out)
    if report["structures"]:
        head("4. STRUCTURAL TELLS  (not auto-fixed, rewrite these yourself)")
        for h in report["structures"]:
            print(f"  {h['count']:>3}x  {h['name']}\n        {h['fix']}", file=out)
    if not any(report.values()):
        head("CLEAN")
        print("  Nothing to strip.", file=out)
    print("", file=out)


def read_input(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return data.decode("utf-8-sig")


def main(argv: Optional[List[str]] = None) -> int:
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Strip the machine fingerprint out of a draft.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("-o", "--out", help="write cleaned text here instead of stdout")
    ap.add_argument("--report", action="store_true", help="print what changed, to stderr")
    ap.add_argument("--json", action="store_true", help="emit {text, report} as JSON")
    ap.add_argument("--lexicon", default=LEX, help="path to slop.json")
    args = ap.parse_args(argv)
    try:
        raw = read_input(args.input)
        lex = load_lexicon(args.lexicon)
    except (OSError, ValueError) as exc:
        print(f"humanize: {exc}", file=sys.stderr)
        return 2
    clean, report = humanize(raw, lex)
    if args.json:
        print(json.dumps({"text": clean, "report": report}, indent=2, ensure_ascii=False))
        return 0
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(clean)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(clean.encode("utf-8"))
    if args.report:
        render_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
