# Copyright (c) 2026 Muhammad Hassan. MIT License.
import subprocess
import sys

import xcount
from conftest import ROOT


def w(text, premium=False):
    return xcount.count(text, premium)["weighted"]


def test_ascii_is_one_each():
    assert w("hello world") == 11


def test_empty_is_zero():
    assert w("") == 0


def test_cjk_is_two_each():
    assert w("你好") == 4


def test_url_is_23_whatever_its_length():
    assert w("https://example.com/" + "a" * 200) == 23
    assert w("see https://t.co/x") == 4 + 23


def test_bare_domain_counts_as_url():
    assert w("example.com") == 23


def test_trailing_punctuation_not_part_of_url():
    assert w("go to https://example.com.") == 6 + 23 + 1


def test_email_is_not_a_url():
    assert xcount.count("me@example.com")["urls"] == 0


def test_emoji_sequence_is_two_total():
    assert w("\U0001F600") == 2
    assert w("\U0001F468‍\U0001F469‍\U0001F467") == 2      # ZWJ family
    assert w("\U0001F44D\U0001F3FD") == 2                            # skin tone
    assert w("\U0001F1FA\U0001F1F8") == 2                            # flag
    assert w("1️⃣") == 2                                   # keycap


def test_punctuation_ranges_weigh_one():
    assert w("’") == 1          # 8217, in 8208-8223
    assert w("…") == 2          # 8230, outside the listed ranges


def test_nfc_normalisation():
    assert w("é") == 1         # e + combining acute -> one precomposed char


def test_crlf_counts_as_one_newline():
    assert w("a\r\nb") == w("a\nb") == 3


def test_free_limit_boundary():
    assert xcount.count("a" * 280)["fits"] is True
    r = xcount.count("a" * 281)
    assert r["fits"] is False and r["over"] == 1


def test_premium_limit_and_25000_char_post():
    assert xcount.count("a" * 25000, premium=True)["fits"] is True
    assert xcount.count("a" * 25001, premium=True)["over"] == 1
    assert xcount.count("a" * 25000)["fits"] is False


def test_post_that_is_only_a_url():
    r = xcount.count("https://example.com/very/long/path?x=1")
    assert r["weighted"] == 23 and r["urls"] == 1


def test_cli_exit_codes(tmp_path):
    p = tmp_path / "p.txt"
    p.write_text("short", encoding="utf-8")
    cmd = [sys.executable, str(ROOT) + "/skills/x-post/xcount.py"]
    assert subprocess.run(cmd + [str(p)], capture_output=True).returncode == 0
    p.write_text("a" * 300, encoding="utf-8")
    assert subprocess.run(cmd + [str(p)], capture_output=True).returncode == 1
    assert subprocess.run(cmd + [str(tmp_path / "nope.txt")], capture_output=True).returncode == 2


def test_cli_json_and_bom(tmp_path):
    p = tmp_path / "p.txt"
    p.write_bytes(b"\xef\xbb\xbfhi\r\n")
    out = subprocess.run([sys.executable, str(ROOT) + "/skills/x-post/xcount.py", str(p), "--json"],
                         capture_output=True, text=True)
    assert out.returncode == 0 and '"weighted": 2' in out.stdout
