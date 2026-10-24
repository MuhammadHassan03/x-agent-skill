# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""Repository hygiene: the rules from CONTRIBUTING.md, enforced."""
import ast
import json
import os
import re
import subprocess
import sys

import pytest

from conftest import ROOT, SKILLS

TEXT_EXT = {".md", ".py", ".json", ".yml", ".txt", ".ini", ".rs", ".html", ".css", ".js"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
GATE_START = "## Approval gate"
FORBIDDEN_IMPORTS = {"socket", "urllib", "http", "requests", "httpx", "selenium", "playwright", "webbrowser",
                     "ftplib", "smtplib", "aiohttp", "subprocess", "ssl", "xmlrpc", "telnetlib"}


def text_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1] in TEXT_EXT or f in ("LICENSE", "CODEOWNERS"):
                yield os.path.join(base, f)


def skill_dirs():
    return sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))


def read(path):
    return open(path, encoding="utf-8").read()


def test_twelve_skills_with_expected_names():
    assert skill_dirs() == sorted(f"x-{n}" for n in
        ["post", "thread", "reply", "viral", "article", "human", "profile", "plan", "dm", "audit", "money", "algo"])


@pytest.mark.parametrize("name", skill_dirs())
def test_skill_format(name):
    text = read(os.path.join(SKILLS, name, "SKILL.md"))
    m = re.match(r"---\nname: (.+)\ndescription: >-\n((?:  .*\n)+)---\n", text)
    assert m, "frontmatter must be name + folded description"
    assert m.group(1) == name and len(name) <= 64 and re.fullmatch(r"[a-z0-9-]+", name)
    assert "claude" not in name and "anthropic" not in name
    desc = " ".join(l.strip() for l in m.group(2).splitlines())
    assert 100 < len(desc) <= 1024
    assert len(text.splitlines()) < 500


def test_every_skill_ends_with_the_same_approval_gate():
    gates = set()
    for name in skill_dirs():
        text = read(os.path.join(SKILLS, name, "SKILL.md"))
        gate = text[text.rindex(GATE_START):]
        gates.add(gate.strip())
        assert "Reply yes to log it" in gate and "Never post" in gate
    assert len(gates) == 1


def test_no_em_dashes_anywhere():
    exempt = (os.path.join(ROOT, "tests", "fixtures"), os.path.join(ROOT, "demo", "samples"))
    bad = [p for p in text_files() if not p.startswith(exempt) and "\u2014" in read(p)]
    assert not bad, bad


def test_copyright_header_on_every_python_file():
    header = "# Copyright (c) 2026 Muhammad Hassan. MIT License."
    for p in text_files():
        if p.endswith(".py"):
            assert header in "".join(read(p).splitlines(True)[:3]), p


def test_tools_import_nothing_that_talks_to_the_network_or_a_browser():
    for p in text_files():
        if p.endswith(".py") and os.sep + "skills" + os.sep in p:
            tree = ast.parse(read(p))
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module.split(".")[0]]
                assert not (set(mods) & FORBIDDEN_IMPORTS), (p, mods)


def test_undetectable_is_only_ever_negated():
    for p in text_files():
        if p.endswith((".md", ".py")) and "test_repo" not in p:
            lines = read(p).splitlines()
            for i, line in enumerate(lines):
                if re.search(r"undetectab", line, re.I):
                    window = " ".join(lines[max(0, i - 2):i + 1])
                    assert re.search(r"\b(never|not|no|nothing|cannot|can't|doesn't)\b", window, re.I), (p, line)


def test_every_tool_named_in_a_skill_exists():
    for name in skill_dirs():
        text = read(os.path.join(SKILLS, name, "SKILL.md"))
        for rel in re.findall(r"python3 ((?:\.\./[\w-]+/)?\w+\.py)", text):
            assert os.path.exists(os.path.normpath(os.path.join(SKILLS, name, rel))), (name, rel)


