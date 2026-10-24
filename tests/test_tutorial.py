# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""The /x-post tutorial quotes real tool output. If a tool changes, this fails and the tutorial gets re-run."""
import os
import re
import subprocess
import sys

from conftest import ROOT

TUTORIAL = os.path.join(ROOT, "docs", "tutorial-x-post.md")
DRAFT = ("I sent 40 cold DMs in 30 days and 2 became clients.\n\n"
         "The two who said yes both got a question about their pricing page, not a pitch.\n\n"
         "What is the first line you send a stranger?\n\n"
         "Write-up: https://example.com/cold-dm-notes\n")
POST2 = ("I sent 40 cold DMs in 30 days. Two became clients.\n\n"
         "Neither got a pitch. Both got one question about their pricing page, written for them, with nothing else attached.\n\n"
         "What's the first line you send a stranger?\n")
HOOKS = ("A thread on cold DMs\nI used to open cold DMs with a pitch. Now I open with a question.\n"
         "I sent 40 cold DMs in 30 days and 2 became clients.\n")


def text():
    return open(TUTORIAL, encoding="utf-8").read()


def run(script, path, *args):
    return subprocess.run([sys.executable, os.path.join(ROOT, script), str(path), *args], capture_output=True,
                          text=True, encoding="utf-8")


def test_tutorial_is_linked_from_the_readme_and_every_tool_it_names_exists():
    assert "docs/tutorial-x-post.md" in open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    for rel in set(re.findall(r"skills/[\w-]+/\w+\.py", text())):
        assert os.path.exists(os.path.join(ROOT, rel)), rel


def test_the_draft_and_post_quoted_in_the_tutorial_are_the_ones_tested_here():
    t = text()
    for block in (DRAFT.strip(), POST2.strip(), HOOKS.strip()):
        assert block in t


def test_quoted_counts_and_scores_match_the_tools(tmp_path):
    t = text()
    d, p = tmp_path / "draft.txt", tmp_path / "post2.txt"
    d.write_text(DRAFT, encoding="utf-8")
    p.write_text(POST2, encoding="utf-8")
    xc = run("skills/x-post/xcount.py", d).stdout
    assert "212 / 280 weighted (free)  FITS" in xc and "212 / 280 weighted (free)  FITS" in t
    ps = run("skills/x-post/postscore.py", d)
    assert ps.returncode == 1 and "POST SCORE  49.0  WEAK" in ps.stdout and "POST SCORE  49.0  WEAK" in t
    split = run("skills/x-post/postscore.py", d, "--split-link").stdout
    assert "FIRST REPLY\nWrite-up:\nhttps://example.com/cold-dm-notes" in split.replace("\r\n", "\n")
    final = run("skills/x-post/postscore.py", p).stdout
    assert "POST SCORE  93.8  STRONG   (210/280 weighted)" in final and "POST SCORE  93.8  STRONG   (210/280 weighted)" in t
    panel = run("skills/x-human/detect.py", p).stdout
    assert "HUMAN SCORE" in panel and "81.6   PASS" in panel and "81.6   PASS" in t


def test_quoted_hook_ranking_matches_the_tool(tmp_path):
    h = tmp_path / "hooks.txt"
    h.write_text(HOOKS, encoding="utf-8")
    out = run("skills/x-post/postscore.py", h.parent / "none.txt", "--hooks", str(h)).stdout
    for line in ("97.0  no formula matched", "66.3  Reversal", "40.0  no formula matched"):
        assert line in out and line in text()
