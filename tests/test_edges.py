# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""Edge cases the first test pass missed: hook scoring, zero baselines, bad dates, CLI misuse, dev scripts."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

import humanize
import detect
import ocr
import postscore
import swipe
import xanalytics
from conftest import ROOT, fixture

LEX = humanize.load_lexicon()
PY = sys.executable


def run(script, *args, stdin=None):
    return subprocess.run([PY, os.path.join(ROOT, script)] + list(args), capture_output=True, text=True,
                          encoding="utf-8", input=stdin)


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- postscore.score_hook_line (used by --hooks and by the measurement script)
def test_hook_with_bait_is_capped_at_twenty():
    assert postscore.score_hook_line("Like and repost if you shipped 3 apps in 30 days")["score"] <= 20.0


def test_hook_names_its_formula_and_carries_notes():
    r = postscore.score_hook_line("I used to reply with advice. Now I reply with a question.")
    assert r["formula"] == "Reversal"
    thin = postscore.score_hook_line("Thoughts?")
    assert thin["score"] < r["score"] and thin["notes"]


def test_hooks_mode_rejects_an_empty_file(tmp_path):
    p = tmp_path / "h.txt"
    p.write_text("\n\n", encoding="utf-8")
    assert run("skills/x-post/postscore.py", "--hooks", str(p)).returncode == 2


def test_hooks_json_is_ranked_best_first(tmp_path):
    p = tmp_path / "h.txt"
    p.write_text("A thread on growth\nI sent 400 cold DMs in 30 days.\n", encoding="utf-8")
    out = json.loads(run("skills/x-post/postscore.py", "--hooks", str(p), "--json").stdout)
    assert out[0]["hook"].startswith("I sent 400") and out[0]["score"] > out[1]["score"]


# ---- swipe.py
def test_swipe_zero_baseline_is_reported_not_divided():
    rows = [{"account": "a", "views": 0.0, "hook": "", "median": None} for _ in range(3)]
    res = swipe.rank(rows)
    assert res["ranked"] == [] and res["no_baseline"][0]["reason"] == "baseline is zero"


def test_swipe_accepts_a_semicolon_delimited_file():
    rows, _ = swipe.parse("account;views;hook\n@a;100;x\n@a;120;y\n@a;900;z\n")
    assert [r["views"] for r in rows] == [100, 120, 900]


def test_swipe_account_names_are_case_and_at_insensitive():
    rows, _ = swipe.parse("account,views\n@Alpha,10\nalpha,12\n@ALPHA,300\n")
    assert {r["account"] for r in rows} == {"alpha"}
    assert swipe.rank(rows)["ranked"][0]["multiple"] > 10


# ---- xanalytics.py
def test_unparseable_dates_drop_the_time_groups_without_crashing():
    t = "text,impressions,date\n" + "\n".join(f"post {i},{100 * i},not a date" for i in range(1, 6))
    posts, _, _ = xanalytics.parse(t)
    res = xanalytics.analyse(posts)
    groups = {f["feature"]: f["groups"] for f in res["features"]}
    assert groups["weekday"] == [] and groups["hour"] == []


def test_analytics_without_text_still_ranks_by_impressions():
    posts, _, _ = xanalytics.parse("impressions\n100\n200\n3000\n150\n")
    res = xanalytics.analyse(posts)
    assert res["top"][0]["impressions"] == 3000 and res["top"][0]["engagement_rate"] is None


# ---- ocr.py
def test_ocr_negative_rate_is_refused():
    r = run("skills/x-money/ocr.py", "status", "--estimate", "--rate-per-1000", "-1", "--period-impressions", "1000")
    assert r.returncode == 2


def test_ocr_estimate_needs_the_period_impressions():
    assert run("skills/x-money/ocr.py", "status", "--estimate", "--rate-per-1000", "0.5").returncode == 2


def test_ocr_lint_reads_stdin_and_treats_each_line_as_a_post_without_separators():
    r = run("skills/x-money/ocr.py", "lint", "-", "--json", stdin="Shipped it in 3 days.\nFollow for more!\n")
    out = json.loads(r.stdout)
    assert r.returncode == 1 and out["posts"] == 2 and out["issues"][0]["post"] == 2


def test_ocr_unknown_inputs_are_unknown_not_eligible():
    assert ocr.status(None, None, None, None, None)["verdict"].startswith("UNKNOWN")


# ---- humanize / detect on very short text
def test_humanize_leaves_a_clean_single_word_alone():
    out, rep = humanize.humanize("hello", LEX)
    assert out == "hello\n" and not any(rep.values())


def test_detect_does_not_invent_a_score_for_an_emoji():
    r = detect.run("\U0001F525", LEX)
    assert r["checks"]["BURSTINESS"][0] is None and r["scored"] <= 2


# ---- dev scripts (skipped where their third-party packages are not installed)
def test_demo_tape_commands_are_parsed_with_their_clear_markers():
    pytest.importorskip("PIL")
    mod = load("demo/render_fallback.py", "render_fallback")
    tape = 'Hide\nType "clear" Enter\nShow\nType "__PY__ a.py x" Sleep 400ms Enter\nType "__PY__ b.py | tail -3" Sleep 1s Enter\n'
    assert mod.commands(tape, "python") == [("python a.py x", True), ("python b.py | tail -3", False)]
    real = mod.commands(open(os.path.join(ROOT, "demo", "x-agent-skill.tape"), encoding="utf-8").read(), "python")
    assert len(real) == 4 and real[0][1] is True


def test_render_icons_draws_a_rounded_mark():
    pytest.importorskip("PIL")
    mod = load("measurement/render_icons.py", "render_icons")
    m = mod.mark(64)
    assert m.size == (64, 64) and m.getpixel((0, 0))[3] == 0           # transparent rounded corner
    assert m.getpixel((32, 12))[:3] == mod.INK[:3]                      # dark ground inside the tile


def test_validation_script_auc_matches_a_hand_computed_value():
    np = pytest.importorskip("numpy")
    pytest.importorskip("pyarrow")
    mod = load("measurement/validate.py", "validate")
    # pairs of (pos, neg): 3 beats 1 and 2 and ties 3; 4 and 5 beat all three -> 8.5 / 9
    assert abs(mod.auc(np.array([3.0, 4.0, 5.0]), np.array([1.0, 2.0, 3.0])) - 8.5 / 9) < 1e-9
    assert mod.auc(np.array([]), np.array([1.0])) is None
