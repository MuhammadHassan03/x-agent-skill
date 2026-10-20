# Copyright (c) 2026 Muhammad Hassan. MIT License.
import json
import subprocess
import sys

import detect
import humanize
from conftest import ROOT, fixture

LEX = humanize.load_lexicon()
SLOP = open(fixture("slop_sample.txt"), encoding="utf-8").read()
HUMAN = open(fixture("human_sample.txt"), encoding="utf-8").read()
H = ROOT + "/skills/x-human/humanize.py"
D = ROOT + "/skills/x-human/detect.py"


def clean(t):
    return humanize.humanize(t, LEX)


def test_invisible_removed():
    out, rep = clean("a​b⁠c﻿d­e")
    assert out.strip() == "abcde" and rep["invisible"]


def test_tag_characters_removed():
    out, _ = clean("hi" + "".join(chr(0xE0000 + ord(c)) for c in "hidden"))
    assert out.strip() == "hi"


def test_emoji_zwj_family_is_preserved():
    fam = "\U0001F468‍\U0001F469‍\U0001F467"
    out, _ = clean("family " + fam)
    assert fam in out


def test_stray_zwj_outside_emoji_removed():
    out, _ = clean("a‍b")
    assert out.strip() == "ab"


def test_em_dash_becomes_comma_and_no_dashes_remain():
    out, _ = clean("I tried it—it worked. Pages 5–10 help.")
    assert "—" not in out and "–" not in out
    assert "5-10" in out and "I tried it, it worked" in out


def test_curly_quotes_straightened():
    out, _ = clean("“it’s fine”")
    assert out.strip() == '"it\'s fine"'


def test_lexicon_replaces_with_case_kept():
    out, _ = clean("Leverage the robust tool.")
    assert out.strip() == "Use the solid tool."


def test_x_phrases_deleted_and_emoji_thread_marker():
    out, rep = clean("A thread \U0001F9F5\n\nLet that sink in. I shipped it in 3 days.")
    assert "sink in" not in out and "\U0001F9F5" not in out
    assert "I shipped it in 3 days." in out


def test_urls_mentions_cashtags_untouched():
    t = "Ask @leverage about $robust at https://example.com/leverage–robust now"
    out, _ = clean(t)
    assert "@leverage" in out and "$robust" in out and "https://example.com/leverage–robust" in out


def test_lowercase_voice_is_kept():
    out, _ = clean("lol this worked. it was robust.")
    assert out.startswith("lol this worked.")


def test_structures_flagged_not_rewritten():
    _, rep = clean(SLOP)
    ids = {s["id"] for s in rep["structures"]}
    assert {"numbered-emoji", "hashtag-wall"} <= ids


def test_full_sample_end_state():
    out, rep = clean(SLOP)
    body = out.replace("https://example.com/a–b—c", "")
    assert "—" not in body and "​" not in out and " " not in out
    assert "https://example.com/a–b—c" in out      # URL protected, dashes inside kept
    assert "leverage" not in out.lower() and "kicker" not in out


def test_empty_input():
    out, rep = clean("")
    assert out == "\n" and not any(rep.values())


def test_non_latin_survives():
    out, _ = clean("こんにちは、世界。")
    assert "こんにちは" in out


def test_idempotent():
    once, _ = clean(SLOP)
    twice, _ = clean(once)
    assert once == twice


def test_detect_human_sample_passes_and_slop_does_not():
    assert detect.run(HUMAN, LEX)["verdict"].startswith("PASS")
    assert not detect.run(SLOP, LEX)["verdict"].startswith("PASS")


def test_detect_short_text_not_given_fake_score():
    r = detect.run("Shipped it in 3 days.", LEX)
    assert r["checks"]["BURSTINESS"][0] is None and r["scored"] < 5


def test_detect_improves_after_humanize():
    out, _ = clean(SLOP)
    assert detect.run(out, LEX)["overall"] > detect.run(SLOP, LEX)["overall"]


def test_detect_empty():
    assert detect.run("", LEX)["verdict"] == "NO TEXT"


def test_cli_roundtrip(tmp_path):
    p = tmp_path / "d.txt"
    p.write_bytes(SLOP.replace("\n", "\r\n").encode("utf-8"))
    r = subprocess.run([sys.executable, H, str(p), "--json"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and "\r" not in json.loads(r.stdout)["text"]
    q = tmp_path / "o.txt"
    assert subprocess.run([sys.executable, H, str(p), "-o", str(q)], capture_output=True).returncode == 0
    assert subprocess.run([sys.executable, D, str(p), str(q)], capture_output=True).returncode in (0, 1)
    assert subprocess.run([sys.executable, H, str(tmp_path / "no")], capture_output=True).returncode == 2
    assert subprocess.run([sys.executable, D, str(tmp_path / "no")], capture_output=True).returncode == 2


def test_orphaned_connective_after_deletion_is_dropped():
    out, _ = clean("I shipped it. Bookmark this and follow for more!")
    assert out.strip() == "I shipped it."
