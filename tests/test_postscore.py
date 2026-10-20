# Copyright (c) 2026 Muhammad Hassan. MIT License.
import json
import subprocess
import sys

import postscore
from conftest import ROOT, fixture

SCRIPT = ROOT + "/skills/x-post/postscore.py"


def read(name):
    return open(fixture(name), encoding="utf-8").read()


def test_good_post_scores_strong_and_clean():
    r = postscore.score(read("post_good.txt"))
    assert r["verdict"] == "STRONG" and not r["hard_flags"]


def test_bad_post_is_blocked_for_bait_and_hashtags():
    r = postscore.score(read("post_bad.txt"))
    assert "engagement bait" in r["hard_flags"]
    assert any("hashtag" in f for f in r["hard_flags"])
    assert "Original Content Rewards" in " ".join(r["checks"]["BAIT"]["notes"])


def test_placeholder_blocks_and_is_not_specific():
    r = postscore.score(read("post_placeholder.txt"))
    assert "unfilled {{placeholder}}" in r["hard_flags"]
    assert r["checks"]["SPECIFICITY"]["score"] == 0.0


def test_link_in_body_warns_on_free_not_blocked():
    r = postscore.score("I shipped a tool in 3 days. Here: https://example.com/tool", premium=False)
    assert r["checks"]["LINK"]["score"] < 50
    assert "Observed, not coded" in r["checks"]["LINK"]["notes"][0]
    assert not r["hard_flags"]


def test_post_that_is_only_a_url():
    r = postscore.score("https://example.com/a/very/long/path")
    assert r["length"]["weighted"] == 23
    assert r["checks"]["LINK"]["score"] < 50


def test_over_limit_blocks():
    r = postscore.score("I wrote " + "word " * 100)
    assert any("over the 280" in f for f in r["hard_flags"])


def test_long_post_ok_on_premium():
    r = postscore.score("I wrote " + "word " * 100, premium=True)
    assert not any("over" in f for f in r["hard_flags"])


def test_non_latin_text_does_not_crash():
    r = postscore.score("我在 30 天内发了 400 条私信")
    assert 0 <= r["score"] <= 100


def test_hook_ranking_orders_sensibly():
    a = postscore.score_hook_line("I sent 400 cold DMs in 30 days.")
    b = postscore.score_hook_line("A thread on growth")
    assert a["score"] > b["score"]


def test_bait_patterns():
    for t in ["RT if you agree", "like and repost if you want this", "follow for more tips",
              "Bookmark this for later"]:
        assert postscore.find_bait(t), t
    assert not postscore.find_bait("I liked the book and reposted nothing")


def test_cli_exit_codes_and_json(tmp_path):
    p = tmp_path / "p.txt"
    p.write_text(read("post_good.txt"), encoding="utf-8")
    r = subprocess.run([sys.executable, SCRIPT, str(p), "--json"], capture_output=True, text=True)
    assert r.returncode == 0 and json.loads(r.stdout)["verdict"] == "STRONG"
    p.write_text(read("post_bad.txt"), encoding="utf-8")
    assert subprocess.run([sys.executable, SCRIPT, str(p)], capture_output=True).returncode == 1
    p.write_text("   \n", encoding="utf-8")
    assert subprocess.run([sys.executable, SCRIPT, str(p)], capture_output=True).returncode == 2
    assert subprocess.run([sys.executable, SCRIPT, str(tmp_path / "x")], capture_output=True).returncode == 2


def test_crlf_input(tmp_path):
    p = tmp_path / "p.txt"
    p.write_bytes(read("post_good.txt").replace("\n", "\r\n").encode("utf-8"))
    r = subprocess.run([sys.executable, SCRIPT, str(p), "--json"], capture_output=True, text=True)
    assert r.returncode == 0


def test_hooks_mode(tmp_path):
    r = subprocess.run([sys.executable, SCRIPT, "--hooks", fixture("hooks.txt")], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.splitlines()[0].startswith("1.")
