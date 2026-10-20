# Copyright (c) 2026 Muhammad Hassan. MIT License.
import subprocess
import sys

import replylint
from conftest import ROOT, fixture

PARENT = open(fixture("parent.txt"), encoding="utf-8").read()
SCRIPT = ROOT + "/skills/x-reply/replylint.py"


def band(reply, **kw):
    return replylint.lint(reply, PARENT, **kw)["band"]


def test_generic_praise_is_band_zero():
    for r in ["Great point!", "This!", "So true", "100%", "Well said.", "Love this"]:
        assert band(r) == 0, r


def test_compliment_with_substance_loses_praise_opener_not_zero():
    r = replylint.lint("Great point. I switched to asking about pricing pages and my reply rate went from 3% to 11% in a month.", PARENT)
    assert r["band"] in (1, 2)


def test_strong_reply_is_three():
    assert band("I saw the same: after I started asking about their pricing page, 9 of 40 cold DMs got replies, because it proves you read it.") == 3


def test_off_topic_is_zero():
    assert band("My cat knocked a glass off the table yesterday and it shattered everywhere, honestly hilarious stuff.") == 0


def test_emoji_only_is_zero():
    assert band("\U0001F525\U0001F525\U0001F525") == 0


def test_link_plus_promo_is_zero():
    assert band("Check out my newsletter about cold DMs and pricing pages https://example.com/n") == 0


def test_self_reply_chain_is_zero():
    good = "I saw the same: after I started asking about their pricing page, 9 of 40 cold DMs got replies, because it proves you read it."
    assert band(good, prior_in_thread=1) == 0
    assert band(good, prior_in_thread=0) == 3


def test_too_short_not_band_two():
    assert band("pricing pages matter") <= 1


def test_restatement_is_capped():
    assert band("Cold DMs get ignored because they open with the sender and pricing pages") <= 2


def test_without_parent_on_topic_not_checked():
    r = replylint.lint("I tried it for 30 days and got 4 calls, because the pricing question is easy to answer.")
    assert any("not checked" in c["detail"] for c in r["checks"])


def test_non_latin_reply_does_not_crash():
    r = replylint.lint("私は30日間試しました。理由は明確です。", PARENT)
    assert 0 <= r["band"] <= 3


def test_cli(tmp_path):
    r = tmp_path / "r.txt"
    r.write_text("Great point!\r\n", encoding="utf-8")
    p = subprocess.run([sys.executable, SCRIPT, str(r), "--parent", fixture("parent.txt")], capture_output=True, text=True)
    assert p.returncode == 1 and "generic praise" in p.stdout
    r.write_text("", encoding="utf-8")
    assert subprocess.run([sys.executable, SCRIPT, str(r)], capture_output=True).returncode == 2
    assert subprocess.run([sys.executable, SCRIPT, str(r), "--prior-replies-in-thread", "-1"], capture_output=True).returncode == 2
