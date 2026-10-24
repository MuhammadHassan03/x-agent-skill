#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""algo_watch.py - track changes to X's open-sourced ranking parameters. Maintainer tool.

This is NOT one of the plugin's skill tools. Those make no network calls. This script
fetches exactly one public file (home-mixer/params/param.rs from github.com/xai-org/x-algorithm,
at the default branch) and is meant to run in CI or on a maintainer's machine.

What it does
  1. Finds the default branch and the latest commit that touched the file (the pin), through the
     GitHub API, then downloads the file at that commit.
  2. Parses every `param!(Name, type, "key", default)` into JSON (weights and all other parameters).
  3. Compares with references/weights.json and writes the changes.
  4. With --write it updates references/weights.json, references/x-algorithm.md (commit, dates and
     the weights table, through skills/x-algo/weights.py), prepends an entry to
     references/ALGO-CHANGELOG.md and refreshes the "Algorithm changelog" block in README.md.
  5. With --diff-out it also writes the dated diff as markdown, for a commit message.

It commits nothing itself. The workflow commits the result to the default branch (no pull request).

Exit codes
  0   nothing changed
  10  changes found (and written, with --write)
  2   failure: the file moved, the download failed, or the parse looks wrong. The message on stderr
      starts with "FAILURE:" and is what the workflow puts in an issue.
  3   validation failed: a weight key from the previous weights.json is gone, a weight is not numeric,
      or a weight moved by more than 10x (to or from zero and sign flips count). Nothing is written;
      the raw diff goes to --diff-out and the workflow opens an issue instead of committing.

Usage
  python tools/algo_watch.py                       # check only, print the diff
  python tools/algo_watch.py --write --diff-out /tmp/algo-diff.md
  python tools/algo_watch.py --param-file param.rs --commit 74d49a4 --date 2026-10-20 --write   # offline
  python tools/algo_watch.py --json

Set GITHUB_TOKEN to raise the GitHub API rate limit (optional).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "skills", "x-algo"))
import weights as weights_tool  # noqa: E402

REPO = "xai-org/x-algorithm"
PATH = "home-mixer/params/param.rs"
SOURCE_URL = f"https://github.com/{REPO}/blob/main/{PATH}"
MIN_PARAMS = 50      # the file has ~190; far fewer means the format changed
MIN_WEIGHTS = 5
PARAM_RE = re.compile(r"param!\(\s*(\w+)\s*,\s*((?:[^,<\"]|<[^<>]*>)+?)\s*,\s*\"([^\"]+)\"\s*,\s*(.*?)\)\s*;", re.S)
BLOCK_RE = re.compile(r"(?m)^param!\(")
NUM_RE = re.compile(r"-?[0-9][0-9_]*(?:\.[0-9_]+)?")
START = "<!-- algo-changelog:start -->"
END = "<!-- algo-changelog:end -->"


class WatchError(Exception):
    """A failure the workflow should turn into an issue."""


class ValidationFailed(Exception):
    """The new parse looks unsafe to commit. Nothing is written; the workflow opens an issue."""

    def __init__(self, problems: List[str], diff: str):
        super().__init__("; ".join(problems))
        self.problems = problems
        self.diff = diff


MAX_MOVE = 10.0


def is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def moved_too_far(before: float, after: float) -> bool:
    """True when a weight moved by more than 10x in one run.

    Going to or from zero, or flipping sign, counts: the ratio is undefined or negative, and that is
    exactly the kind of jump a human should look at before it lands on the default branch.
    """
    if before == after:
        return False
    if before == 0 or after == 0 or (before < 0) != (after < 0):
        return True
    ratio = abs(after / before)
    return ratio > MAX_MOVE or ratio < 1 / MAX_MOVE


