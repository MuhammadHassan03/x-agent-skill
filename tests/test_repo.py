# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""Repository hygiene: the rules from CONTRIBUTING.md, enforced."""
import ast
import json
import os
import re

import pytest

from conftest import ROOT, SKILLS

TEXT_EXT = {".md", ".py", ".json", ".yml", ".txt", ".ini", ".rs"}
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
    fixtures = os.path.join(ROOT, "tests", "fixtures")
    bad = [p for p in text_files() if not p.startswith(fixtures) and "\u2014" in read(p)]
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


def test_every_tool_has_help_and_json_flags():
    for p in text_files():
        if p.endswith(".py") and os.sep + "skills" + os.sep in p and "import argparse" in read(p):
            assert "--json" in read(p) or p.endswith(("ocr.py",)), p


def test_manifest_and_data_files():
    plugin = json.loads(read(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    assert plugin["name"] == "x-agent" and plugin["license"] == "MIT" and re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
    rubric = json.loads(read(os.path.join(SKILLS, "x-profile", "rubric.json")))
    assert sum(i["points"] for i in rubric["items"]) == rubric["total"] == 100
    hooks = json.loads(read(os.path.join(SKILLS, "x-post", "hooks.json")))
    ids = [h["id"] for h in hooks["hooks"]]
    assert len(ids) == len(set(ids)) == 19
    for h in hooks["hooks"]:
        re.compile(h["match"])
        assert set(h) >= {"name", "template", "example", "best_for", "trap"}


def test_license_is_mit_with_owner():
    assert "Copyright (c) 2026 Muhammad Hassan" in read(os.path.join(ROOT, "LICENSE"))


def test_every_reference_has_a_last_checked_line():
    for f in ("x-algorithm.md", "x-rules.md", "stale.md"):
        t = read(os.path.join(ROOT, "references", f))
        assert re.search(r"(?i)last checked: 2026-\d\d-\d\d|\| 2026-\d\d-\d\d \|", t), f
