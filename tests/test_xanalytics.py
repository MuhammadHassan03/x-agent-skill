# Copyright (c) 2026 Muhammad Hassan. MIT License.
import json
import subprocess
import sys

import pytest

import xanalytics
from conftest import ROOT, fixture

SCRIPT = ROOT + "/skills/x-audit/xanalytics.py"


def load(**kw):
    return xanalytics.parse(open(fixture("analytics.csv"), encoding="utf-8").read(), **kw)


def test_replies_dropped_by_default_and_kept_on_request():
    posts, notes, _ = load()
    assert len(posts) == 20 and any("reply row" in n for n in notes)
    posts2, _, _ = load(include_replies=True)
    assert len(posts2) == 22


def test_ranking_uses_multiple_of_median():
    posts, _, _ = load()
    res = xanalytics.analyse(posts, top=3)
    assert res["top"][0]["multiple"] >= res["top"][1]["multiple"]
    assert abs(res["baseline_median_impressions"] - 996) < 100
    assert res["top"][0]["text"].startswith("Everyone says")


def test_feature_groups_need_three_posts():
    posts, _, _ = load()
    res = xanalytics.analyse(posts)
    link = [f for f in res["features"] if f["feature"] == "link in body"][0]
    assert {g["group"] for g in link["groups"]} == {"link", "no link"}
    assert all(g["median_multiple"] is None or g["n"] >= 3 for f in res["features"] for g in f["groups"])
    assert "fewer than 30" in res["caveat"]


def test_needs_three_posts():
    with pytest.raises(ValueError):
        xanalytics.analyse([{"impressions": 1, "text": "", "date": None}] * 2)


def test_missing_impressions_column_lists_headers():
    with pytest.raises(ValueError) as e:
        xanalytics.parse("a,b\n1,2\n")
    assert "Found headers" in str(e.value)


def test_flexible_headers_tsv_and_bom_style_dates():
    t = "Tweet text\tPosted\tViews\n" + "\n".join(f"post {i} text here\tOct {i}, 2026\t{i * 100}" for i in range(1, 6))
    posts, _, mapping = xanalytics.parse(t)
    assert mapping["impressions"] == "Views" and posts[0]["date"].month == 10


def test_zero_median_rejected():
    t = "text,impressions\n" + "\n".join(f"p{i},0" for i in range(5))
    posts, _, _ = xanalytics.parse(t)
    with pytest.raises(ValueError):
        xanalytics.analyse(posts)


def test_non_latin_text():
    t = "text,impressions\n你好世界,100\nこんにちは,200\nمرحبا,300\n"
    posts, _, _ = xanalytics.parse(t)
    assert xanalytics.analyse(posts)["posts"] == 3


def test_in_reply_to_column():
    t = "text,impressions,in reply to\nhello,100,\nhi,200,12345\nyo,300,\nsup,400,\n"
    posts, _, _ = xanalytics.parse(t)
    assert len(posts) == 3


def test_cli(tmp_path):
    r = subprocess.run([sys.executable, SCRIPT, fixture("analytics.csv"), "--json"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and json.loads(r.stdout)["posts"] == 20
    p = tmp_path / "e.csv"
    p.write_text("", encoding="utf-8")
    assert subprocess.run([sys.executable, SCRIPT, str(p)], capture_output=True).returncode == 2