def validate_update(prev: Optional[Dict[str, Dict[str, Any]]], new: Dict[str, Dict[str, Any]]) -> List[str]:
    """Checks that must pass before any commit. Returns the list of problems (empty means safe).

    1. every weight key present in the previous weights.json is still present;
    2. every weight value is numeric;
    3. no single weight moves by more than 10x in one run.
    """
    problems: List[str] = []
    for name, v in sorted(new.items()):
        if is_weight(name) and not is_number(v["value"]):
            problems.append(f"weight {name} is not numeric: {v['value']!r}")
    if prev:
        for name in sorted(n for n in prev if is_weight(n)):
            if name not in new:
                problems.append(f"weight key missing from the new parse: {name}")
                continue
            a, b = prev[name]["value"], new[name]["value"]
            if is_number(a) and is_number(b) and moved_too_far(a, b):
                problems.append(f"weight {name} moved from {fmt(a)} to {fmt(b)} (more than {MAX_MOVE:g}x in one run)")
    return problems


def parse_all(text: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for m in PARAM_RE.finditer(text.replace("\r\n", "\n")):
        name, typ, key, raw = m.group(1), m.group(2).strip(), m.group(3), " ".join(m.group(4).split())
        value: Any = raw
        if raw in ("true", "false"):
            value = raw == "true"
        elif NUM_RE.fullmatch(raw):
            num = raw.replace("_", "")
            value = float(num) if ("." in num or typ in ("f64", "f32")) else int(num)
        elif len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            value = raw[1:-1]
        out[name] = {"key": key, "type": typ, "value": value}
    return out


def check_complete(text: str, parsed: Dict[str, Dict[str, Any]]) -> None:
    """Every param! block in the file must have been parsed; a silent skip hides a changed weight."""
    blocks = len(BLOCK_RE.findall(text.replace("\r\n", "\n")))
    if len(parsed) < blocks:
        raise WatchError(f"parsed {len(parsed)} of {blocks} param! blocks: the file format changed, "
                         "so some parameters would be silently ignored.")


def is_weight(name: str) -> bool:
    return bool(re.search(r"(Weight|WeightBoost)$", name))


def validate(params: Dict[str, Dict[str, Any]]) -> None:
    if len(params) < MIN_PARAMS:
        raise WatchError(f"parse looks wrong: found {len(params)} params, expected at least {MIN_PARAMS}. "
                         "The file format may have changed.")
    n = sum(1 for k, v in params.items() if is_weight(k) and isinstance(v["value"], (int, float)))
    if n < MIN_WEIGHTS:
        raise WatchError(f"parse looks wrong: found {n} numeric weight params, expected at least {MIN_WEIGHTS}.")


def compare(old: Dict[str, Dict[str, Any]], new: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    changes: List[Dict[str, Any]] = []
    for name in sorted(set(old) | set(new)):
        a, b = old.get(name), new.get(name)
        if a is None:
            changes.append({"change": "added", "name": name, "before": None, "after": b["value"], "weight": is_weight(name)})  # type: ignore[index]
        elif b is None:
            changes.append({"change": "removed", "name": name, "before": a["value"], "after": None, "weight": is_weight(name)})
        elif a["value"] != b["value"] or a["type"] != b["type"] or a["key"] != b["key"]:
            same = a["value"] == b["value"]       # only the type or the key moved: show that, not two equal values
            changes.append({"change": "changed", "name": name, "weight": is_weight(name),
                            "before": a["value"] if not same else f"{a['type']} {a['key']}",
                            "after": b["value"] if not same else f"{b['type']} {b['key']}"})
    changes.sort(key=lambda c: (not c["weight"], c["name"]))
    return changes


def fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:g}"
    s = str(v)
    if s == "":
        return chr(34) * 2
    s = s if len(s) <= 60 else s[:57] + "..."
    if isinstance(v, str):
        # Upstream strings reach README, commit messages and issues: neutralise markdown and HTML.
        s = s.replace("`", "'").replace("|", "\\|").replace("<", "(").replace(">", ")")
        return "`" + s + "`"
    return s


def render_diff(changes: List[Dict[str, Any]], date: str, commit: str, commit_date: str, baseline: bool = False,
                total: int = 0) -> str:
    n = len(changes)
    wn = sum(1 for c in changes if c["weight"])
    if baseline:
        head = f"## {date}, baseline ({total} params, commit {commit[:7]})"
    else:
        head = f"## {date}, {n} change{'s' if n != 1 else ''} (commit {commit[:7]})"
    L = [head, "", f"Source commit date: {commit_date}. Source: {SOURCE_URL}", ""]
    if baseline:
        L += ["First snapshot. Later entries list what changed against it.", ""]
        return "\n".join(L)
    L += [f"{wn} of the changes are ranking weights; the rest are other parameters and feature defaults.", "",
          "| change | param | before | after |", "|---|---|---|---|"]
    for c in changes:
        mark = "weight" if c["weight"] else "param"
        L.append(f"| {c['change']} ({mark}) | `{c['name']}` | {fmt(c['before'])} | {fmt(c['after'])} |")
    L.append("")
    return "\n".join(L)


def read_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def entries(changelog: str) -> List[str]:
    parts = re.split(r"(?m)^(?=## \d{4}-\d{2}-\d{2},)", changelog)
    return [p.rstrip() + "\n" for p in parts if p.startswith("## ")]


CHANGELOG_HEAD = ("# Algorithm changelog\n\nGenerated by `tools/algo_watch.py` from "
                  "`home-mixer/params/param.rs` in xai-org/x-algorithm. Newest first. Never edit by hand.\n\n")


def update_changelog(path: str, entry: str) -> str:
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    body = "".join(entries(old))
    text = CHANGELOG_HEAD + entry.rstrip() + "\n\n" + body
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.rstrip() + "\n")
    return text