TOOL_HELP = [
    ("skills/x-post/xcount.py", []), ("skills/x-post/postscore.py", []), ("skills/x-thread/thread.py", []),
    ("skills/x-reply/replylint.py", []), ("skills/x-viral/swipe.py", []), ("skills/x-audit/xanalytics.py", []),
    ("skills/x-human/humanize.py", []), ("skills/x-human/detect.py", []), ("skills/x-money/ocr.py", ["status"]),
    ("skills/x-money/ocr.py", ["lint"]), ("tools/algo_watch.py", []), ("measurement/dogfood/report.py", []),
]


@pytest.mark.parametrize("script,sub", TOOL_HELP)
def test_every_tool_answers_help_and_offers_json(script, sub):
    r = subprocess.run([sys.executable, os.path.join(ROOT, script)] + sub + ["--help"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and "usage:" in r.stdout.lower(), script
    if script != "skills/x-algo/weights.py":
        assert "--json" in r.stdout, script


def test_weights_tool_help():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "skills/x-algo/weights.py"), "--help"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and "--commit" in r.stdout and "--json" in r.stdout


def test_manifest_and_data_files():
    plugin = json.loads(read(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    assert plugin["name"] == "x-agent" and plugin["license"] == "MIT" and re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
    rubric = json.loads(read(os.path.join(SKILLS, "x-profile", "rubric.json")))
    assert sum(i["points"] for i in rubric["items"]) == rubric["total"] == 100
    hooks = json.loads(read(os.path.join(SKILLS, "x-post", "hooks.json")))
    ids = [h["id"] for h in hooks["hooks"]]
    assert len(ids) == len(set(ids))
    for doc in ("README.md", os.path.join("site", "index.html")):
        claimed = {int(n) for n in re.findall(r"(\d+) formulas", read(os.path.join(ROOT, doc)))}
        assert claimed == {len(ids)}, (doc, claimed, len(ids))
    for h in hooks["hooks"]:
        re.compile(h["match"])
        assert set(h) >= {"name", "template", "example", "best_for", "trap"}


def test_license_is_mit_with_owner():
    assert "Copyright (c) 2026 Muhammad Hassan" in read(os.path.join(ROOT, "LICENSE"))


def test_every_reference_has_a_last_checked_line():
    for f in ("x-algorithm.md", "x-rules.md", "stale.md"):
        t = read(os.path.join(ROOT, "references", f))
        assert re.search(r"(?i)last checked: \d{4}-\d\d-\d\d|\| \d{4}-\d\d-\d\d \|", t), f


def test_site_is_static_small_and_self_contained():
    site = os.path.join(ROOT, "site")
    assert sorted(os.listdir(site)) == ["app.js", "apple-touch-icon.png", "favicon-32.png", "icon-64.png", "icon.svg", "index.html", "og.png", "style.css"]
    assert sum(os.path.getsize(os.path.join(site, f)) for f in os.listdir(site)) < 200 * 1024
    html = read(os.path.join(site, "index.html"))
    for url in re.findall(r'<(?:script|link)[^>]+(?:src|href)="([^"]+)"', html):
        assert not url.startswith(("http:", "https:", "//")), url
    assert "@import" not in read(os.path.join(site, "style.css"))
    assert not re.search(r"fetch\(|XMLHttpRequest|sendBeacon|WebSocket", read(os.path.join(site, "app.js")))


def test_site_has_no_invented_proof():
    html = read(os.path.join(ROOT, "site", "index.html")).lower()
    for word in ("testimonial", "stars", "customers", "trusted by", "users love"):
        assert word not in html, word


def test_demo_gif_is_small_1200_wide_and_linked():
    path = os.path.join(ROOT, "demo", "x-agent-skill.gif")
    data = open(path, "rb").read()
    assert data[:6] == b"GIF89a" and len(data) < 3 * 1024 * 1024
    assert int.from_bytes(data[6:8], "little") == 1200
    assert "demo/x-agent-skill.gif" in read(os.path.join(ROOT, "README.md"))


def test_demo_tape_commands_point_at_real_files():
    tape = read(os.path.join(ROOT, "demo", "x-agent-skill.tape"))
    paths = re.findall(r"__PY__ ((?:skills|demo)/[\w./-]+\.(?:py|txt))", tape)
    assert paths
    for p in paths:
        assert os.path.exists(os.path.join(ROOT, p)), p
