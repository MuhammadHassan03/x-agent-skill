# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""The checks that must pass before algo_watch commits anything to the default branch."""
import json
import os
import subprocess
import sys

import pytest

import algo_watch
from conftest import ROOT, fixture

SCRIPT = ROOT + "/tools/algo_watch.py"
TEXT = open(fixture("param_full.rs"), encoding="utf-8").read()
COMMIT = "74d49a4ffb398949a5f9312f828d7112d7d31f00"
FAV = '"rust_home_mixer_favorite_weight", '


def make_root(tmp_path):
    (tmp_path / "references").mkdir()
    (tmp_path / "README.md").write_text("# T\n\n" + algo_watch.START + "\n" + algo_watch.END + "\n", encoding="utf-8")
    return str(tmp_path)


def seeded(tmp_path):
    root = make_root(tmp_path)
    algo_watch.run(TEXT, COMMIT, "2026-10-20T00:00:00Z", root, "2026-10-21", True)
    return root


def snapshot(root):
    return open(root + "/references/weights.json", encoding="utf-8").read()


def attempt(root, text, diff=None):
    return algo_watch.run(text, "b" * 40, "2026-10-27T00:00:00Z", root, "2026-10-28", True, diff)


def test_a_clean_update_passes_and_commits(tmp_path):
    root = seeded(tmp_path)
    r = attempt(root, TEXT.replace(FAV + "0.66", FAV + "0.7"))
    assert r["n"] == 1 and json.loads(snapshot(root))["commit"] == "b" * 40


def test_check_1_a_missing_weight_key_fails_and_writes_nothing(tmp_path):
    root = seeded(tmp_path)
    before = snapshot(root)
    md_before = open(root + "/references/x-algorithm.md", encoding="utf-8").read()
    log_before = open(root + "/references/ALGO-CHANGELOG.md", encoding="utf-8").read()
    start = TEXT.index("param!(\n    BlockAuthorWeight")
    end = TEXT.index(");", start) + 2
    broken = TEXT[:start] + TEXT[end:]
    diff = str(tmp_path / "raw.md")
    with pytest.raises(algo_watch.ValidationFailed) as e:
        attempt(root, broken, diff)
    assert any("BlockAuthorWeight" in p and "missing" in p for p in e.value.problems)
    assert snapshot(root) == before
    assert open(root + "/references/x-algorithm.md", encoding="utf-8").read() == md_before
    assert open(root + "/references/ALGO-CHANGELOG.md", encoding="utf-8").read() == log_before
    assert "Validation failed" in open(diff, encoding="utf-8").read() and "BlockAuthorWeight" in open(diff, encoding="utf-8").read()


def test_check_2_a_non_numeric_weight_fails(tmp_path):
    root = seeded(tmp_path)
    before = snapshot(root)
    for bad in ('"high"', "true"):
        with pytest.raises(algo_watch.ValidationFailed) as e:
            attempt(root, TEXT.replace(FAV + "0.66", FAV + bad))
        assert any("FavoriteWeight is not numeric" in p for p in e.value.problems)
    assert snapshot(root) == before


def test_check_3_a_move_of_more_than_10x_fails(tmp_path):
    root = seeded(tmp_path)
    before = snapshot(root)
    for v in ("7.0", "0.05"):      # 0.66 -> 7.0 is 10.6x up, 0.66 -> 0.05 is 13x down
        with pytest.raises(algo_watch.ValidationFailed) as e:
            attempt(root, TEXT.replace(FAV + "0.66", FAV + v))
        assert any("FavoriteWeight moved from 0.66" in p and "10x" in p for p in e.value.problems)
    assert snapshot(root) == before


def test_check_3_boundaries_and_special_cases():
    assert not algo_watch.moved_too_far(1.0, 10.0)        # exactly 10x is allowed
    assert algo_watch.moved_too_far(1.0, 10.01)
    assert not algo_watch.moved_too_far(1.0, 0.1)
    assert algo_watch.moved_too_far(1.0, 0.099)
    assert algo_watch.moved_too_far(0, 0.5) and algo_watch.moved_too_far(0.5, 0)    # to or from zero
    assert algo_watch.moved_too_far(-234.0, 234.0)                                  # sign flip
    assert not algo_watch.moved_too_far(-234.0, -300.0)
    assert not algo_watch.moved_too_far(3, 3)


def test_non_weight_params_may_change_freely(tmp_path):
    root = seeded(tmp_path)
    r = attempt(root, TEXT.replace('"rust_home_mixer_phoenix_max_results",\n    1000', '"rust_home_mixer_phoenix_max_results",\n    90000'))
    assert r["n"] == 1 and r["weight_changes"] == 0


def test_baseline_still_checks_numeric_weights(tmp_path):
    root = make_root(tmp_path)
    with pytest.raises(algo_watch.ValidationFailed):
        algo_watch.run(TEXT.replace(FAV + "0.66", FAV + "true"), COMMIT, "2026-10-20", root, "2026-10-21", True)
    assert not os.path.exists(root + "/references/weights.json")


def test_cli_exit_code_3_and_diff_file(tmp_path):
    root = seeded(tmp_path)
    before = snapshot(root)
    bad = tmp_path / "bad.rs"
    bad.write_text(TEXT.replace(FAV + "0.66", FAV + "9.0"), encoding="utf-8")
    diff = tmp_path / "raw.md"
    r = subprocess.run([sys.executable, SCRIPT, "--param-file", str(bad), "--commit", "c" * 40, "--date", "2026-10-27",
                        "--root", root, "--today", "2026-10-28", "--write", "--diff-out", str(diff)],
                       capture_output=True, text=True)
    assert r.returncode == 3 and r.stderr.startswith("VALIDATION FAILED")
    assert "FavoriteWeight" in r.stderr and snapshot(root) == before
    assert "Raw diff" in diff.read_text(encoding="utf-8")


def test_workflow_validates_then_commits_with_upstream_details():
    wf = open(ROOT + "/.github/workflows/algo-watch.yml", encoding="utf-8").read()
    assert "== '3'" in wf and "gh issue create" in wf and "--body-file" in wf
    assert "upstream" in wf and "commit_date" in wf
    assert "pull-requests" not in wf and "gh pr create" not in wf
