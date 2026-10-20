# Copyright (c) 2026 Muhammad Hassan. MIT License.
import datetime
import importlib.util
import json
import os
import subprocess
import sys

import pytest

from conftest import ROOT, fixture

PATH = os.path.join(ROOT, "measurement", "dogfood", "report.py")
spec = importlib.util.spec_from_file_location("dogfood_report", PATH)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

CSV = open(fixture("analytics.csv"), encoding="utf-8").read()
D = datetime.date
MANUAL = {"followers_start": 100, "followers_end": 130, "leads": 4, "calls": 1, "clients": 0}


def test_window_counts_and_before_period():
    r = report.build(CSV, D(2026, 9, 11), D(2026, 9, 22), MANUAL)
    assert r["posts"] >= 8 and r["window_days"] == 12
    assert r["before_window_posts"] >= 3 and r["before_window_median_impressions"] is not None
    assert r["follower_change"] == 30


def test_output_has_no_post_text():
    r = report.build(CSV, D(2026, 9, 1), D(2026, 9, 22), MANUAL)
    blob = json.dumps(r) + report.markdown(r)
    assert "cold DMs" not in blob and "landing page" not in blob


def test_markdown_states_the_caveat_and_handles_missing_numbers():
    r = report.build(CSV, D(2026, 9, 1), D(2026, 9, 22), {k: None for k in MANUAL})
    md = report.markdown(r)
    assert "not findings" in md and "n/a" in md


def test_too_few_posts_and_bad_window():
    with pytest.raises(ValueError):
        report.build(CSV, D(2026, 9, 1), D(2026, 9, 2), MANUAL)
    with pytest.raises(ValueError):
        report.build(CSV, D(2026, 9, 5), D(2026, 9, 1), MANUAL)


def test_log_counts_edited_drafts():
    log = "2026-09-01 | x-post | hello | edited: yes\n2026-09-02 | x-post | hi | edited: no\n"
    r = report.build(CSV, D(2026, 9, 1), D(2026, 9, 22), MANUAL, log)
    assert r["log_lines"] == 2 and r["log_marked_edited"] == 1


def test_cli(tmp_path):
    args = [sys.executable, PATH, fixture("analytics.csv"), "--start", "2026-09-01", "--end", "2026-09-22"]
    r = subprocess.run(args + ["--leads", "2"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and "30-day dogfood" in r.stdout
    bad_date = [sys.executable, PATH, fixture("analytics.csv"), "--start", "bad", "--end", "2026-09-22"]
    assert subprocess.run(bad_date, capture_output=True).returncode == 2
    bad = subprocess.run([sys.executable, PATH, str(tmp_path / "no.csv"), "--start", "2026-09-01", "--end", "2026-09-22"],
                         capture_output=True)
    assert bad.returncode == 2
