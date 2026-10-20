# Copyright (c) 2026 Muhammad Hassan. MIT License.
import json
import subprocess
import sys

import ocr
from conftest import ROOT, fixture

SCRIPT = ROOT + "/skills/x-money/ocr.py"


def run(*a):
    return subprocess.run([sys.executable, SCRIPT] + list(a), capture_output=True, text=True, encoding="utf-8")


def test_eligible_when_all_met():
    r = ocr.status(True, 500, 500_000, True, True)
    assert r["verdict"].startswith("ELIGIBLE")


def test_not_eligible_names_the_gap():
    r = ocr.status(True, 310, 120_000, True, True)
    assert r["verdict"] == "NOT ELIGIBLE"
    details = " ".join(i["detail"] for i in r["requirements"])
    assert "190 to go" in details and "380,000 to go" in details


def test_free_account_is_not_eligible():
    assert ocr.status(False, 900, 900_000, True, True)["verdict"] == "NOT ELIGIBLE"


def test_missing_inputs_is_unknown_not_eligible():
    assert ocr.status(None, 600, None, None, None)["verdict"].startswith("UNKNOWN")


def test_boundaries():
    assert ocr.status(True, 499, 500_000, True, True)["verdict"] == "NOT ELIGIBLE"
    assert ocr.status(True, 500, 499_999, True, True)["verdict"] == "NOT ELIGIBLE"


def test_estimate_refused_without_rate():
    r = run("status", "--premium", "yes", "--estimate")
    assert r.returncode == 2 and "publishes no per-impression rate" in r.stderr


def test_estimate_with_user_rate_is_labelled_assumption():
    r = run("status", "--premium", "yes", "--verified-followers", "600", "--impressions-90d", "600000",
            "--age18", "yes", "--country-listed", "yes", "--estimate", "--rate-per-1000", "0.5",
            "--period-impressions", "100000", "--json")
    e = json.loads(r.stdout)["estimate"]
    assert e["estimated_period_payout"] == 50.0 and "YOUR rate" in e["assumption"] and e["meets_30_minimum"]
    assert r.returncode == 0


def test_estimate_below_minimum():
    assert ocr.estimate(0.1, 10_000)["meets_30_minimum"] is False


def test_bad_values_exit_2():
    assert run("status", "--premium", "maybe").returncode == 2
    assert run("status", "--verified-followers", "-5").returncode == 2


def test_lint_flags_each_class():
    posts = ocr.split_posts(open(fixture("ocr_posts.txt"), encoding="utf-8").read())
    found = {f["post"]: f["issues"] for f in ocr.lint(posts)}
    assert 1 not in found
    assert "engagement solicitation" in found[2]
    assert "monetisation coaching" in found[3]
    assert "copied or aggregated marker" in found[4]
    assert "automation marker" in found[5]


def test_lint_cli_exit_codes(tmp_path):
    assert run("lint", fixture("ocr_posts.txt")).returncode == 1
    p = tmp_path / "ok.txt"
    p.write_text("I shipped it in 3 days.\r\nAnd wrote down what broke.\r\n", encoding="utf-8")
    assert run("lint", str(p)).returncode == 0
    p.write_text("", encoding="utf-8")
    assert run("lint", str(p)).returncode == 2
