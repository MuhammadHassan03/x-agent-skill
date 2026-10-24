# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""Regression tests for bugs that passed CI and were found by a whole-repo review."""
import pytest

import algo_watch
import humanize
import postscore
import replylint
import thread
import xcount
from conftest import fixture

LEX = humanize.load_lexicon()
JA_PARENT = "30日間試した結果を共有します"
JA_REPLY = "私は30日間試しました。理由は明確です。"
AR_PARENT = "جربت هذا لمدة 30 يوما"
AR_REPLY = "هذا منطقي جدا لأنني جربته لمدة 30 يوما"


# replylint: a reply in a script other than Latin must not be judged "no words"
@pytest.mark.parametrize("reply,parent", [(JA_REPLY, JA_PARENT), (AR_REPLY, AR_PARENT)])
def test_non_latin_reply_is_not_spam_by_default(reply, parent):
    r = replylint.lint(reply, parent)
    names = {c["check"]: c for c in r["checks"]}
    assert names["has words"]["pass"] and names["on topic"]["pass"]
    assert r["band"] >= 1


def test_emoji_only_reply_is_still_band_zero():
    assert replylint.lint("\U0001F525\U0001F525", JA_PARENT)["band"] == 0


def test_spaceless_scripts_match_on_bigrams():
    assert replylint.words("日本語") == ["日本", "本語"]
    assert replylint.words("it's 30 days") == ["it's", "30", "days"]


# "1/3 of my leads" is a fraction, not thread numbering
@pytest.mark.parametrize("line", ["1/3 of my leads came from replies", "1 / 4 customers asked twice", "1/2 the battle is the hook"])
def test_fractions_are_not_thread_openers(line):
    assert "thread opener as the hook" not in postscore.check_hook(line)[2]
    assert "thread-opener" not in {s["id"] for s in humanize.scan_structures(line, LEX)}


@pytest.mark.parametrize("line", ["1/ Here is why this works", "1/7: the hook", "1/", "A thread on cold DMs", "1/7."])
def test_real_thread_openers_still_flagged(line):
    assert "thread opener as the hook" in postscore.check_hook(line)[2]
    assert "thread-opener" in {s["id"] for s in humanize.scan_structures(line, LEX)}


# "#1" is not a hashtag
def test_numeric_hash_is_not_a_hashtag():
    text = "Rule #1 beats rule #2 and rule #3 every time. Why?"
    assert postscore.HASHTAG_RE.findall(text) == []
    assert "hashtag wall (more than 2)" not in postscore.score(text)["hard_flags"]
    assert "hashtag-wall" not in {s["id"] for s in humanize.scan_structures(text, LEX)}


def test_real_hashtag_wall_still_flagged():
    text = "Shipped it. #growth #x #tips"
    assert "hashtag wall (more than 2)" in postscore.score(text)["hard_flags"]
    assert "hashtag-wall" in {s["id"] for s in humanize.scan_structures(text, LEX)}
    assert postscore.HASHTAG_RE.findall("#2024election and #a1") == ["#2024election", "#a1"]


# a closing bracket that closes one opened inside the URL belongs to the URL
def test_balanced_parenthesis_stays_in_the_url():
    assert xcount.count("see https://en.wikipedia.org/wiki/Foo_(bar) now")["weighted"] == 4 + 23 + 4
    assert xcount.count("https://en.wikipedia.org/wiki/Foo_(bar).")["weighted"] == 23 + 1


def test_unbalanced_closing_bracket_is_not_part_of_the_url():
    assert xcount.count("(see https://example.com/x)")["weighted"] == 5 + 23 + 1
    assert xcount.count("[https://example.com/x]")["weighted"] == 1 + 23 + 1


# an emoji left over after a link is removed is content, not nothing
def test_thread_keeps_an_emoji_only_remainder():
    r = thread.build("Intro.\n\n\U0001F525 https://a.example/x\n\nOutro.")
    assert r["posts"] == ["Intro.", "\U0001F525", "Outro."]
    assert r["first_reply"] == "https://a.example/x"


def test_split_link_keeps_an_emoji_only_remainder():
    root, reply = postscore.split_link("Intro.\n\n\U0001F525 https://a.example/x")
    assert "\U0001F525" in root and reply == "https://a.example/x"


def test_split_link_still_drops_a_punctuation_only_remainder():
    assert postscore.split_link("Intro.\n\n(https://a.example/x)")[0] == "Intro."


# algo_watch must not silently ignore a param block it cannot parse
def test_generic_types_with_commas_parse():
    p = algo_watch.parse_all('param!(\n A,\n HashMap<String, u32>,\n "k_weight",\n 1\n);\nparam!(B, f64, "b_weight", 2.0);')
    assert set(p) == {"A", "B"} and p["A"]["type"] == "HashMap<String, u32>"


def test_unparseable_block_is_an_error_not_a_silent_skip():
    text = 'param!(Good, f64, "g_weight", 1.0);\nparam!(\n  Broken,\n  "no_type_here"\n);\n'
    parsed = algo_watch.parse_all(text)
    assert set(parsed) == {"Good"}
    with pytest.raises(algo_watch.WatchError) as e:
        algo_watch.check_complete(text, parsed)
    assert "1 of 2" in str(e.value)


def test_complete_file_passes_the_completeness_check():
    text = open(fixture("param_full.rs"), encoding="utf-8").read()
    algo_watch.check_complete(text, algo_watch.parse_all(text))


def test_run_refuses_an_incomplete_parse(tmp_path):
    text = open(fixture("param_full.rs"), encoding="utf-8").read() + '\nparam!(\n  Broken,\n  "no_type_here"\n);\n'
    (tmp_path / "references").mkdir()
    with pytest.raises(algo_watch.WatchError):
        algo_watch.run(text, "a" * 40, "2026-10-24", str(tmp_path), "2026-10-24", True)
    assert not (tmp_path / "references" / "weights.json").exists()


# upstream strings are data: they must not become markdown or HTML in README, commits and issues
@pytest.mark.parametrize("hostile", ["[click](https://evil.example)", "a | b", "x`y", "<script>alert(1)</script>", "![i](https://e.example/p.png)"])
def test_string_values_are_neutralised(hostile):
    out = algo_watch.fmt(hostile)
    assert out.startswith("`") and out.endswith("`")
    assert "<" not in out and ">" not in out and "|" not in out.replace("\\|", "") and "`" not in out[1:-1]


def test_hostile_default_cannot_inject_a_link_into_the_diff():
    ch = [{"change": "added", "name": "X", "before": None, "after": "[click](https://evil.example)", "weight": False}]
    md = algo_watch.render_diff(ch, "2026-10-24", "a" * 40, "2026-10-24")
    row = [ln for ln in md.splitlines() if "`X`" in ln][0]
    assert "`[click](https://evil.example)`" in row


def test_type_or_key_only_change_is_visible():
    old = {"W": {"key": "k_old", "type": "f64", "value": 1.0}}
    new = {"W": {"key": "k_new", "type": "f64", "value": 1.0}}
    ch = algo_watch.compare(old, new)
    assert ch[0]["before"] == "f64 k_old" and ch[0]["after"] == "f64 k_new"
