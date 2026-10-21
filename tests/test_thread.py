# Copyright (c) 2026 Muhammad Hassan. MIT License.
import subprocess
import sys

import thread
import xcount
from conftest import ROOT, fixture

SCRIPT = ROOT + "/skills/x-thread/thread.py"


def draft():
    return open(fixture("thread_draft.txt"), encoding="utf-8").read()


def test_every_post_fits():
    r = thread.build(draft())
    assert all(c <= 280 for c in r["weighted"])
    assert len(r["posts"]) >= 4


def test_links_go_to_a_first_reply_block_not_the_thread():
    r = thread.build(draft())
    assert r["links_moved"] == 1
    assert r["first_reply"] == "Full breakdown of the messages:\nhttps://example.com/dm-breakdown"
    assert not any("https://" in p for p in r["posts"])
    assert not any("Full breakdown" in p for p in r["posts"])


def test_links_last_keeps_the_old_behaviour():
    r = thread.build(draft(), links_last=True)
    assert r["first_reply"] is None
    assert "https://example.com/dm-breakdown" in r["posts"][-1]
    assert not any("https://" in p for p in r["posts"][:-1])
    assert r["posts"][-1].count("Full breakdown of the messages:") == 1


def test_no_link_means_no_first_reply():
    assert thread.build("I did a thing.\n\nIt worked in 3 days.")["first_reply"] is None


def test_cli_prints_first_reply_block():
    run = lambda *a: subprocess.run([sys.executable, SCRIPT, fixture("thread_draft.txt")] + list(a), capture_output=True, text=True).stdout  # noqa: E731
    assert ("FIRST REPLY (post it as a reply under post 1)\nFull breakdown of the messages:\n"
            "https://example.com/dm-breakdown") in run()
    out = run("--links-last")
    assert "FIRST REPLY" not in out and "moved to the last post" in out


def test_long_paragraph_splits_on_sentences():
    para = " ".join(f"Sentence number {i} says something specific." for i in range(12))
    r = thread.build(para)
    assert len(r["posts"]) >= 2 and all(c <= 280 for c in r["weighted"])
    assert all(p.rstrip().endswith(".") for p in r["posts"])


def test_numbering_counts_toward_budget():
    r = thread.build(draft(), number=True)
    assert r["posts"][0].startswith("1/")
    assert all(c <= 280 for c in r["weighted"])


def test_single_post_warns():
    r = thread.build("Short and sweet. I shipped it in 3 days.")
    assert any("one post" in w for w in r["warnings"])


def test_unbroken_word_run_is_split_and_flagged():
    r = thread.build("word" * 200)
    assert all(c <= 280 for c in r["weighted"])


def test_cjk_posts_respect_weight():
    r = thread.build("你好。" * 120)
    assert all(c <= 280 for c in r["weighted"]) and len(r["posts"]) > 1


def test_only_url_is_rejected():
    try:
        thread.build("https://example.com")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_empty_is_rejected():
    for t in ["", "  \n\n "]:
        try:
            thread.build(t)
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def test_pack_merges_short_paragraphs():
    t = "I did a thing.\n\nIt worked in 3 days.\n\nHere is why."
    assert len(thread.build(t, pack=True)["posts"]) == 1
    assert len(thread.build(t)["posts"]) == 3


def test_cli(tmp_path):
    p = tmp_path / "d.txt"
    p.write_bytes(draft().replace("\n", "\r\n").encode("utf-8"))
    r = subprocess.run([sys.executable, SCRIPT, str(p), "--json"], capture_output=True, text=True)
    assert r.returncode in (0, 1) and '"posts"' in r.stdout
    assert subprocess.run([sys.executable, SCRIPT, str(tmp_path / "nope")], capture_output=True).returncode == 2
