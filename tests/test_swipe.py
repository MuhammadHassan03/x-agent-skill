# Copyright (c) 2026 Muhammad Hassan. MIT License.
import json
import subprocess
import sys

import pytest

import swipe
from conftest import ROOT, fixture

SCRIPT = ROOT + "/skills/x-viral/swipe.py"


def load(name="swipe.tsv"):
    rows, _ = swipe.parse(open(fixture(name), encoding="utf-8").read())
    return rows


def test_number_parsing():
    assert swipe.parse_num("12.4K") == 12400 and swipe.parse_num("1,100") == 1100
    assert swipe.parse_num("1.2M") == 1_200_000 and swipe.parse_num("x") is None


def test_ranks_by_multiple_not_raw_views():
    res = swipe.rank(load())
    top = res["ranked"][0]
    assert top["account"] == "alpha_demo" and top["views"] == 41000
    # beta's 2.4k is a bigger multiple than alpha's ordinary posts despite fewer views
    beta = [r for r in res["ranked"] if r["account"] == "beta_demo" and r["views"] == 2400][0]
    assert beta["outlier"] and beta["multiple"] > 5


def test_account_with_one_post_has_no_baseline():
    res = swipe.rank(load())
    assert any(n["account"] == "lonely_demo" for n in res["no_baseline"])
    assert not any(r["account"] == "lonely_demo" for r in res["ranked"])


def test_two_posts_not_enough_without_median():
    rows = [{"account": "a", "views": 10, "hook": "", "median": None}, {"account": "a", "views": 99, "hook": "", "median": None}]
    assert swipe.rank(rows)["no_baseline"][0]["account"] == "a"


def test_given_median_overrides():
    res = swipe.rank(load("swipe.tsv") + [{"account": "m", "views": 100, "hook": "", "median": 10.0}])
    assert [r for r in res["ranked"] if r["account"] == "m"][0]["multiple"] == 10.0


def test_formula_classification():
    res = swipe.rank(load())
    top = res["ranked"][0]
    assert top["formula"] == "Contrarian Take"
    assert res["formula_summary"]


def test_csv_with_quoted_commas_same_ranking():
    a = [(r["account"], r["views"]) for r in swipe.rank(load("swipe.tsv"))["ranked"]]
    b = [(r["account"], r["views"]) for r in swipe.rank(load("swipe.csv"))["ranked"]]
    assert a == b


def test_missing_columns_error_names_headers():
    with pytest.raises(ValueError) as e:
        swipe.parse("foo\tbar\n1\t2\n")
    assert "views" in str(e.value) and "Found headers" in str(e.value)


def test_empty_and_bad_rows():
    with pytest.raises(ValueError):
        swipe.parse("")
    rows, notes = swipe.parse("account\tviews\n@a\tNaN\n@b\t10\n")
    assert len(rows) == 1 and notes


def test_flexible_header_names_and_crlf():
    rows, _ = swipe.parse("Handle,Impressions,Text\r\n@x,1.5K,hello there\r\n")
    assert rows[0]["views"] == 1500 and rows[0]["account"] == "x"


def test_cli(tmp_path):
    out = tmp_path / "s.md"
    r = subprocess.run([sys.executable, SCRIPT, fixture("swipe.tsv"), "--out", str(out)], capture_output=True)
    assert r.returncode == 0 and "OUTLIER" in out.read_text(encoding="utf-8")
    j = subprocess.run([sys.executable, SCRIPT, fixture("swipe.tsv"), "--json"], capture_output=True, text=True, encoding="utf-8")
    assert json.loads(j.stdout)["ranked"]
    assert subprocess.run([sys.executable, SCRIPT, str(tmp_path / "nope")], capture_output=True).returncode == 2