def update_readme(readme: str, changelog_text: str) -> bool:
    if not os.path.exists(readme):
        return False
    t = open(readme, encoding="utf-8").read()
    if START not in t or END not in t:
        return False
    last3 = "\n".join(e.rstrip() + "\n" for e in entries(changelog_text)[:3])
    # Demote the headings so they nest under the README section.
    last3 = re.sub(r"(?m)^## ", "#### ", last3)
    block = f"{START}\n{last3.rstrip()}\n\nFull history: [references/ALGO-CHANGELOG.md](references/ALGO-CHANGELOG.md).\n{END}"
    new = t[:t.index(START)] + block + t[t.index(END) + len(END):]
    if new != t:
        with open(readme, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
    return new != t


def _get(url: str, token: Optional[str]) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "x-agent-skill-algo-watch", "Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as exc:
        raise WatchError(f"HTTP {exc.code} fetching {url}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WatchError(f"network error fetching {url}: {exc}") from exc


def fetch(token: Optional[str] = None) -> Tuple[str, str, str]:
    """Return (text, commit_sha, commit_date) for the file at the default branch."""
    repo = json.loads(_get(f"https://api.github.com/repos/{REPO}", token))
    branch = repo.get("default_branch") or "main"
    commits = json.loads(_get(f"https://api.github.com/repos/{REPO}/commits?path={PATH}&sha={branch}&per_page=1", token))
    if not commits:
        raise WatchError(f"{PATH} has no commits on {branch}: the file moved or was deleted.")
    sha = commits[0]["sha"]
    date = commits[0]["commit"]["committer"]["date"]
    try:
        text = _get(f"https://raw.githubusercontent.com/{REPO}/{sha}/{PATH}", token).decode("utf-8")
    except WatchError as exc:
        raise WatchError(f"{exc}. The file may have moved at {sha[:7]}.") from exc
    return text, sha, date


def run(text: str, commit: str, commit_date: str, root: str, today: str, write: bool,
        diff_out: Optional[str] = None) -> Dict[str, Any]:
    new = parse_all(text)
    check_complete(text, new)
    validate(new)
    ref = os.path.join(root, "references")
    wpath = os.path.join(ref, "weights.json")
    prev = read_json(wpath)
    baseline = prev is None
    changes = [] if baseline else compare(prev["params"], new)  # type: ignore[index]
    unchanged_pin = (not baseline) and prev.get("commit") == commit  # type: ignore[union-attr]
    result = {"changes": changes, "n": len(changes), "baseline": baseline, "commit": commit, "date": today,
              "weight_changes": sum(1 for c in changes if c["weight"])}
    problems = validate_update(None if baseline else prev["params"], new)  # type: ignore[index]
    if not baseline and not changes and not problems:
        return result
    diff_md = render_diff(changes, today, commit, commit_date, baseline, len(new))
    result["diff"] = diff_md
    if problems:
        diff_md = ("## Validation failed, nothing was committed\n\n" + "\n".join(f"- {p}" for p in problems)
                   + "\n\nRaw diff:\n\n" + diff_md)
    if diff_out:
        with open(diff_out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(diff_md)
    if problems:
        raise ValidationFailed(problems, diff_md)
    if write and not unchanged_pin:
        os.makedirs(ref, exist_ok=True)
        snap = {"source": SOURCE_URL, "commit": commit, "commit_date": commit_date, "fetched": today, "params": new}
        with open(wpath, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(snap, fh, indent=1, sort_keys=True)
            fh.write("\n")
        apath = os.path.join(ref, "x-algorithm.md")
        old_md = open(apath, encoding="utf-8").read() if os.path.exists(apath) else ""
        md = weights_tool.render(weights_tool.parse_params(text), commit, commit_date[:10], today, SOURCE_URL,
                                 weights_tool.previous_values(old_md) if old_md else None)
        with open(apath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        cl = update_changelog(os.path.join(ref, "ALGO-CHANGELOG.md"), diff_md)
        update_readme(os.path.join(root, "README.md"), cl)
    return result


def main(argv: Optional[List[str]] = None) -> int:
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Track changes to X's open-sourced ranking parameters.")
    ap.add_argument("--param-file", help="use this param.rs instead of fetching (needs --commit and --date)")
    ap.add_argument("--commit", help="commit hash for --param-file")
    ap.add_argument("--date", help="commit date (YYYY-MM-DD or ISO) for --param-file")
    ap.add_argument("--root", default=ROOT, help="repo root (default: this repo)")
    ap.add_argument("--today", default=datetime.date.today().isoformat(), help="date stamped on the entry")
    ap.add_argument("--write", action="store_true", help="update references/ and README.md")
    ap.add_argument("--diff-out", help="write the diff markdown here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        datetime.date.fromisoformat(args.today)
        if args.param_file:
            if not args.commit or not args.date:
                raise WatchError("--param-file needs --commit and --date")
            if not re.fullmatch(r"[0-9a-fA-F]{7,40}", args.commit):
                raise WatchError("--commit must be a 7 to 40 character hex hash")
            with open(args.param_file, "rb") as fh:
                text, commit, cdate = fh.read().decode("utf-8-sig"), args.commit.lower(), args.date
        else:
            text, commit, cdate = fetch(os.environ.get("GITHUB_TOKEN"))
        res = run(text, commit, cdate, args.root, args.today, args.write, args.diff_out)
    except ValidationFailed as exc:
        print("VALIDATION FAILED: nothing written, nothing to commit.", file=sys.stderr)
        for pr in exc.problems:
            print(f"  - {pr}", file=sys.stderr)
        return 3
    except (WatchError, OSError, ValueError) as exc:
        print(f"FAILURE: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({k: v for k, v in res.items() if k != "diff"}, indent=2, default=str))
    elif res.get("diff"):
        sys.stdout.write(res["diff"])
    else:
        print(f"No changes at {commit[:7]}.")
    return 10 if (res["changes"] or res["baseline"]) else 0


if __name__ == "__main__":
    sys.exit(main())
